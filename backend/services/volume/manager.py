import asyncio
import logging
import alsaaudio
from typing import Tuple

logger = logging.getLogger(__name__)

class VolumeManager:
    # Limites réelles du volume ALSA
    MIN_VOLUME = 22
    MAX_VOLUME = 80

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.mixer = None
        self._volume = 0
        self._lock = asyncio.Lock()
        
    def _interpolate_to_display(self, actual_volume: int) -> int:
        """Convertit le volume réel (20-80) en volume d'affichage (0-100)"""
        actual_range = self.MAX_VOLUME - self.MIN_VOLUME
        normalized = actual_volume - self.MIN_VOLUME
        return round((normalized / actual_range) * 100)

    def _interpolate_from_display(self, display_volume: int) -> int:
        """Convertit le volume d'affichage (0-100) en volume réel (20-80)"""
        actual_range = self.MAX_VOLUME - self.MIN_VOLUME
        return round((display_volume / 100) * actual_range) + self.MIN_VOLUME

    async def initialize(self):
        """Initialize the volume manager and set up ALSA mixer for HiFiBerry AMP2"""
        try:
            logger.info("Initializing HiFiBerry AMP2 Digital mixer")
            logger.info(f"Volume limits: min={self.MIN_VOLUME}%, max={self.MAX_VOLUME}%")
            self.mixer = alsaaudio.Mixer('Digital')
            
            # Get initial volume and ensure it's within limits
            initial_volume = self.get_alsa_volume()
            self._volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, initial_volume))
            
            # Si le volume initial est hors limites, le régler
            if initial_volume != self._volume:
                self.set_alsa_volume(self._volume)
            
            logger.info(f"Volume Manager initialized with volume: {self._volume}")
            await self.broadcast_volume_status()
            
        except Exception as e:
            logger.error(f"Failed to initialize ALSA mixer: {e}")
            raise

    def get_alsa_volume(self) -> int:
        """Get the current ALSA volume"""
        volumes = self.mixer.getvolume()
        return int(sum(volumes) / len(volumes))

    def set_alsa_volume(self, volume: int) -> None:
        """Set the ALSA volume"""
        volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, volume))
        self.mixer.setvolume(volume)
        logger.debug(f"ALSA volume set to {volume}")

    async def broadcast_volume_status(self):
        """Broadcast current volume status to all clients"""
        current_volume = self.get_alsa_volume()
        display_volume = self._interpolate_to_display(current_volume)
        
        await self.websocket_manager.broadcast_to_service({
            "type": "volume_status",
            "volume": display_volume  # Envoie le volume interpolé (0-100)
        }, "volume")

    async def set_volume(self, display_volume: int) -> None:
        """Set the system volume from display value (0-100)"""
        async with self._lock:
            try:
                # Convertir le volume d'affichage en volume réel
                actual_volume = self._interpolate_from_display(display_volume)
                logger.debug(f"Setting volume: display={display_volume}% → actual={actual_volume}%")
                
                self.set_alsa_volume(actual_volume)
                self._volume = actual_volume
                
                await self.broadcast_volume_status()
                
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
                raise

    async def get_volume(self) -> int:
        """Get the current system volume as display value (0-100)"""
        try:
            actual_volume = self.get_alsa_volume()
            return self._interpolate_to_display(actual_volume)
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            raise

    async def adjust_volume(self, display_delta: int) -> None:
        """Adjust the volume by a relative display amount"""
        async with self._lock:
            try:
                current_actual = self.get_alsa_volume()
                current_display = self._interpolate_to_display(current_actual)
                new_display = max(0, min(100, current_display + display_delta))
                new_actual = self._interpolate_from_display(new_display)
                
                logger.debug(f"Adjusting volume: display={current_display}%→{new_display}% (actual={current_actual}%→{new_actual}%)")
                
                if new_actual != current_actual:
                    self.set_alsa_volume(new_actual)
                    self._volume = new_actual
                    await self.broadcast_volume_status()
                else:
                    logger.debug("Volume adjustment skipped: no change in actual volume")
                
            except Exception as e:
                logger.error(f"Error adjusting volume: {e}")
                raise

    async def handle_message(self, message: dict) -> None:
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            logger.debug(f"Handling volume message: {message}")
            
            if message_type == "get_volume":
                await self.broadcast_volume_status()
                
            elif message_type == "set_volume":
                volume = message.get("volume")
                if volume is not None:
                    await self.set_volume(volume)
                    
            elif message_type == "adjust_volume":
                delta = message.get("delta")
                if delta is not None:
                    await self.adjust_volume(delta)
                    
        except Exception as e:
            logger.error(f"Error handling volume message: {e}")
            raise