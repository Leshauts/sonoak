# backend/plugins/audio_source/base_source.py
import logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class AudioSourcePlugin(BasePlugin):
    """
    Classe de base pour les plugins de source audio.
    Une seule source audio peut être active à la fois.
    """
    def __init__(self, plugin_registry, plugin_id):
        super().__init__(plugin_registry, plugin_id)
        self.plugin_type = self.TYPE_SOURCE
        
        # Nom du script pour activer cette source
        self.activation_script = f"switch-to-{plugin_id}.sh"
    
    async def activate(self):
        """
        Active cette source audio.
        """
        logger.info(f"Activation de la source audio: {self.name}")
        
        success = await self._execute_script(self.activation_script)
        if success:
            self.is_active = True
            await self.send_status()
            logger.info(f"Source {self.name} activée avec succès")
        else:
            logger.error(f"Échec de l'activation de la source {self.name}")
            
        return success
    
    async def deactivate(self):
        """
        Désactive cette source audio.
        """
        logger.info(f"Désactivation de la source audio: {self.name}")
        self.is_active = False
        await self.send_status()
        return True
        
    async def send_status(self):
        """
        Envoie l'état actuel de la source au frontend.
        """
        status_message = {
            "type": f"{self.plugin_id}_status",
            "data": {
                "active": self.is_active,
                "name": self.name
            }
        }
        await self.plugin_registry.websocket_manager.broadcast_to_service(
            status_message, self.plugin_id
        )