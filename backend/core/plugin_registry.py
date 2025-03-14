# backend/core/plugin_registry.py
import logging
import asyncio
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class PluginRegistry:
    """
    Registre central qui gère tous les plugins.
    """
    def __init__(self, websocket_manager, event_bus):
        self.plugins = {}
        self.sources = {}  # Plugins de type source audio
        self.services = {} # Plugins de type service système
        self.websocket_manager = websocket_manager
        self.event_bus = event_bus
        self.current_source = None
        self.is_switching = False
        
    def register_plugin(self, plugin):
        """
        Enregistre un plugin dans le registre.
        
        Args:
            plugin (BasePlugin): Instance du plugin à enregistrer
        """
        self.plugins[plugin.plugin_id] = plugin
        
        if plugin.plugin_type == BasePlugin.TYPE_SOURCE:
            self.sources[plugin.plugin_id] = plugin
            logger.info(f"Source audio enregistrée: {plugin.name} ({plugin.plugin_id})")
        elif plugin.plugin_type == BasePlugin.TYPE_SERVICE:
            self.services[plugin.plugin_id] = plugin
            logger.info(f"Service système enregistré: {plugin.name} ({plugin.plugin_id})")
        else:
            logger.warning(f"Type de plugin inconnu: {plugin.plugin_type}")
    
    async def initialize_plugins(self):
        """
        Initialise tous les plugins enregistrés.
        """
        logger.info("Initialisation de tous les plugins...")
        
        for plugin_id, plugin in self.plugins.items():
            try:
                success = await plugin.initialize()
                if not success:
                    logger.error(f"Échec de l'initialisation du plugin {plugin_id}")
            except Exception as e:
                logger.exception(f"Erreur lors de l'initialisation du plugin {plugin_id}: {e}")
                
        logger.info("Initialisation des plugins terminée")
    
    async def switch_audio_source(self, source_id):
        """
        Change la source audio active.
        
        Args:
            source_id (str): Identifiant de la nouvelle source
            
        Returns:
            bool: True si le changement a réussi, False sinon
        """
        if self.is_switching:
            logger.warning("Changement de source déjà en cours")
            return False
            
        if source_id == self.current_source:
            logger.info(f"Source {source_id} déjà active")
            return True
            
        self.is_switching = True
        await self._notify_source_change()
        
        old_source = self.current_source
        logger.info(f"Changement de source: {old_source} -> {source_id}")
        
        # Désactiver la source actuelle
        if old_source:
            current = self.sources.get(old_source)
            if current:
                try:
                    await current.deactivate()
                except Exception as e:
                    logger.error(f"Erreur lors de la désactivation de {old_source}: {e}")
        
        # Activer la nouvelle source
        success = False
        if source_id in self.sources:
            new_source = self.sources[source_id]
            try:
                success = await new_source.activate()
                if success:
                    self.current_source = source_id
                    
                    # Notifier les services du changement de source
                    await self.event_bus.publish("source_changed", {
                        "old_source": old_source,
                        "new_source": source_id
                    })
                    logger.info(f"Source changée avec succès: {source_id}")
                else:
                    logger.error(f"Échec de l'activation de la source {source_id}")
            except Exception as e:
                logger.exception(f"Erreur lors de l'activation de {source_id}: {e}")
        else:
            logger.error(f"Source inconnue: {source_id}")
        
        self.is_switching = False
        await self._notify_source_change()
        return success
    
    async def toggle_service(self, service_id, enable=True):
        """
        Active ou désactive un service système.
        
        Args:
            service_id (str): Identifiant du service
            enable (bool): True pour activer, False pour désactiver
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if service_id not in self.services:
            logger.error(f"Service inconnu: {service_id}")
            return False
            
        service = self.services[service_id]
        try:
            if enable:
                logger.info(f"Activation du service: {service_id}")
                return await service.enable()
            else:
                logger.info(f"Désactivation du service: {service_id}")
                return await service.disable()
        except Exception as e:
            logger.exception(f"Erreur lors de la {enable and 'activation' or 'désactivation'} de {service_id}: {e}")
            return False
    
    async def handle_message(self, service, message):
        """
        Route les messages vers le plugin approprié.
        
        Args:
            service (str): Identifiant du service destinataire
            message (dict): Message à traiter
        """
        if service == "audio":
            return await self._handle_audio_messages(message)
            
        if service in self.plugins:
            plugin = self.plugins[service]
            return await plugin.handle_message(message)
        
        logger.warning(f"Service inconnu: {service}")
        
    async def _handle_audio_messages(self, message):
        """
        Gère les messages destinés au service audio.
        
        Args:
            message (dict): Message à traiter
        """
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "switch_source":
            source_id = data.get("source")
            if source_id:
                return await self.switch_audio_source(source_id)
            else:
                logger.error("Message switch_source sans source spécifiée")
        elif message_type == "get_status":
            return await self._notify_source_change()
        else:
            logger.warning(f"Type de message audio inconnu: {message_type}")
    
    async def _notify_source_change(self):
        """
        Notifie les clients du changement de source audio.
        """
        source_name = None
        if self.current_source:
            source = self.sources.get(self.current_source)
            source_name = source.plugin_id if source else None
        
        message = {
            "type": "audio_state_change",
            "data": {
                "current_source": source_name or "none",
                "is_switching": self.is_switching
            }
        }
        
        await self.websocket_manager.broadcast_to_service(message, "audio")