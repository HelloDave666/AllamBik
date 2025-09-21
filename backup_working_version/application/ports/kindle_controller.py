"""
Port KindleController - Interface pour contrôler Kindle
"""
from abc import ABC, abstractmethod
from typing import Optional


class KindleController(ABC):
    """Interface pour contrôler l'application Kindle."""
    
    @abstractmethod
    async def navigate_to_page(self, page: int) -> None:
        """
        Navigue vers une page spécifique.
        
        Args:
            page: Numéro de page cible
        """
        pass
    
    @abstractmethod
    async def capture_screen(self) -> bytes:
        """
        Capture l'écran actuel.
        
        Returns:
            Image de l'écran en bytes
        """
        pass
    
    @abstractmethod
    async def get_current_page(self) -> Optional[int]:
        """
        Obtient le numéro de page actuel.
        
        Returns:
            Numéro de page ou None si impossible à déterminer
        """
        pass
    
    @abstractmethod
    async def is_kindle_running(self) -> bool:
        """Vérifie si Kindle est en cours d'exécution."""
        pass