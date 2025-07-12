"""
Test d'intégration pour vérifier que l'architecture fonctionne
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.application.use_cases.extract_highlights_use_case import (
    ExtractHighlightsUseCase,
    ExtractionParams,
    TaskStartedEvent,
    TaskCompletedEvent,
    HighlightFoundEvent
)
from src.application.ports.ocr_engine import OCREngine
from src.application.ports.kindle_controller import KindleController
from src.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from src.domain.entities.extraction_task import TaskStatus


# Mock implementations pour les tests
class MockOCREngine(OCREngine):
    """Mock OCR pour les tests."""
    
    async def extract_text(self, image: bytes, region: tuple[int, int, int, int]) -> tuple[str, float]:
        # Simuler l'extraction avec des données de test
        return "Texte de test extrait", 95.0
    
    async def is_available(self) -> bool:
        return True


class MockKindleController(KindleController):
    """Mock Kindle controller pour les tests."""
    
    def __init__(self):
        self.current_page = 0
    
    async def navigate_to_page(self, page: int) -> None:
        self.current_page = page
        await asyncio.sleep(0.01)  # Simuler un délai
    
    async def capture_screen(self) -> bytes:
        # Retourner des données d'image fictives
        return b"fake_image_data"
    
    async def get_current_page(self) -> int:
        return self.current_page
    
    async def is_kindle_running(self) -> bool:
        return True


@pytest.mark.asyncio
class TestUseCaseIntegration:
    """Tests d'intégration pour le use case principal."""
    
    async def test_complete_extraction_workflow(self):
        """Test du workflow complet d'extraction."""
        # Setup
        ocr_engine = MockOCREngine()
        kindle_controller = MockKindleController()
        event_bus = InMemoryEventBus()
        
        use_case = ExtractHighlightsUseCase(
            ocr_engine=ocr_engine,
            kindle_controller=kindle_controller,
            event_bus=event_bus
        )
        
        # Tracking des événements
        events_received = []
        
        async def event_handler(event):
            events_received.append(event)
        
        # S'abonner aux événements
        event_bus.subscribe(TaskStartedEvent, event_handler)
        event_bus.subscribe(TaskCompletedEvent, event_handler)
        event_bus.subscribe(HighlightFoundEvent, event_handler)
        
        # Paramètres de test
        params = ExtractionParams(
            total_pages=5,
            start_page=1,
            end_page=5,
            navigation_delay=0.01,
            ocr_delay=0.01
        )
        
        # Exécuter
        task = await use_case.execute(params)
        
        # Vérifications
        assert task.status == TaskStatus.COMPLETED
        assert task.pages_scanned == 5
        assert task.pages_with_content > 0
        assert len(task.highlights_extracted) > 0
        
        # Vérifier les événements
        assert any(isinstance(e, TaskStartedEvent) for e in events_received)
        assert any(isinstance(e, TaskCompletedEvent) for e in events_received)
        assert any(isinstance(e, HighlightFoundEvent) for e in events_received)
    
    async def test_extraction_cancellation(self):
        """Test de l'annulation d'extraction."""
        # Setup
        ocr_engine = MockOCREngine()
        kindle_controller = MockKindleController()
        event_bus = InMemoryEventBus()
        
        use_case = ExtractHighlightsUseCase(
            ocr_engine=ocr_engine,
            kindle_controller=kindle_controller,
            event_bus=event_bus
        )
        
        # Paramètres avec beaucoup de pages
        params = ExtractionParams(
            total_pages=100,
            navigation_delay=0.1  # Délai plus long
        )
        
        # Démarrer l'extraction
        extraction_task = asyncio.create_task(use_case.execute(params))
        
        # Attendre un peu puis annuler
        await asyncio.sleep(0.2)
        await use_case.cancel()
        
        # Attendre la fin
        task = await extraction_task
        
        # Vérifications
        assert task.status == TaskStatus.CANCELLED
        assert task.pages_scanned < 100  # Pas toutes les pages scannées
    
    async def test_extraction_with_no_kindle(self):
        """Test quand Kindle n'est pas disponible."""
        # Setup avec Kindle non disponible
        ocr_engine = MockOCREngine()
        kindle_controller = MockKindleController()
        kindle_controller.is_kindle_running = AsyncMock(return_value=False)
        event_bus = InMemoryEventBus()
        
        use_case = ExtractHighlightsUseCase(
            ocr_engine=ocr_engine,
            kindle_controller=kindle_controller,
            event_bus=event_bus
        )
        
        params = ExtractionParams(total_pages=5)
        
        # Exécuter et vérifier l'exception
        with pytest.raises(RuntimeError, match="Kindle application not running"):
            await use_case.execute(params)