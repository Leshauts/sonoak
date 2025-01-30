import asyncio
import json
import websockets
from typing import List, Dict
import traceback

class SnapcastManager:
    def __init__(self, websocket_manager):
        print("Initialisation du SnapcastManager...")
        self.websocket_manager = websocket_manager
        self.clients: List[dict] = []
        self.snapserver_host = "192.168.1.173"
        self.snapserver_port = 1780
        self.server_available = False
        self.ws = None

    async def ensure_connection(self):
        """S'assure que la connexion WebSocket est établie"""
        try:
            if self.ws is None:
                self.ws = await websockets.connect(
                    f'ws://{self.snapserver_host}:{self.snapserver_port}/jsonrpc',
                    ping_interval=None,
                    ping_timeout=None
                )
                print("Nouvelle connexion WebSocket établie avec snapserver")
                self.server_available = True
                return True
            return True
        except Exception as e:
            print(f"Erreur de connexion WebSocket: {e}")
            self.server_available = False
            self.ws = None
            return False

    async def send_command(self, command: dict) -> dict:
        """Envoie une commande via WebSocket et retourne la réponse"""
        try:
            if not await self.ensure_connection():
                return None

            print(f"Envoi de la commande: {command}")
            await self.ws.send(json.dumps(command))
            response = await self.ws.recv()
            print(f"Réponse reçue: {response}")
            return json.loads(response)
        except Exception as e:
            print(f"Erreur lors de l'envoi de la commande: {e}")
            self.ws = None
            self.server_available = False
            return None

    async def get_clients_status(self):
        """Récupère le statut des clients Snapcast"""
        command = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Server.GetStatus"
        }
        
        response = await self.send_command(command)
        if response and "result" in response:
            try:
                self.clients = []
                server_status = response["result"]["server"]
                if "groups" in server_status:
                    for group in server_status["groups"]:
                        for client in group["clients"]:
                            client_info = {
                                "id": client["id"],
                                "host": client["host"]["name"],
                                "connected": client["connected"]
                            }
                            print(f"Client trouvé: {client_info}")
                            self.clients.append(client_info)
                
                await self.notify_clients_status()
                return True
            except Exception as e:
                print(f"Erreur lors du traitement de la réponse: {e}")
                traceback.print_exc()
        
        await self.notify_clients_status()
        return False

    async def notify_clients_status(self):
        """Envoie la liste des clients au frontend"""
        message = {
            "type": "clients_status",
            "clients": self.clients,
            "server_available": self.server_available
        }
        print(f"Envoi du statut Snapcast: {message}")
        await self.websocket_manager.broadcast_to_service(message, "snapcast")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"Message Snapcast reçu: {message}")
        message_type = message.get("type")
        
        if message_type == "get_status":
            await self.get_clients_status()