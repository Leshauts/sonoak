## backend/services/navigation/manager.py
import asyncio
import os
from pathlib import Path

class NavigationManager:
    def __init__(self, websocket_manager):
        print("Initialisation du NavigationManager...")
        self.websocket_manager = websocket_manager
        self.current_route = "/"
        # Chemin vers le dossier des scripts
        self.scripts_dir = Path(os.path.expanduser("~/sonoak/scripts"))
        print(f"Dossier des scripts configuré: {self.scripts_dir}")
        
        # Mapping des routes vers les scripts
        self.route_scripts = {
            "/bluetooth": "switch-to-bluetooth.sh",
            "/spotify": "switch-to-spotify.sh",
            "/macos": "switch-to-macos.sh"
        }
        print(f"Routes configurées: {self.route_scripts}")

    async def execute_script(self, script_name):
        """Exécute un script shell de manière asynchrone"""
        script_path = self.scripts_dir / script_name
        print(f"Tentative d'exécution du script: {script_path}")
        
        if not script_path.exists():
            print(f"ERREUR: Script {script_path} non trouvé")
            return False

        try:
            print(f"Le script existe, tentative de le rendre exécutable...")
            # Rendre le script exécutable
            os.chmod(script_path, 0o755)
            
            print(f"Exécution du script...")
            # Exécuter le script avec sudo
            process = await asyncio.create_subprocess_exec(
                "sudo",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"Script {script_name} exécuté avec succès")
                print(f"Sortie: {stdout.decode()}")
                return True
            else:
                print(f"ERREUR lors de l'exécution du script {script_name}")
                print(f"Code de retour: {process.returncode}")
                print(f"Erreur: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"EXCEPTION lors de l'exécution du script: {e}")
            return False

    async def set_current_route(self, route):
        """Met à jour la route actuelle, exécute le script correspondant et notifie les clients"""
        print(f"Demande de changement de route vers: {route}")
        
        # Exécuter le script correspondant à la route
        if route in self.route_scripts:
            print(f"Route {route} trouvée, script associé: {self.route_scripts[route]}")
            script_success = await self.execute_script(self.route_scripts[route])
            if script_success:
                self.current_route = route
                await self.notify_route()
            else:
                print(f"ÉCHEC du changement de route vers {route} dû à une erreur de script")
        else:
            print(f"Aucun script trouvé pour la route: {route}")
            self.current_route = route
            await self.notify_route()

    async def notify_route(self):
        """Envoie la route actuelle à tous les clients"""
        message = {
            "type": "navigation_update",
            "route": self.current_route
        }
        print(f"Envoi de la mise à jour de navigation: {message}")
        await self.websocket_manager.broadcast_to_service(message, "navigation")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"Message de navigation reçu: {message}")
        message_type = message.get("type")
        data = message.get("data", {})

        if message_type == "route_change":
            route = data.get("route")
            print(f"Changement de route demandé vers: {route}")
            await self.set_current_route(route)
        elif message_type == "get_current_route":
            print("Demande de route actuelle")
            await self.notify_route()