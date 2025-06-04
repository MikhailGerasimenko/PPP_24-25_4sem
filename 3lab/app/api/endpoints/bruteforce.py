from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Path, BackgroundTasks
from celery.result import AsyncResult
import uuid
import json
import asyncio
from typing import Union, Optional
from app.core.config import settings # Added import for settings

# Try to use redis.asyncio, hoping redislite patches it or is compatible
try:
    from redis.asyncio import Redis as AsyncRedis
    from redis.asyncio.client import PubSub as AsyncPubSub # Ensure this is the right PubSub
    # from redis.asyncio.connection import ConnectionPool as AsyncConnectionPool
    print("Successfully imported redis.asyncio.Redis and PubSub")
except ImportError:
    AsyncRedis = None # type: ignore
    AsyncPubSub = None # type: ignore
    # AsyncConnectionPool = None
    print("Failed to import redis.asyncio.Redis. Ensure redis-py >= 4.2 is installed.")
    # As a fallback, this part of app might not work as expected with sync redis client in async code

from app.schemas import (
    BruteforceRequest,
    TaskCreationResponse,
    TaskStartedMessage,
    TaskProgressMessage,
    TaskCompletedMessage,
    TaskFailedMessage,
    TaskActionResponse
)
# We will use the redis_client from tasks for Celery task submission logic if needed for status,
# but for FastAPI's own PubSub listening, we need an async client.
from app.celery.tasks import bruteforce_task, NOTIFICATION_CHANNEL # Removed redis_client import from tasks
from app.celery.celery_app import celery_app
from app.websocket import manager

router = APIRouter()

# Global vars for the async Redis client and its pubsub listener
redis_async_client: Union[AsyncRedis, None] = None
active_redis_listener_task: Union[asyncio.Task, None] = None

async def redis_message_listener_async(pubsub: AsyncPubSub): # Renamed and expecting AsyncPubSub
    """Listens to Redis Pub/Sub messages and forwards them to WebSocket clients."""
    print("redis_message_listener_async started")
    try:
        async for message in pubsub.listen():
            if message and message["type"] == "message":
                print(f"Async listener received: {message['data']}")
                try:
                    data = json.loads(message["data"])
                    client_id = data.get("client_id")
                    payload = data.get("payload")
                    if client_id and payload:
                        await manager.send_personal_message(payload, client_id)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from Redis: {message['data']}")
                except Exception as e:
                    print(f"Error processing message from Redis: {e}")
    except asyncio.CancelledError:
        print("redis_message_listener_async was cancelled.")
        # Important: Resubscribe might be needed if connection drops and pubsub object becomes invalid
    except Exception as e:
        print(f"Exception in redis_message_listener_async: {e}")
    finally:
        print("redis_message_listener_async finished.")


async def startup_event():
    global redis_async_client, active_redis_listener_task
    
    if AsyncRedis is None:
        print("AsyncRedis not available. Cannot start Redis PubSub listener for FastAPI.")
        return

    try:
        # Use the same URL Celery is configured with (hoping redislite patches it)
        # This assumes redislite will correctly handle a standard Redis URL for async client too
        redis_async_client = AsyncRedis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        await redis_async_client.ping()
        print(f"Successfully connected async Redis client to {settings.CELERY_BROKER_URL} (hopefully redislite)")
        
        # Ensure pubsub is not None before using it, though from_url should give valid client or raise error
        if redis_async_client:
            pubsub: Optional[AsyncPubSub] = redis_async_client.pubsub()
            if pubsub:
                await pubsub.subscribe(NOTIFICATION_CHANNEL)
                print(f"Subscribed to Redis channel '{NOTIFICATION_CHANNEL}' with async pubsub.")
                active_redis_listener_task = asyncio.create_task(redis_message_listener_async(pubsub))
                print("Started async Redis message listener task.")
            else:
                print("Failed to get pubsub object from async_redis_client.")
        else:
            print("redis_async_client is None after connection attempt.")

    except Exception as e:
        print(f"Error during async Redis startup or pubsub subscription: {e}")
        if redis_async_client:
            await redis_async_client.close() # Ensure connection is closed on error
        redis_async_client = None


async def shutdown_event():
    global active_redis_listener_task, redis_async_client
    if active_redis_listener_task:
        print("Cancelling async Redis listener task...")
        active_redis_listener_task.cancel()
        try:
            await active_redis_listener_task
        except asyncio.CancelledError:
            print("Async Redis listener task cancelled successfully.")
        active_redis_listener_task = None
        
    if redis_async_client:
        print("Closing async Redis client connection...")
        await redis_async_client.close()
        redis_async_client = None
        print("Async Redis client connection closed.")
    print("Performed shutdown actions for async Redis listener.")


@router.post("/start_bruteforce/{client_id}", response_model=TaskCreationResponse)
async def start_bruteforce_task(
    client_id: str, 
    request: BruteforceRequest, 
    background_tasks: BackgroundTasks
):
    """
    Starts a new bruteforce task for a given client_id.
    The client_id is used to route WebSocket notifications back to the correct client.
    """
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required")

    # Ensure the client is connected via WebSocket if we want to enforce it here
    # For now, we assume the client will connect/is connected with this client_id
    if client_id not in manager.active_connections:
        # This check is optional. We could allow task submission even if WS is not yet connected,
        # notifications would just be missed until connection.
        # However, for a better UX, it's good if the client connects the WS first.
        print(f"Warning: Client {client_id} submitted a task but is not connected via WebSocket.")
        # raise HTTPException(status_code=400, detail=f"Client {client_id} not connected via WebSocket. Please connect first.")

    task_id_ws = str(uuid.uuid4()) # Unique ID for WebSocket message tracking and client-side handling
    
    # Send Celery task
    # We pass both client_id (for WS routing) and task_id_ws (for the payload of WS messages)
    celery_task_ref = bruteforce_task.delay(
        client_id=client_id,
        task_id_ws=task_id_ws,
        hash_to_crack=request.hash_to_crack,
        max_length=request.max_length,
        charset=request.charset,
        hash_type="rar" # As per variant 5 requirements
    )
    
    return TaskCreationResponse(
        task_id=celery_task_ref.id, # This is Celery's task ID
        message=f"Bruteforce task started. WebSocket Task ID for notifications: {task_id_ws}"
    )

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str = Path(...)):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # We can receive messages from the client if needed, e.g., to confirm connection
            # or to manage task subscriptions if one WS handles multiple tasks for a user.
            data = await websocket.receive_text()
            # For this lab, server primarily sends data. Client can send pings or commands.
            print(f"Received from {client_id}: {data}")
            await manager.send_personal_message(f"Echo: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client {client_id} disconnected from WebSocket.")
    except Exception as e:
        manager.disconnect(client_id)
        print(f"Error with WebSocket client {client_id}: {e}")

@router.get("/task_status/{celery_task_id}")
async def get_task_status(celery_task_id: str):
    """Gets the status of a Celery task."""
    task_result = AsyncResult(celery_task_id, app=celery_app)
    response = {
        "task_id": celery_task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    if task_result.failed():
        response["error"] = str(task_result.info) # Exception info
    return response

@router.post("/cancel_task/{celery_task_id}", response_model=TaskActionResponse)
async def cancel_bruteforce_task(celery_task_id: str):
    """Cancels a running Celery task."""
    # Check if task exists or is already completed/revoked
    task_result = AsyncResult(celery_task_id, app=celery_app)
    if task_result.ready(): # True if task has run (SUCCESS, FAILURE, REVOKED)
        return TaskActionResponse(task_id=celery_task_id, message=f"Task is already completed or not running. Status: {task_result.status}")

    try:
        # For Celery, revoke sends a signal. The task must check for self.is_revoked().
        celery_app.control.revoke(celery_task_id, terminate=True, signal='SIGTERM')
        # Note: `terminate=True` might not work with all brokers or OS. 
        # The task itself should handle revocation gracefully.
        return TaskActionResponse(task_id=celery_task_id, message="Task cancellation request sent.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send cancellation request: {str(e)}") 