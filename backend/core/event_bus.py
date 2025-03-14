# backend/core/event_bus.py
import asyncio
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    Bus d'événements simple pour permettre la communication entre plugins.
    """
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type, callback):
        """
        S'abonne à un type d'événement.
        
        Args:
            event_type (str): Type d'événement à écouter
            callback (callable): Fonction à appeler quand l'événement est publié
        
        Returns:
            callable: Fonction pour se désabonner
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        
        # Retourner une fonction pour se désabonner
        def unsubscribe():
            if event_type in self.subscribers and callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
        
        return unsubscribe
        
    async def publish(self, event_type, data=None):
        """
        Publie un événement à tous les abonnés.
        
        Args:
            event_type (str): Type d'événement à publier
            data (Any, optional): Données associées à l'événement
        """
        if event_type not in self.subscribers:
            return
            
        logger.debug(f"Publication événement {event_type} avec données: {data}")
        
        for callback in self.subscribers[event_type]:
            try:
                result = callback(data)
                # Si le callback est une coroutine, on l'attend
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Erreur dans callback pour {event_type}: {e}")