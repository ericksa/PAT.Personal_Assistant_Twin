#!/usr/bin/env python3
"""
WebSocket Manager

Manages WebSocket connections and broadcasts messages to all connected clients.
"""

import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Add a new WebSocket connection to the manager.

        Args:
            websocket: The WebSocket connection to add.
            client_id: A unique identifier for the client.
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(
            f"Client {client_id} connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, client_id: str) -> None:
        """
        Remove a WebSocket connection from the manager.

        Args:
            client_id: The unique identifier for the client to remove.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(
                f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}"
            )

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast as a dictionary.
        """
        if not self.active_connections:
            logger.warning("No active WebSocket connections to broadcast to.")
            return

        message_str = json.dumps(message)
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                self.disconnect(client_id)

    async def send_personal_message(self, message: dict, client_id: str) -> None:
        """
        Send a message to a specific client.

        Args:
            message: The message to send as a dictionary.
            client_id: The unique identifier for the client.
        """
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not found in active connections.")
            return

        message_str = json.dumps(message)
        try:
            await self.active_connections[client_id].send_text(message_str)
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            self.disconnect(client_id)
