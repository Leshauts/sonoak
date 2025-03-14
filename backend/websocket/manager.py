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
            # Créer une entrée vide pour ce service
            self.active_connections[service] = set()
        
        # Assurer que les connections "global" existent
        if "global" not in self.active_connections:
            self.active_connections["global"] = set()

        # Vérifier si les connections sont encore valides
        for service_name, connections in self.active_connections.items():
            to_remove = set()
            for conn in connections:
                try:
                    if not conn or conn.client_state.DISCONNECTED:
                        to_remove.add(conn)
                except Exception:
                    to_remove.add(conn)
            
            # Nettoyer les connexions invalides
            for conn in to_remove:
                try:
                    self.disconnect(conn, service_name)
                except Exception as e:
                    logger.error(f"Error cleaning invalid connection: {e}")

        # Continuer avec le broadcast normal
        wrapped_message = {"service": service, **message}
        
        # Envoyer à tous les clients globaux si le service n'est pas global
        if service != "global" and self.active_connections["global"]:
            await self._broadcast_message(wrapped_message, "global")
        
        # Envoyer aux clients spécifiques du service
        if service != "global" and self.active_connections[service]:
            await self._broadcast_message(message, service)
        
        # Si c'est un message global
        if service == "global" and self.active_connections["global"]:
            await self._broadcast_message(message, "global")

    async def _broadcast_message(self, message: dict, target_service: str):
        """
        Méthode interne pour diffuser un message aux clients d'un service
        """
        if target_service not in self.active_connections or not self.active_connections[target_service]:
            logger.debug(f"No active connections for {target_service}, skipping broadcast")
            return

        dead_connections = set()
        for connection in self.active_connections[target_service].copy():
            try:
                if connection.client_state.DISCONNECTED:
                    logger.debug(f"Connection for {target_service} is already disconnected")
                    dead_connections.add(connection)
                    continue
                    
                await connection.send_json(message)
            except RuntimeError as e:
                if "Cannot call 'send' once a close message has been sent" in str(e):
                    logger.warning(f"Connection for {target_service} is closing/closed")
                else:
                    logger.error(f"Error broadcasting to {target_service}: {e}")
                dead_connections.add(connection)
            except Exception as e:
                logger.error(f"Unknown error broadcasting to {target_service}: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for dead_conn in dead_connections:
            try:
                self.disconnect(dead_conn, target_service)
            except Exception as e:
                logger.error(f"Error during dead connection cleanup: {e}")

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
        # S'assurer que la déconnexion est propre
        try:
            self.disconnect(websocket, service)
        except Exception as e:
            logger.error(f"Error during disconnect for {service}: {e}")
        
        # Incrémenter les tentatives de reconnexion
        self.reconnect_attempts[service] = self.reconnect_attempts.get(service, 0) + 1
        
        if self.reconnect_attempts[service] <= self.max_reconnect_attempts:
            backoff = min(2 ** (self.reconnect_attempts[service] - 1), 60)  # Exponential backoff
            logger.info(f"Attempting to reconnect to {service} in {backoff} seconds...")
            await asyncio.sleep(backoff)
            
            # Ne pas tenter de réutiliser le même objet WebSocket
            # Le client devrait se reconnecter de lui-même
            logger.info(f"Ready for {service} to reconnect.")
        else:
            logger.error(f"Max reconnection attempts reached for {service}")
            # Réinitialiser pour les futures tentatives
            self.reconnect_attempts[service] = 0