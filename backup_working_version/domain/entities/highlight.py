"""
Entité Highlight - Représente un surlignement Kindle avec support individuel
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass(frozen=True)
class Highlight:
    """
    Entité métier immutable représentant un surlignement extrait individuellement.
    
    Attributes:
        id: Identifiant unique du highlight
        book_id: Identifiant du livre associé
        page_number: Numéro de page dans le livre
        text: Texte extrait du surlignement
        confidence: Score de confiance OCR (0-100)
        extracted_at: Date/heure d'extraction
        position: Position dans la page (x, y, width, height)
        highlight_number: Numéro du surlignement sur la page (1, 2, 3...)
        session_id: Identifiant de la session d'extraction
    """
    id: uuid.UUID
    book_id: uuid.UUID
    page_number: int
    text: str
    confidence: float
    extracted_at: datetime
    position: Optional[tuple[int, int, int, int]] = None
    highlight_number: int = 1  # Nouveau: numéro du surlignement sur la page
    session_id: Optional[str] = None  # Nouveau: pour grouper les extractions
    
    def __post_init__(self):
        """Validation des invariants métier."""
        # Validation de la confiance
        if not 0 <= self.confidence <= 100:
            raise ValueError("Confidence must be between 0 and 100")
        
        # Validation du numéro de page
        if self.page_number < 1:
            raise ValueError("Page number must be positive")
        
        # Validation du texte (mais permet des textes courts pour les surlignements)
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        
        # Validation du numéro de surlignement
        if self.highlight_number < 1:
            raise ValueError("Highlight number must be positive")
    
    @classmethod
    def create(
        cls,
        book_id: uuid.UUID,
        page_number: int,
        text: str,
        confidence: float,
        position: Optional[tuple[int, int, int, int]] = None,
        highlight_number: int = 1,
        session_id: Optional[str] = None
    ) -> "Highlight":
        """Factory method pour créer un nouveau highlight individuel."""
        # Générer un session_id automatique si non fourni
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return cls(
            id=uuid.uuid4(),
            book_id=book_id,
            page_number=page_number,
            text=text.strip(),
            confidence=confidence,
            extracted_at=datetime.now(),
            position=position,
            highlight_number=highlight_number,
            session_id=session_id
        )
    
    @property
    def unique_id(self) -> str:
        """Identifiant unique lisible du surlignement."""
        return f"{self.session_id}_page{self.page_number:03d}_highlight{self.highlight_number:02d}"
    
    @property
    def is_valid(self) -> bool:
        """Vérifie si le surlignement est valide."""
        return (
            len(self.text.strip()) > 0 and 
            self.confidence > 0 and 
            self.page_number > 0 and
            self.highlight_number > 0
        )
    
    @property
    def preview_text(self) -> str:
        """Aperçu du texte (premiers 100 caractères)."""
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."
    
    @property
    def word_count(self) -> int:
        """Nombre de mots dans le surlignement."""
        return len(self.text.split())
    
    @property
    def character_count(self) -> int:
        """Nombre de caractères dans le surlignement."""
        return len(self.text)
    
    @property
    def position_info(self) -> Optional[Dict[str, Any]]:
        """Informations détaillées sur la position."""
        if not self.position:
            return None
        
        x, y, w, h = self.position
        return {
            "x": x,
            "y": y, 
            "width": w,
            "height": h,
            "area": w * h,
            "aspect_ratio": w / h if h > 0 else 0,
            "center_x": x + w // 2,
            "center_y": y + h // 2
        }
    
    @property
    def confidence_level(self) -> str:
        """Niveau de confiance textuel."""
        if self.confidence >= 90:
            return "HIGH"
        elif self.confidence >= 70:
            return "MEDIUM"
        else:
            return "LOW"
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire pour sauvegarde JSON."""
        return {
            "id": str(self.id),
            "unique_id": self.unique_id,
            "book_id": str(self.book_id),
            "page_number": self.page_number,
            "highlight_number": self.highlight_number,
            "text": self.text,
            "confidence": round(self.confidence, 1),
            "confidence_level": self.confidence_level,
            "extracted_at": self.extracted_at.isoformat(),
            "session_id": self.session_id,
            "position": {
                "x": self.position[0],
                "y": self.position[1],
                "width": self.position[2],
                "height": self.position[3]
            } if self.position else None,
            "metrics": {
                "word_count": self.word_count,
                "character_count": self.character_count,
                "preview": self.preview_text
            },
            "position_info": self.position_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Highlight':
        """Création depuis un dictionnaire (pour chargement depuis JSON)."""
        # Reconstruction de la position
        position = None
        if data.get("position"):
            pos = data["position"]
            position = (pos["x"], pos["y"], pos["width"], pos["height"])
        
        return cls(
            id=uuid.UUID(data["id"]),
            book_id=uuid.UUID(data["book_id"]),
            page_number=data["page_number"],
            text=data["text"],
            confidence=data["confidence"],
            extracted_at=datetime.fromisoformat(data["extracted_at"]),
            position=position,
            highlight_number=data.get("highlight_number", 1),
            session_id=data.get("session_id")
        )
    
    def get_display_title(self) -> str:
        """Titre d'affichage pour l'interface."""
        return f"Page {self.page_number} - Surlignement #{self.highlight_number}"
    
    def get_summary(self) -> str:
        """Résumé du surlignement pour les logs."""
        return f"{self.get_display_title()}: '{self.preview_text}' (confiance: {self.confidence:.0f}%, {self.word_count} mots)"
    
    def is_similar_to(self, other: 'Highlight', similarity_threshold: float = 0.8) -> bool:
        """
        Vérifie si ce surlignement est similaire à un autre.
        Utile pour détecter les doublons.
        """
        if not isinstance(other, Highlight):
            return False
        
        # Même page
        if self.page_number != other.page_number:
            return False
        
        # Similarité textuelle simple (ratio de mots communs)
        words_self = set(self.text.lower().split())
        words_other = set(other.text.lower().split())
        
        if not words_self or not words_other:
            return False
        
        common_words = words_self.intersection(words_other)
        total_words = words_self.union(words_other)
        
        similarity = len(common_words) / len(total_words)
        return similarity >= similarity_threshold
    
    def __str__(self) -> str:
        """Représentation textuelle."""
        return f"Highlight(page={self.page_number}, #{self.highlight_number}, confidence={self.confidence:.1f}%, words={self.word_count}, text='{self.preview_text}')"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __lt__(self, other: 'Highlight') -> bool:
        """Comparaison pour tri: d'abord par page, puis par numéro de surlignement."""
        if not isinstance(other, Highlight):
            return NotImplemented
        
        if self.page_number != other.page_number:
            return self.page_number < other.page_number
        
        return self.highlight_number < other.highlight_number