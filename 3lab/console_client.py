import asyncio
import websockets
import json
import httpx # For making HTTP requests to the API
import click
import uuid
from typing import Optional

API_BASE_URL = "http://localhost:8000/api/v1/bruteforce"
WS_BASE_URL = "ws://localhost:8000/ws"

# Store active Celery task IDs and their corresponding WebSocket task IDs
# (celery_task_id -> ws_task_id)
active_tasks_map = {}

async def handle_websocket_messages(websocket, client_id):
    """Receives and prints messages from the WebSocket server."""
    try:
        async for message_str in websocket:
            try:
                message = json.loads(message_str)
                task_id = message.get("task_id", "N/A")
                status = message.get("status", "N/A")
                
                if status == "STARTED":
                    print(f"\n[TASK {task_id} STARTED] Hash Type: {message.get('hash_type')}, Max Length: {message.get('max_length')}, Charset Len: {message.get('charset_length')}")
                elif status == "PROGRESS":
                    print(f"[TASK {task_id} PROGRESS] {message.get('progress')}% | Current: {message.get('current_combination', '')} | CPS: {message.get('combinations_per_second', 0)}", end='\r')
                elif status == "COMPLETED":
                    print(f"\n[TASK {task_id} COMPLETED]")
                    print(f"  Result: {message.get('result', 'Not found')}")
                    print(f"  Time: {message.get('elapsed_time')}")
                    if task_id in active_tasks_map.values():
                        # Remove task from active map once completed
                        for c_id, w_id in list(active_tasks_map.items()):
                            if w_id == task_id:
                                del active_tasks_map[c_id]
                                break
                elif status == "REVOKED":
                     print(f"\n[TASK {task_id} REVOKED] {message.get('message')}")
                elif status == "FAILED":
                    print(f"\n[TASK {task_id} FAILED] Error: {message.get('error')}")   
                else:
                    print(f"\n[TASK {task_id} INFO] {message}")
            except json.JSONDecodeError:
                print(f"\n[RAW MSG] {message_str}")
            except Exception as e:
                print(f"\nError processing message: {e} | Original: {message_str}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"\nWebSocket connection closed: {e}")
    except Exception as e:
        print(f"\nWebSocket error: {e}")
    finally:
        print("\nDisconnected from WebSocket.")

async def start_task_async(client_id: str, hash_to_crack: str, max_length: int, charset: Optional[str]):
    payload = {
        "hash_to_crack": hash_to_crack,
        "max_length": max_length,
    }
    if charset:
        payload["charset"] = charset

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/start_bruteforce/{client_id}", json=payload)
            response.raise_for_status() # Raise an exception for bad status codes
            result = response.json()
            celery_task_id = result.get("task_id")
            ws_task_id = result.get("message", "").split("ID for notifications: ")[-1] # Extract ws_task_id
            if celery_task_id and ws_task_id != celery_task_id : # ensure ws_task_id was extracted
                 active_tasks_map[celery_task_id] = ws_task_id
                 print(f"Task submitted. Celery Task ID: {celery_task_id}, WebSocket Task ID: {ws_task_id}")
            else:
                 print(f"Task submitted. Celery Task ID: {celery_task_id}. Could not parse WebSocket Task ID from message: {result.get('message')}")

        except httpx.HTTPStatusError as e:
            print(f"Error starting task: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error starting task (request failed): {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

async def get_task_status_async(celery_task_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/task_status/{celery_task_id}")
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))
        except httpx.HTTPStatusError as e:
            print(f"Error getting status: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error getting status (request failed): {e}")

async def cancel_task_async(celery_task_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/cancel_task/{celery_task_id}")
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))
            if celery_task_id in active_tasks_map:
                 del active_tasks_map[celery_task_id] # Remove if cancellation successful or task was already finished
        except httpx.HTTPStatusError as e:
            print(f"Error cancelling task: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error cancelling task (request failed): {e}")

@click.group()
@click.option('--client-id', default=lambda: str(uuid.uuid4()), help='Unique ID for this client session.')
@click.pass_context
def cli(ctx, client_id):
    """A console client for the Bruteforce API with WebSocket notifications."""
    ctx.obj = {'client_id': client_id}
    print(f"Client ID for this session: {client_id}")

@cli.command()
@click.option('--hash-val', prompt='Hash to crack', help='The hash value (e.g., a SHA256 hash for testing).')
@click.option('--max-len', prompt='Max password length', type=int, help='Maximum length of the password.')
@click.option('--charset', default=None, help='Optional custom charset.')
@click.pass_context
def start(ctx, hash_val: str, max_len: int, charset: Optional[str]):
    """Starts a new bruteforce task."""
    client_id = ctx.obj['client_id']
    asyncio.run(start_task_async(client_id, hash_val, max_len, charset))

@cli.command()
@click.argument('celery_task_id', type=str)
@click.pass_context
def status(ctx, celery_task_id: str):
    """Gets the status of a Celery task."""
    asyncio.run(get_task_status_async(celery_task_id))

@cli.command()
@click.argument('celery_task_id', type=str)
@click.pass_context
def cancel(ctx, celery_task_id: str):
    """Cancels a running Celery task."""
    asyncio.run(cancel_task_async(celery_task_id))

@cli.command()
@click.pass_context
def connect_ws(ctx):
    """Connects to the WebSocket server to receive notifications."""
    client_id = ctx.obj['client_id']
    ws_url = f"{WS_BASE_URL}/{client_id}"
    print(f"Connecting to WebSocket: {ws_url}")
    
    async def listen():
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"Connected to WebSocket for client {client_id}.")
                # Keep connection alive and listen for messages
                await handle_websocket_messages(websocket, client_id)
        except websockets.exceptions.InvalidURI:
            print(f"Invalid WebSocket URI: {ws_url}")
        except ConnectionRefusedError:
            print(f"WebSocket connection refused at {ws_url}. Is the server running?")
        except Exception as e:
            print(f"Failed to connect or lost WebSocket connection: {e}")
            
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("WebSocket listener stopped by user.")

if __name__ == '__main__':
    cli() 