# backend/plugins/base_plugin.py
import logging
import asyncio
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class BasePlugin:
    """
    Classe de base pour tous les plugins.
    """
    TYPE_SOURCE = "source"
    TYPE_SERVICE = "service"
    
    def __init__(self, plugin_registry, plugin_id):
        self.plugin_registry = plugin_registry
        self.plugin_id = plugin_id
        self.plugin_type = None  # À définir dans les sous-classes
        self.name = "Unnamed Plugin"
        self.is_active = False
        self.scripts_dir = Path(os.path.expanduser("~/sonoak/scripts")).expanduser()
    
    async def initialize(self):
        """Initialisation du plugin"""
        logger.info(f"Initialisation du plugin {self.name} ({self.plugin_id})")
        return True
    
    async def handle_message(self, message):
        """Traite les messages websocket pour ce plugin"""
        logger.debug(f"Message reçu pour {self.plugin_id}: {message}")
        message_type = message.get("type")
        
        if message_type == "get_status":
            await self.send_status()
    
    async def send_status(self):
        """Envoie l'état actuel au frontend"""
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
        
    async def _execute_script(self, script_name):
        """
        Exécute un script shell et retourne le succès/échec.
        
        Args:
            script_name (str): Nom du script à exécuter
            
        Returns:
            bool: True si l'exécution est réussie, False sinon
        """
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script non trouvé: {script_path}")
            return False
            
        try:
            script_path.chmod(0o755)  # Rendre exécutable
            
            logger.info(f"Exécution du script: {script_path}")
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
                
                if process.returncode == 0:
                    logger.info(f"Script {script_name} exécuté avec succès")
                    return True
                else:
                    logger.error(f"Échec du script {script_name}: {stderr.decode().strip()}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout lors de l'exécution de {script_name}")
                process.kill()
                return False
                
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de {script_name}: {e}")
            return False