import asyncio
import json
import aiohttp
from typing import List, Dict
import traceback
from services.audio.manager import AudioSource

class SpotifyManager:
    def __init__(self, websocket_manager, audio_manager=None):
        print("Initialisation du SpotifyManager...")
        self.websocket_manager = websocket_manager
        self.audio_manager = audio_manager
        self.librespot_host = "localhost"
        self.librespot_port = 3678
        self.current_status = {
            "connected": False,
            "username": None,
            "device_name": None
        }
        self.polling_task = None
        self.initialized = False

    async def connect_to_events(self):
        """Initialise la connexion avec go-librespot et démarre le polling"""
        print(f"Initialisation de la connexion avec go-librespot sur {self.librespot_host}:{self.librespot_port}")
        if not self.initialized:
            await self.get_status()  # Récupérer immédiatement le statut de connexion
            self.start_polling()
            self.initialized = True

    def start_polling(self):
        """Démarre la vérification périodique du statut"""
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self.poll_status())
            print("Démarrage du polling du statut Spotify")

    async def poll_status(self):
        """Vérifie périodiquement le statut"""
        while True:
            try:
                await self.get_status()
                await asyncio.sleep(2)  # Vérifie toutes les 2 secondes
            except Exception as e:
                print(f"Erreur lors du polling: {e}")
                await asyncio.sleep(2)

    async def get_status(self):
        """Récupère le statut via l'API REST"""
        try:
            url = f'http://{self.librespot_host}:{self.librespot_port}/status'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        status = await response.json()
                        old_connected = self.current_status["connected"]
                        
                        is_connected = not status.get("stopped", True) and status.get("username") is not None
                        
                        new_status = {
                            "connected": is_connected,
                            "username": status.get("username"),
                            "device_name": status.get("device_name")
                        }

                        if new_status != self.current_status:
                            self.current_status = new_status
                            
                            # Si le statut de connexion a changé
                            if old_connected != is_connected:
                                if self.audio_manager:
                                    if is_connected:
                                        await self.audio_manager.switch_source(AudioSource.SPOTIFY)
                                    else:
                                        await self.audio_manager.switch_source(AudioSource.NONE)
                            
                            await self.notify_status()
        except aiohttp.ClientError as e:
            print(f"Erreur de connexion à go-librespot: {e}")
            if self.current_status["connected"]:
                self.current_status = {
                    "connected": False,
                    "username": None,
                    "device_name": None
                }
                await self.notify_status()
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            traceback.print_exc()

    async def notify_status(self):
        """Envoie le statut au frontend"""
        message = {
            "type": "spotify_status",
            "status": self.current_status
        }
        print(f"Envoi du statut Spotify au frontend: {message}")
        await self.websocket_manager.broadcast_to_service(message, "spotify")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"Message Spotify reçu du frontend: {message}")
        message_type = message.get("type")
        
        if message_type == "get_status":
            # Force une récupération du statut et notification
            await self.get_status()
            # Force l'envoi du statut même s'il n'a pas changé
            await self.notify_status()
            # Si connecté, notifier l'AudioManager
            if self.current_status["connected"] and self.audio_manager:
                await self.audio_manager.switch_source(AudioSource.SPOTIFY)

    async def cleanup(self):
        """Nettoie les ressources"""
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            self.polling_task = None
        print("Nettoyage du SpotifyManager terminé")