import asyncio
import logging
import alsaaudio
from typing import Tuple

logger = logging.getLogger(__name__)

class VolumeManager:
    # Limites réelles du volume ALSA
    MIN_VOLUME = 40
    MAX_VOLUME = 98
    VOLUME_STEP = 5  # Change de 5% le volume affiché à chaque clic

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.mixer = None
        self._volume = 0
        self._lock = asyncio.Lock()
        self._is_adjusting = False
        
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
            
            initial_volume = self.get_alsa_volume()
            self._volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, initial_volume))
            
            if initial_volume != self._volume:
                self.set_alsa_volume(self._volume)
            
            logger.info(f"Volume Manager initialized with volume: {self._volume}")
            await self.broadcast_volume_status()
            
        except Exception as e:
            logger.error(f"Failed to initialize ALSA mixer: {e}")
            raise

    async def broadcast_volume_status(self):
        """Broadcast current volume status to all clients"""
        current_volume = self.get_alsa_volume()
        display_volume = self._interpolate_to_display(current_volume)
        
        await self.websocket_manager.broadcast_to_service({
            "type": "volume_status",
            "volume": display_volume,
            "alsa_volume": current_volume,
            "show_volume_bar": True,
            "is_initial_status": False  # Par défaut, ce n'est pas un status initial
        }, "volume")

    async def broadcast_initial_status(self):
        """Broadcast initial volume status without triggering volume bar"""
        current_volume = self.get_alsa_volume()
        display_volume = self._interpolate_to_display(current_volume)
        
        await self.websocket_manager.broadcast_to_service({
            "type": "volume_status",
            "volume": display_volume,
            "alsa_volume": current_volume,
            "show_volume_bar": False,
            "is_initial_status": True
        }, "volume")

    def get_alsa_volume(self) -> int:
        """Get the current ALSA volume"""
        volumes = self.mixer.getvolume()
        return int(sum(volumes) / len(volumes))

    def set_alsa_volume(self, volume: int) -> None:
        """Set the ALSA volume"""
        volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, volume))
        self.mixer.setvolume(volume)
        logger.debug(f"ALSA volume set to {volume}")

    async def set_volume(self, display_volume: int) -> None:
        """Set the system volume from display value (0-100)"""
        async with self._lock:
            try:
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

    async def adjust_volume_gradually(self, display_delta: int, steps: int = 3, interval: float = 0.05) -> None:
        """Adjust the volume gradually over multiple steps"""
        try:
            if self._is_adjusting:
                logger.debug("Volume adjustment already in progress, skipping")
                return

            self._is_adjusting = True
            
            # Récupérer les volumes actuels
            current_actual = self.get_alsa_volume()
            current_display = self._interpolate_to_display(current_actual)
            
            # Calculer les volumes cibles
            target_display = max(0, min(100, current_display + (display_delta * self.VOLUME_STEP)))
            target_actual = self._interpolate_from_display(target_display)
            
            # Calculer les incréments
            actual_delta = target_actual - current_actual
            step_delta = actual_delta / steps
            
            logger.debug(f"""Starting gradual volume adjustment:
                Current: display={current_display}% (actual={current_actual})
                Target: display={target_display}% (actual={target_actual})
                Steps: {steps}, Interval: {interval}s
                Step delta: {step_delta}""")
            
            # Appliquer les changements graduellement
            for i in range(steps):
                next_actual = round(current_actual + (step_delta * (i + 1)))
                next_actual = max(self.MIN_VOLUME, min(self.MAX_VOLUME, next_actual))
                
                self.set_alsa_volume(next_actual)
                self._volume = next_actual
                
                next_display = self._interpolate_to_display(next_actual)
                logger.debug(f"Step {i + 1}/{steps}: display={next_display}% (actual={next_actual})")
                
                await self.broadcast_volume_status()
                
                if i < steps - 1:  # Ne pas attendre après la dernière étape
                    await asyncio.sleep(interval)
            
            logger.debug("Gradual volume adjustment complete")
            
        except Exception as e:
            logger.error(f"Error during gradual volume adjustment: {e}")
            raise
        finally:
            self._is_adjusting = False

    async def handle_message(self, message: dict) -> None:
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            logger.debug(f"Handling volume message: {message}")
            
            if message_type == "get_volume":
                await self.broadcast_initial_status()  # Utiliser la nouvelle méthode
                
            elif message_type == "set_volume":
                volume = message.get("volume")
                if volume is not None:
                    await self.set_volume(volume)
                    
            elif message_type == "adjust_volume":
                delta = message.get("delta")
                if delta is not None:
                    await self.adjust_volume_gradually(delta, steps=3, interval=0.05)
                    
        except Exception as e:
            logger.error(f"Error handling volume message: {e}")
            raise