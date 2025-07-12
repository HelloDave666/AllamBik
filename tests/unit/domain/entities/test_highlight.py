"""
Tests unitaires pour l'entité Highlight
"""
import uuid
from datetime import datetime
import pytest

from src.domain.entities.highlight import Highlight


class TestHighlight:
    """Tests pour l'entité Highlight."""
    
    def test_create_valid_highlight(self):
        """Test de création d'un highlight valide."""
        book_id = uuid.uuid4()
        
        highlight = Highlight.create(
            book_id=book_id,
            page_number=42,
            text="  Ceci est un texte surligné  ",
            confidence=95.5,
            position=(100, 200, 300, 50)
        )
        
        assert highlight.id is not None
        assert highlight.book_id == book_id
        assert highlight.page_number == 42
        assert highlight.text == "Ceci est un texte surligné"  # Trimmed
        assert highlight.confidence == 95.5
        assert highlight.position == (100, 200, 300, 50)
        assert isinstance(highlight.extracted_at, datetime)
    
    def test_highlight_immutability(self):
        """Test que le highlight est immutable."""
        highlight = Highlight.create(
            book_id=uuid.uuid4(),
            page_number=1,
            text="Test",
            confidence=90.0
        )
        
        with pytest.raises(AttributeError):
            highlight.text = "Modified"
    
    def test_invalid_confidence_too_high(self):
        """Test avec une confiance trop élevée."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 100"):
            Highlight.create(
                book_id=uuid.uuid4(),
                page_number=1,
                text="Test",
                confidence=101.0
            )
    
    def test_invalid_confidence_negative(self):
        """Test avec une confiance négative."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 100"):
            Highlight.create(
                book_id=uuid.uuid4(),
                page_number=1,
                text="Test",
                confidence=-1.0
            )
    
    def test_invalid_page_number(self):
        """Test avec un numéro de page invalide."""
        with pytest.raises(ValueError, match="Page number must be positive"):
            Highlight.create(
                book_id=uuid.uuid4(),
                page_number=0,
                text="Test",
                confidence=90.0
            )
    
    def test_empty_text(self):
        """Test avec un texte vide."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            Highlight.create(
                book_id=uuid.uuid4(),
                page_number=1,
                text="   ",  # Only whitespace
                confidence=90.0
            )
    
    def test_highlight_without_position(self):
        """Test création sans position."""
        highlight = Highlight.create(
            book_id=uuid.uuid4(),
            page_number=1,
            text="Test",
            confidence=90.0
            # position omitted
        )
        
        assert highlight.position is None