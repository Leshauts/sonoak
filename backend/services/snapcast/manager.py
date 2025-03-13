import asyncio
import json
import websockets
from typing import List, Dict
import traceback
from services.audio.manager import AudioSource

class SnapcastManager:
    def __init__(self, websocket_manager, audio_manager=None):
        print("Initialisation du SnapcastManager...")
        self.websocket_manager = websocket_manager
        self.audio_manager = audio_manager
        self.clients = []
        self.server_info = None
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

    async def get_server_info(self):
        """Récupère les informations détaillées du serveur"""
        try:
            status_command = {
                "id": 2,
                "jsonrpc": "2.0",
                "method": "Server.GetStatus"
            }
            status_response = await self.send_command(status_command)
            
            if status_response and "result" in status_response:
                server_status = status_response["result"]["server"]
                host_info = server_status.get("server", {}).get("host", {})
                
                # Récupérer le nom et appliquer les transformations
                server_name = host_info.get("name", "Unknown")
                server_name = server_name.replace(".local", "")  # Retirer .local
                server_name = server_name.replace("-", " ")      # Remplacer les tirets par des espaces
                
                self.server_info = {
                    "name": server_name,
                    "os": host_info.get("os", "Unknown"),
                    "arch": host_info.get("arch", "Unknown")
                }
                print(f"Server info updated: {self.server_info}")
                return True
                
        except Exception as e:
            print(f"Erreur lors de la récupération des informations serveur: {e}")
            traceback.print_exc()
            return False

    async def get_clients_status(self):
        """Récupère le statut des clients et du serveur Snapcast"""
        # D'abord obtenir les infos serveur
        await self.get_server_info()
        
        command = {
            "id": 3,
            "jsonrpc": "2.0",
            "method": "Server.GetStatus"
        }
        
        response = await self.send_command(command)
        if response and "result" in response:
            try:
                server_status = response["result"]["server"]
                old_clients_count = len(self.clients)
                
                # Mise à jour des clients
                self.clients = []
                if "groups" in server_status:
                    for group in server_status["groups"]:
                        for client in group["clients"]:
                            if client["connected"]:
                                client_info = {
                                    "id": client["id"],
                                    "host": client["host"]["name"],
                                    "connected": client["connected"]
                                }
                                self.clients.append(client_info)
                
                
                await self.notify_clients_status()
                return True
            except Exception as e:
                print(f"Erreur lors du traitement de la réponse: {e}")
                traceback.print_exc()
        
        await self.notify_clients_status()
        return False


    async def notify_clients_status(self):
        """Envoie la liste des clients et les infos serveur au frontend"""
        message = {
            "type": "clients_status",
            "clients": self.clients,
            "server_available": self.server_available,
            "server_info": self.server_info
        }
        print(f"Envoi du statut Snapcast: {message}")
        await self.websocket_manager.broadcast_to_service(message, "snapcast")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"Message Snapcast reçu: {message}")
        message_type = message.get("type")
        
        if message_type == "get_status":
            await self.get_clients_status()
            

    async def set_client_volume(self, client_id: str, volume: int) -> bool:
        """Modifie le volume d'un client"""
        command = {
            "id": 2,
            "jsonrpc": "2.0",
            "method": "Client.SetVolume",
            "params": {
                "id": client_id,
                "volume": {"muted": False, "percent": volume}
            }
        }

        response = await self.send_command(command)
        return response is not None