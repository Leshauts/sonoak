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
            "volume": 0
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

        if event_type == 'metadata':
            # Forcer une mise à jour du statut pour obtenir toutes les métadonnées
            await self.get_playback_status()
        elif event_type in ['active', 'inactive', 'will_play', 'playing', 'paused']:
            # Ces événements peuvent contenir des informations importantes
            # Forçons une mise à jour du statut
            await self.get_playback_status()

    async def _poll_status(self):
        """Vérifie périodiquement l'état de lecture"""
        while True:
            try:
                # Toujours vérifier le statut au démarrage
                status = await self.get_playback_status()
                if status and status.get('track'):
                    # Si nous avons des données de piste, forcer une notification
                    await self.notify_status()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Erreur lors du polling: {e}")
                await asyncio.sleep(1)

    async def get_playback_status(self, force_notify: bool = False) -> Optional[Dict]:
        """Récupère l'état de lecture actuel
        
        Args:
            force_notify: Si True, force l'envoi d'une notification même si l'état n'a pas changé
        """
        try:
            url = f'http://{self.librespot_host}:{self.librespot_port}/status'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"Statut Spotify reçu: {status}")  # Debug log
                        should_notify = self._update_track_state(status)
                        if should_notify or force_notify:
                            await self.notify_status()
                            await self.spotify_manager.get_status()
                        return status
        except Exception as e:
            print(f"Erreur lors de la récupération du statut: {e}")
            return None

    def _update_track_state(self, status: Dict) -> bool:
        """Met à jour l'état interne du lecteur en préservant les métadonnées"""
        try:
            if not status:
                return False

            track_data = status.get("track", {})
            state_changed = False
            
            # Force une mise à jour si nous n'avons pas encore de métadonnées
            if self.current_track_metadata is None and track_data and track_data.get("name"):
                state_changed = True

            # Mettre à jour l'état de lecture
            new_playback_state = {
                "is_playing": not (status.get("stopped", True) or status.get("paused", True)),
                "volume": status.get("volume", 0)
            }

            if new_playback_state != self.playback_state:
                self.playback_state = new_playback_state
                state_changed = True

            # Ne mettre à jour les métadonnées que si on a des données valides
            if track_data and track_data.get("name"):
                new_metadata = {
                    "track_name": track_data.get("name"),
                    "artist_names": track_data.get("artist_names", []),
                    "album_name": track_data.get("album_name"),
                    "album_cover_url": track_data.get("album_cover_url"),
                    "duration": track_data.get("duration")
                }

                # Si c'est la première piste ou si la piste a changé
                if self.current_track_metadata is None or new_metadata != self.current_track_metadata:
                    self.current_track_metadata = new_metadata
                    state_changed = True

            return state_changed
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'état: {e}")
            return False

    async def notify_status(self):
        """Envoie l'état de lecture au frontend"""
        try:
            print("Notification du statut:")
            print(f"Métadonnées actuelles: {self.current_track_metadata}")
            print(f"État de lecture: {self.playback_state}")
            
            # N'envoyer que si on a des métadonnées valides
            if self.current_track_metadata is not None:
                formatted_status = {
                    **self.current_track_metadata,
                    "is_playing": self.playback_state["is_playing"],
                    "volume": self.playback_state["volume"]
                }
                
                print(f"Envoi au frontend: {formatted_status}")
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
            # Forcer une notification lors d'une demande explicite de statut
            await self.get_playback_status()
            
            # Si nous avons des métadonnées, forcer l'envoi même sans changement
            if self.current_track_metadata is not None:
                print("Envoi forcé des métadonnées existantes")
                await self.notify_status()
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
        elif message_type == "seek":
            url = f'http://{self.librespot_host}:{self.librespot_port}/player/seek'
            try:
                position = message.get("position")
                async with aiohttp.ClientSession() as session:
                    headers = {'Content-Type': 'application/json'}
                    data = {"position": position}
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status != 200:
                            print(f"Erreur lors du seek: statut {response.status}")
                        else:
                            await self.get_playback_status()
            except Exception as e:
                print(f"Erreur lors du seek: {e}")