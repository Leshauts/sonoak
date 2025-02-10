import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NavigationManager:
    def __init__(self, websocket_manager):
        """
        Initialise le gestionnaire de navigation.
        
        Args:
            websocket_manager: Le gestionnaire de WebSocket pour la communication avec les clients
        """
        logger.info("Initialisation du NavigationManager...")
        self.websocket_manager = websocket_manager
        self.current_route = "/"
        
        # Configuration des chemins
        self.scripts_dir = Path(os.path.expanduser("~/sonoak/scripts"))
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Dossier des scripts configuré: {self.scripts_dir}")
        
        # Mapping des routes vers les scripts
        self.route_scripts: Dict[str, str] = {
            "/bluetooth": "switch-to-bluetooth.sh",
            "/spotify": "switch-to-spotify.sh",
            "/macos": "switch-to-macos.sh"
        }
        logger.info(f"Routes configurées: {self.route_scripts}")
        
        # Vérification initiale des scripts
        self._verify_scripts()

    def _verify_scripts(self) -> None:
        """Vérifie l'existence de tous les scripts configurés."""
        for route, script in self.route_scripts.items():
            script_path = self.scripts_dir / script
            if not script_path.exists():
                logger.warning(f"Script manquant pour la route {route}: {script_path}")
            else:
                logger.info(f"Script vérifié pour la route {route}: {script_path}")

    async def execute_script(self, script_name: str) -> bool:
        """
        Exécute un script shell de manière asynchrone.
        
        Args:
            script_name: Nom du script à exécuter
            
        Returns:
            bool: True si l'exécution est réussie, False sinon
        """
        script_path = self.scripts_dir / script_name
        logger.info(f"Tentative d'exécution du script: {script_path}")
        
        if not script_path.exists():
            logger.error(f"Script non trouvé: {script_path}")
            return False

        try:
            # Rendre le script exécutable
            script_path.chmod(0o755)
            logger.debug(f"Script rendu exécutable: {script_path}")
            
            # Exécution du script avec sudo et timeout de 30 secondes
            process = await asyncio.create_subprocess_exec(
                "sudo",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                
                if process.returncode == 0:
                    logger.info(f"Script {script_name} exécuté avec succès")
                    logger.debug(f"Sortie: {stdout.decode().strip()}")
                    return True
                else:
                    logger.error(f"Échec de l'exécution du script {script_name}")
                    logger.error(f"Code de retour: {process.returncode}")
                    logger.error(f"Erreur: {stderr.decode().strip()}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout lors de l'exécution du script: {script_name}")
                process.kill()
                return False
                
        except Exception as e:
            logger.exception(f"Exception lors de l'exécution du script: {e}")
            return False

    async def set_current_route(self, route: str) -> None:
        """
        Met à jour la route actuelle, exécute le script correspondant et notifie les clients.
        
        Args:
            route: Nouvelle route à définir
        """
        logger.info(f"Demande de changement de route vers: {route}")
        
        # Vérifie si la route est différente de la route actuelle
        if route == self.current_route:
            logger.info(f"Déjà sur la route: {route}")
            return

        # Exécute le script correspondant à la route
        if route in self.route_scripts:
            logger.info(f"Exécution du script pour la route {route}: {self.route_scripts[route]}")
            script_success = await self.execute_script(self.route_scripts[route])
            
            if script_success:
                self.current_route = route
                await self.notify_route()
            else:
                logger.error(f"Échec du changement de route vers {route}")
                # Optionnel : notifier le frontend de l'échec
                await self.notify_error(f"Échec du changement vers {route}")
        else:
            logger.info(f"Pas de script pour la route: {route}")
            self.current_route = route
            await self.notify_route()

    async def notify_route(self) -> None:
        """Envoie la route actuelle à tous les clients."""
        message = {
            "type": "navigation_update",
            "route": self.current_route
        }
        logger.info(f"Envoi de la mise à jour de navigation: {message}")
        await self.websocket_manager.broadcast_to_service(message, "navigation")

    async def notify_error(self, error_message: str) -> None:
        """
        Envoie une notification d'erreur aux clients.
        
        Args:
            error_message: Message d'erreur à envoyer
        """
        message = {
            "type": "navigation_error",
            "error": error_message
        }
        logger.info(f"Envoi de la notification d'erreur: {message}")
        await self.websocket_manager.broadcast_to_service(message, "navigation")

    async def handle_message(self, message: dict) -> None:
        """
        Gère les messages du frontend.
        
        Args:
            message: Message reçu du frontend
        """
        logger.info(f"Message de navigation reçu: {message}")
        message_type = message.get("type")
        data = message.get("data", {})

        try:
            if message_type == "route_change":
                route = data.get("route")
                if route is not None:
                    await self.set_current_route(route)
                else:
                    logger.error("Route manquante dans le message route_change")
            elif message_type == "get_current_route":
                await self.notify_route()
            else:
                logger.warning(f"Type de message non reconnu: {message_type}")
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du message: {e}")
            await self.notify_error("Erreur interne du serveur")