# websocket/manager.py
import logging
import asyncio
from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = 30  # seconds
        self.connection_timeouts: Dict[WebSocket, datetime] = {}
        self.reconnect_attempts: Dict[str, int] = {}
        self.max_reconnect_attempts = 5

    async def connect(self, websocket: WebSocket, service: str) -> bool:
        """
        Handle new WebSocket connection with improved error handling
        """
        try:
            await websocket.accept()
            if service not in self.active_connections:
                self.active_connections[service] = set()
            self.active_connections[service].add(websocket)
            self.connection_timeouts[websocket] = datetime.now()
            
            # Start heartbeat for this connection
            asyncio.create_task(self._heartbeat(websocket, service))
            
            return True
        except Exception as e:
            logger.error(f"Error connecting WebSocket for {service}: {e}")
            await self._handle_connection_error(websocket, service)
            return False

    def disconnect(self, websocket: WebSocket, service: str):
        """
        Handle WebSocket disconnection with cleanup
        """
        try:
            if service in self.active_connections:
                self.active_connections[service].discard(websocket)
                self.connection_timeouts.pop(websocket, None)
            
            # Reset reconnection attempts on clean disconnect
            self.reconnect_attempts[service] = 0
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect for {service}: {e}")

    async def broadcast_to_service(self, message: dict, service: str):
        """
        Broadcast message to all clients of a service with error handling
        """
        if service not in self.active_connections:
            return

        dead_connections = set()
        for connection in self.active_connections[service].copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {service}: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for dead_conn in dead_connections:
            self.disconnect(dead_conn, service)

    async def _heartbeat(self, websocket: WebSocket, service: str):
        """
        Maintain connection health with periodic heartbeats
        """
        while True:
            try:
                if websocket not in self.connection_timeouts:
                    break
                
                await websocket.send_json({"type": "ping"})
                self.connection_timeouts[websocket] = datetime.now()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat failed for {service}: {e}")
                await self._handle_connection_error(websocket, service)
                break

    async def _handle_connection_error(self, websocket: WebSocket, service: str):
        """
        Handle connection errors with reconnection logic
        """
        self.disconnect(websocket, service)
        
        # Increment reconnection attempts
        self.reconnect_attempts[service] = self.reconnect_attempts.get(service, 0) + 1
        
        if self.reconnect_attempts[service] <= self.max_reconnect_attempts:
            backoff = min(2 ** (self.reconnect_attempts[service] - 1), 60)  # Exponential backoff
            logger.info(f"Attempting to reconnect to {service} in {backoff} seconds...")
            await asyncio.sleep(backoff)
            
            # Attempt reconnection
            try:
                await self.connect(websocket, service)
            except Exception as e:
                logger.error(f"Reconnection attempt failed for {service}: {e}")
        else:
            logger.error(f"Max reconnection attempts reached for {service}")