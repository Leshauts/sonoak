import asyncio
import logging
import alsaaudio

logger = logging.getLogger(__name__)

class VolumeManager:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.mixer = None
        self._volume = 0
        
    async def initialize(self):
        """Initialize the volume manager and set up ALSA mixer for HiFiBerry DAC+"""
        try:
            # Utiliser le mixer 'Digital' pour HiFiBerry DAC+
            logger.info("Initializing HiFiBerry DAC+ Digital mixer")
            self.mixer = alsaaudio.Mixer('Digital')
            
            # Get initial volume
            self._volume = self.mixer.getvolume()[0]
            logger.info(f"Volume Manager initialized with volume: {self._volume}")
            
            # Broadcast initial volume to all clients
            await self.broadcast_volume_status()
        except Exception as e:
            logger.error(f"Failed to initialize ALSA mixer: {e}")
            raise

    async def broadcast_volume_status(self):
        """Broadcast current volume status to all clients"""
        await self.websocket_manager.broadcast_to_service({
            "type": "volume_status",
            "volume": self._volume
        }, "volume")

    async def set_volume(self, volume: int) -> None:
        """Set the system volume"""
        try:
            # Ensure volume is within bounds
            volume = max(0, min(100, volume))
            
            # Set ALSA volume
            self.mixer.setvolume(volume)
            self._volume = volume
            
            # Broadcast volume change
            await self.broadcast_volume_status()
            
            logger.debug(f"Volume set to {volume}")
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            raise

    async def get_volume(self) -> int:
        """Get the current system volume"""
        try:
            self._volume = self.mixer.getvolume()[0]
            return self._volume
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            raise

    async def adjust_volume(self, delta: int) -> None:
        """Adjust the volume by a relative amount"""
        try:
            current_volume = await self.get_volume()
            new_volume = max(0, min(100, current_volume + delta))
            await self.set_volume(new_volume)
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