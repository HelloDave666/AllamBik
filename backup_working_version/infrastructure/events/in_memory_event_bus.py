"""
Event Bus en mémoire - Implémentation simple
"""
import asyncio
from typing import Dict, List, Callable, Type
from collections import defaultdict
import logging

from src.application.ports.event_bus import EventBus, Event

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Event bus simple en mémoire."""
    
    def __init__(self):
        """Initialise le bus d'événements."""
        self._handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def publish(self, event: Event) -> None:
        """
        Publie un événement à tous les handlers.
        
        Args:
            event: L'événement à publier
        """
        event_type = type(event)
        
        async with self._lock:
            handlers = self._handlers[event_type].copy()
        
        logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handlers")
        
        # Exécuter tous les handlers
        tasks = []
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                task = asyncio.create_task(handler(event))
            else:
                # Wrapper pour les handlers synchrones
                task = asyncio.create_task(
                    asyncio.get_event_loop().run_in_executor(
                        None, handler, event
                    )
                )
            tasks.append(task)
        
        # Attendre que tous les handlers soient exécutés
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """
        S'abonne à un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction à appeler
        """
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.__name__}")
    
    def unsubscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """
        Se désabonne d'un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction à retirer
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler unsubscribed from {event_type.__name__}")