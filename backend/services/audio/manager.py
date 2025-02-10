# backend/services/audio/manager.py
import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class AudioSource(Enum):
    NONE = "none"
    SPOTIFY = "spotify"
    BLUETOOTH = "bluetooth"
    MACOS = "macos"

class AudioManager:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.current_source: AudioSource = AudioSource.NONE
        self.scripts_dir = Path("~/sonoak/scripts").expanduser()
        self.is_switching = False
        
        # Mapping des sources vers leurs scripts
        self.source_scripts = {
            AudioSource.SPOTIFY: "switch-to-spotify.sh",
            AudioSource.BLUETOOTH: "switch-to-bluetooth.sh",
            AudioSource.MACOS: "switch-to-macos.sh"
        }

    async def initialize(self):
        """Initialise l'état initial de l'AudioManager"""
        logger.info("Initializing AudioManager")
        await self._notify_state_change()
        logger.info("AudioManager initialized successfully")

    async def handle_message(self, message: dict):
        """Gère les messages WebSocket entrants"""
        try:
            message_type = message.get("type")
            data = message.get("data", {})

            if message_type == "switch_source":
                source = data.get("source")
                if source:
                    await self.switch_source(AudioSource(source))
            elif message_type == "get_status":
                await self._notify_state_change()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise

    async def switch_source(self, source: AudioSource) -> bool:
        """
        Change la source audio active.
        Retourne True si le changement est réussi, False sinon.
        """
        if self.is_switching:
            logger.warning("Changement de source déjà en cours")
            return False
            
        if source == self.current_source:
            logger.info(f"Déjà sur la source {source.value}")
            return True
            
        try:
            self.is_switching = True
            logger.info(f"Changement vers la source {source.value}")
            
            if script_name := self.source_scripts.get(source):
                success = await self._execute_script(script_name)
                if success:
                    self.current_source = source
                    await self._notify_state_change()
                    return True
                else:
                    logger.error(f"Échec du script pour {source.value}")
                    return False
            else:
                logger.error(f"Pas de script défini pour {source.value}")
                return False
                
        finally:
            self.is_switching = False
            
    async def _execute_script(self, script_name: str) -> bool:
        """Exécute un script de changement de source"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script non trouvé: {script_path}")
            return False
            
        try:
            script_path.chmod(0o755)
            process = await asyncio.create_subprocess_exec(
                "sudo", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=30.0
                )
                return process.returncode == 0
            except asyncio.TimeoutError:
                logger.error(f"Timeout lors de l'exécution de {script_name}")
                process.kill()
                return False
                
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de {script_name}: {e}")
            return False
            
    async def _notify_state_change(self):
        """Notifie tous les clients du changement d'état"""
        message = {
            "type": "audio_state_change",
            "data": {
                "current_source": self.current_source.value,
                "is_switching": self.is_switching
            }
        }
        await self.websocket_manager.broadcast_to_service(message, "audio")