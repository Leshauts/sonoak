# backend/websocket/manager.py
from typing import Dict, Set
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "bluetooth": set(),
            "snapcast": set(),
            "spotify": set(),
            "navigation": set(),
            "audio": set()
        }

    async def connect(self, websocket: WebSocket, service: str):
        """Connecte un nouveau client WebSocket"""
        await websocket.accept()
        if service not in self.active_connections:
            self.active_connections[service] = set()
        self.active_connections[service].add(websocket)

    def disconnect(self, websocket: WebSocket, service: str):
        """Déconnecte un client WebSocket"""
        if service in self.active_connections:
            self.active_connections[service].discard(websocket)

    async def broadcast_to_service(self, message: dict, service: str):
        """Envoie un message à tous les clients d'un service spécifique"""
        if service in self.active_connections:
            disconnected_ws = set()
            for connection in self.active_connections[service]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message to websocket: {e}")
                    disconnected_ws.add(connection)
            
            # Nettoyer les connexions mortes
            for ws in disconnected_ws:
                self.active_connections[service].discard(ws)