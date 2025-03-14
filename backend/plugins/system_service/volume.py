# backend/plugins/system_service/volume.py
import logging
import asyncio
import alsaaudio
from .base_service import SystemServicePlugin

logger = logging.getLogger(__name__)

class VolumePlugin(SystemServicePlugin):
    """
    Plugin pour le contrôle du volume système via ALSA.
    """
    # Limites réelles du volume ALSA
    MIN_VOLUME = 40
    MAX_VOLUME = 98
    VOLUME_STEP = 5

    def __init__(self, plugin_registry):
        super().__init__(plugin_registry, "volume")
        self.name = "Volume Control"
        self.mixer = None
        self._volume = 0
        self._lock = asyncio.Lock()
        self._is_adjusting = False
        
    async def initialize(self):
        """
        Initialise le contrôle de volume ALSA.
        """
        try:
            logger.info("Initialisation du contrôle de volume HiFiBerry AMP2 Digital")
            logger.info(f"Limites volume: min={self.MIN_VOLUME}%, max={self.MAX_VOLUME}%")
            
            self.mixer = alsaaudio.Mixer('Digital')
            
            initial_volume = self.get_alsa_volume()
            self._volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, initial_volume))
            
            if initial_volume != self._volume:
                self.set_alsa_volume(self._volume)
            
            logger.info(f"Volume initialisé: {self._volume}")
            self.is_active = True
            await self.send_status()
            return True
            
        except Exception as e:
            logger.error(f"Échec de l'initialisation du contrôle de volume: {e}")
            return False
    
    def _interpolate_to_display(self, actual_volume):
        """
        Convertit le volume réel (40-98) en volume d'affichage (0-100).
        """
        actual_range = self.MAX_VOLUME - self.MIN_VOLUME
        normalized = actual_volume - self.MIN_VOLUME
        return round((normalized / actual_range) * 100)

    def _interpolate_from_display(self, display_volume):
        """
        Convertit le volume d'affichage (0-100) en volume réel (40-98).
        """
        actual_range = self.MAX_VOLUME - self.MIN_VOLUME
        return round((display_volume / 100) * actual_range) + self.MIN_VOLUME
        
    def get_alsa_volume(self):
        """
        Obtient le volume ALSA actuel.
        
        Returns:
            int: Volume actuel (0-100)
        """
        volumes = self.mixer.getvolume()
        return int(sum(volumes) / len(volumes))

    def set_alsa_volume(self, volume):
        """
        Définit le volume ALSA.
        
        Args:
            volume (int): Volume à définir (0-100)
        """
        volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, volume))
        self.mixer.setvolume(volume)
        logger.debug(f"Volume ALSA défini: {volume}")
        
    async def send_status(self):
        """
        Envoie le statut du volume au frontend.
        """
        current_volume = self.get_alsa_volume()
        display_volume = self._interpolate_to_display(current_volume)
        
        message = {
            "type": "volume_status",
            "data": {
                "volume": display_volume,
                "alsa_volume": current_volume,
                "show_volume_bar": True,
                "is_initial_status": False
            }
        }
        
        await self.plugin_registry.websocket_manager.broadcast_to_service(message, self.plugin_id)
    
    async def handle_message(self, message):
        """
        Traite les messages de contrôle du volume.
        
        Args:
            message (dict): Message à traiter
        """
        message_type = message.get("type")
        
        if message_type == "get_volume":
            await self.send_initial_status()
        elif message_type == "set_volume":
            volume = message.get("volume")
            if volume is not None:
                await self.set_volume(volume)
        elif message_type == "adjust_volume":
            delta = message.get("delta")
            if delta is not None:
                await self.adjust_volume_gradually(delta)
                
    async def send_initial_status(self):
        """
        Envoie le statut initial du volume sans déclencher la barre de volume.
        """
        current_volume = self.get_alsa_volume()
        display_volume = self._interpolate_to_display(current_volume)
        
        message = {
            "type": "volume_status",
            "data": {
                "volume": display_volume,
                "alsa_volume": current_volume,
                "show_volume_bar": False,
                "is_initial_status": True
            }
        }
        
        await self.plugin_registry.websocket_manager.broadcast_to_service(message, self.plugin_id)
    
    async def set_volume(self, display_volume):
        """
        Définit le volume système.
        
        Args:
            display_volume (int): Volume à définir (0-100)
        """
        async with self._lock:
            try:
                actual_volume = self._interpolate_from_display(display_volume)
                logger.debug(f"Définition du volume: affichage={display_volume}% → réel={actual_volume}%")
                
                self.set_alsa_volume(actual_volume)
                self._volume = actual_volume
                
                await self.send_status()
                
            except Exception as e:
                logger.error(f"Erreur lors de la définition du volume: {e}")
    
    async def adjust_volume_gradually(self, display_delta, steps=3, interval=0.05):
        """
        Ajuste le volume progressivement.
        
        Args:
            display_delta (int): Changement de volume (-1 ou 1)
            steps (int): Nombre d'étapes pour l'ajustement
            interval (float): Intervalle entre les étapes
        """
        if self._is_adjusting:
            return
            
        self._is_adjusting = True
        
        try:
            # Calculer volumes actuels et cibles
            current_actual = self.get_alsa_volume()
            current_display = self._interpolate_to_display(current_actual)
            
            target_display = max(0, min(100, current_display + (display_delta * self.VOLUME_STEP)))
            target_actual = self._interpolate_from_display(target_display)
            
            actual_delta = target_actual - current_actual
            step_delta = actual_delta / steps
            
            # Appliquer les changements graduellement
            for i in range(steps):
                next_actual = round(current_actual + (step_delta * (i + 1)))
                next_actual = max(self.MIN_VOLUME, min(self.MAX_VOLUME, next_actual))
                
                self.set_alsa_volume(next_actual)
                self._volume = next_actual
                
                await self.send_status()
                
                if i < steps - 1:
                    await asyncio.sleep(interval)
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'ajustement progressif du volume: {e}")
        finally:
            self._is_adjusting = False