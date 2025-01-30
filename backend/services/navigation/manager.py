class NavigationManager:
    def __init__(self, websocket_manager):
        print("Initialisation du NavigationManager...")
        self.websocket_manager = websocket_manager
        self.current_route = "/"  # Route par défaut

    async def set_current_route(self, route):
        """Met à jour la route actuelle et notifie tous les clients"""
        print(f"Changement de route vers: {route}")
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
            await self.set_current_route(data.get("route"))
        elif message_type == "get_current_route":
            await self.notify_route()