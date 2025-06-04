from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Stores active connections, mapping a user_id/task_id to a WebSocket connection
        # For this lab, we'll use task_id as the primary key for notifications.
        # A single user might have multiple tasks, so multiple WebSockets or a way to multiplex.
        # The requirement says "For each user should be created a separate WebSocket channel"
        # and then "client should be able to handle parallel notifications from different tasks, distinguishing by task_id"
        # This suggests a single WebSocket per user, but messages are per task_id.
        # Or, it could mean a new WebSocket connection for each task submission, identified by a task_id.
        # Let's start with: one connection can subscribe to multiple task_ids.
        # Or simpler: one WebSocket connection is established, and when a task is launched, its ID is associated.
        # For simplicity, let's make it one WebSocket per client, and the client manages task_ids from messages.
        # So, we map a client identifier (e.g., derived from token, or a simple unique ID per connection) to the WebSocket.
        # However, the problem asks for notifications about *tasks*. So we need to send a message *to the client who owns that task*.
        # A user might have multiple tasks.
        # Let's use a dictionary where keys are a client_id (e.g. user_id or a connection_id) and value is the WebSocket.
        # When a task status updates, we need to know which client (WebSocket) to send it to.
        # This means the task itself should probably store who initiated it.

        # Simpler approach for now: a global manager for all connections.
        # We can have a dictionary mapping task_id to a list of WebSockets interested in that task_id.
        # Or, if a user has one WebSocket, we map user_id to WebSocket.
        # Let's follow the "For each USER should be created a separate channel" idea.
        # So we need a way to identify a user for a WebSocket connection.
        # This usually involves authentication and passing a user_id.
        # For now, let's assume a `client_id` (which could be a user ID string) is passed during connection.

        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent message to {client_id}: {message}")
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                # Optionally, handle disconnection here if send fails
        else:
            logger.warning(f"Client {client_id} not found for sending message.")

    async def broadcast(self, message: dict):
        # This might not be needed if messages are task-specific to users.
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")

manager = ConnectionManager() 