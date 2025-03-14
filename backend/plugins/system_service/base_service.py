# backend/plugins/system_service/base_service.py
import logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class SystemServicePlugin(BasePlugin):
    """
    Classe de base pour les plugins de service système.
    Plusieurs services système peuvent être actifs simultanément.
    """
    def __init__(self, plugin_registry, plugin_id):
        super().__init__(plugin_registry, plugin_id)
        self.plugin_type = self.TYPE_SERVICE
    
    async def enable(self):
        """
        Active ce service système.
        """
        logger.info(f"Activation du service: {self.name}")
        self.is_active = True
        await self.send_status()
        return True
    
    async def disable(self):
        """
        Désactive ce service système.
        """
        logger.info(f"Désactivation du service: {self.name}")
        self.is_active = False
        await self.send_status()
        return True
        
    async def handle_source_change(self, old_source, new_source):
        """
        Appelé quand la source audio change.
        À implémenter dans les sous-classes si nécessaire.
        """
        pass