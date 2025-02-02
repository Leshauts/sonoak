import aiohttp
import asyncio
import json
from typing import Dict, Optional

class SpotifyPlayerManager:
    def __init__(self, websocket_manager, spotify_manager):
        self.websocket_manager = websocket_manager
        self.spotify_manager = spotify_manager
        self.librespot_host = "localhost"
        self.librespot_port = 3678
        self.current_track_metadata = None  # Pour les métadonnées persistantes
        self.playback_state = {            # Pour l'état de lecture
            "is_playing": False,
            "volume": 0,
            "position": 0
        }
        self.polling_task = None

    async def start_polling(self):
        """Démarre le polling du statut"""
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self._poll_status())

    async def handle_librespot_event(self, event):
        """Gère les événements WebSocket de go-librespot"""
        print(f"Événement Librespot reçu: {event}")
        
        event_type = event.get('type')
        event_data = event.get('data')

        if event_type == 'metadata' or event_type == 'seek':
            # Forcer une mise à jour du statut pour obtenir toutes les métadonnées
            await self.get_playback_status(force_notify=True)
        elif event_type in ['active', 'inactive', 'will_play', 'playing', 'paused']:
            # Ces événements peuvent contenir des informations importantes
            await self.get_playback_status(force_notify=True)

    async def _poll_status(self):
        """Vérifie périodiquement l'état de lecture"""
        while True:
            try:
                status = await self.get_playback_status()
                if status and 'track' in status:
                    await self.notify_status()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Erreur lors du polling: {e}")
                await asyncio.sleep(1)

    async def get_playback_status(self, force_notify: bool = False) -> Optional[Dict]:
        """Récupère l'état de lecture actuel"""
        try:
            url = f'http://{self.librespot_host}:{self.librespot_port}/status'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"Statut Spotify reçu: {status}")
                        should_notify = self._update_track_state(status)
                        if should_notify or force_notify:
                            await self.notify_status()
                            await self.spotify_manager.get_status()
                        return status
        except Exception as e:
            print(f"Erreur lors de la récupération du statut: {e}")
            return None

    def _update_track_state(self, status: Dict) -> bool:
        """Met à jour l'état interne et retourne True si l'état a changé"""
        try:
            if not status:
                return False

            track_data = status.get("track", {})
            state_changed = False

            # Extraire la position du morceau
            current_position = track_data.get("position", 0)

            # Mettre à jour l'état de lecture
            new_playback_state = {
                "is_playing": not (status.get("stopped", True) or status.get("paused", True)),
                "volume": status.get("volume", 0),
                "position": current_position
            }

            if new_playback_state != self.playback_state:
                self.playback_state = new_playback_state
                state_changed = True

            # Mise à jour des métadonnées si on a des données valides
            if track_data and track_data.get("name"):
                new_metadata = {
                    "track_name": track_data.get("name"),
                    "artist_names": track_data.get("artist_names", []),
                    "album_name": track_data.get("album_name"),
                    "album_cover_url": track_data.get("album_cover_url"),
                    "duration": track_data.get("duration"),
                    "position": current_position
                }

                # Force une mise à jour si c'est une nouvelle piste ou si l'état a changé
                if (self.current_track_metadata is None or 
                    new_metadata != self.current_track_metadata or 
                    current_position != self.current_track_metadata.get("position", 0)):
                    self.current_track_metadata = new_metadata
                    state_changed = True

            return state_changed

        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'état: {e}")
            return False

    async def notify_status(self):
        """Envoie l'état de lecture au frontend"""
        try:
            if self.current_track_metadata is not None:
                # S'assurer que la position est incluse dans le statut
                formatted_status = {
                    **self.current_track_metadata,
                    "is_playing": self.playback_state["is_playing"],
                    "volume": self.playback_state["volume"],
                    "position": self.playback_state["position"]
                }
                
                print(f"Envoi du statut au frontend: {formatted_status}")
                message = {
                    "type": "playback_status",
                    "status": formatted_status
                }
                await self.websocket_manager.broadcast_to_service(message, "spotify")
                await self.spotify_manager.notify_status()

        except Exception as e:
            print(f"Erreur lors de la notification du statut: {e}")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        message_type = message.get("type")
        
        if message_type == "get_playback_status":
            await self.get_playback_status(force_notify=True)
            if self.current_track_metadata is not None:
                await self.notify_status()
        
        elif message_type in ["play_pause", "next_track", "previous_track", "seek"]:
            endpoint = {
                "play_pause": "/player/playpause",
                "next_track": "/player/next",
                "previous_track": "/player/prev",
                "seek": "/player/seek"
            }[message_type]

            url = f'http://{self.librespot_host}:{self.librespot_port}{endpoint}'
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Content-Type': 'application/json'}
                    data = {}
                    if message_type == "seek":
                        data["position"] = message.get("position", 0)
                    
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status != 200:
                            print(f"Erreur lors de la commande {message_type}: statut {response.status}")
                        else:
                            # Forcer une mise à jour immédiate du statut après chaque action
                            await self.get_playback_status(force_notify=True)
            except Exception as e:
                print(f"Erreur lors de la commande {message_type}: {e}")