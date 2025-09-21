"""
Port OCREngine - Interface pour l'extraction de texte
"""
from abc import ABC, abstractmethod
from typing import Tuple


class OCREngine(ABC):
    """Interface pour un moteur OCR."""
    
    @abstractmethod
    async def extract_text(self, image: bytes, region: Tuple[int, int, int, int]) -> Tuple[str, float]:
        """
        Extrait le texte d'une région d'image.
        
        Args:
            image: Image en bytes
            region: Tuple (x, y, width, height)
            
        Returns:
            Tuple (texte extrait, score de confiance 0-100)
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Vérifie si le moteur OCR est disponible."""
        pass