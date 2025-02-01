# sonoak/backend/services/spotify/player_manager.py

import aiohttp
import asyncio
import json
from typing import Dict, Optional

class SpotifyPlayerManager:
    def __init__(self, websocket_manager, spotify_manager):  # Ajout de spotify_manager
        self.websocket_manager = websocket_manager
        self.spotify_manager = spotify_manager  # Référence au SpotifyManager
        self.librespot_host = "localhost"
        self.librespot_port = 3678
        self.current_track = None
        self.polling_task = None

    async def start_polling(self):
        """Démarre le polling du statut"""
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self._poll_status())

    async def _poll_status(self):
        """Vérifie périodiquement l'état de lecture"""
        while True:
            try:
                await self.get_playback_status()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Erreur lors du polling: {e}")
                await asyncio.sleep(1)

    async def get_playback_status(self) -> Optional[Dict]:
        """Récupère l'état de lecture actuel"""
        try:
            url = f'http://{self.librespot_host}:{self.librespot_port}/status'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        status = await response.json()
                        if status != self.current_track:
                            self.current_track = status
                            await self.notify_status()
                            # Forcer une mise à jour du statut de connexion aussi
                            await self.spotify_manager.get_status()
                        return status
        except Exception as e:
            print(f"Erreur lors de la récupération du statut: {e}")
            return None

    async def notify_status(self):
        """Envoie l'état de lecture au frontend"""
        if self.current_track:
            formatted_status = {
                "track_name": self.current_track.get("track", {}).get("name"),
                "artist_names": self.current_track.get("track", {}).get("artist_names", []),
                "album_name": self.current_track.get("track", {}).get("album_name"),
                "album_cover_url": self.current_track.get("track", {}).get("album_cover_url"),
                "duration": self.current_track.get("track", {}).get("duration"),
                "is_playing": not (self.current_track.get("stopped", True) or self.current_track.get("paused", True)),
                "volume": self.current_track.get("volume", 0)
            }
            
            message = {
                "type": "playback_status",
                "status": formatted_status
            }
            await self.websocket_manager.broadcast_to_service(message, "spotify")

        # **Ajout** : Envoyer le statut Spotify aussi
        await self.spotify_manager.notify_status()

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        message_type = message.get("type")
        
        if message_type == "get_playback_status":
            await self.get_playback_status()
        elif message_type == "play_pause":
            url = f'http://{self.librespot_host}:{self.librespot_port}/player/playpause'
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Content-Type': 'application/json'}
                    async with session.post(url, headers=headers, json={}) as response:
                        if response.status != 200:
                            print(f"Erreur lors de la commande play/pause: statut {response.status}")
                        else:
                            await self.get_playback_status()
            except Exception as e:
                print(f"Erreur lors de la commande play/pause: {e}")
        elif message_type == "next_track":
            url = f'http://{self.librespot_host}:{self.librespot_port}/player/next'
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Content-Type': 'application/json'}
                    async with session.post(url, headers=headers, json={}) as response:
                        if response.status != 200:
                            print(f"Erreur lors du passage à la piste suivante: statut {response.status}")
                        else:
                            await self.get_playback_status()
            except Exception as e:
                print(f"Erreur lors du passage à la piste suivante: {e}")
        elif message_type == "previous_track":
            url = f'http://{self.librespot_host}:{self.librespot_port}/player/prev'
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Content-Type': 'application/json'}
                    async with session.post(url, headers=headers, json={}) as response:
                        if response.status != 200:
                            print(f"Erreur lors du retour à la piste précédente: statut {response.status}")
                        else:
                            await self.get_playback_status()
            except Exception as e:
                print(f"Erreur lors du retour à la piste précédente: {e}")