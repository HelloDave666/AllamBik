"""
Port EventBus - Interface pour la communication par événements
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    """Événement de base."""
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus(ABC):
    """Interface pour un bus d'événements."""
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publie un événement.
        
        Args:
            event: L'événement à publier
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """
        S'abonne à un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction à appeler lors de l'événement
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """
        Se désabonne d'un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction à retirer
        """
        pass