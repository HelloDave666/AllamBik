"""
ViewModel principal - Logique de prÃ©sentation
"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Tuple
import asyncio
from enum import Enum
import uuid

from src.application.use_cases.extract_highlights_use_case import (
    ExtractHighlightsUseCase,
    ExtractionParams,
    TaskStartedEvent,
    TaskProgressEvent,
    HighlightFoundEvent,
    TaskCompletedEvent,
    TaskCancelledEvent,
    TaskFailedEvent
)
from src.application.ports.event_bus import EventBus
from src.domain.entities.extraction_task import ExtractionTask, TaskStatus
from src.domain.entities.highlight import Highlight


class ViewState(Enum):
    """Ã‰tats possibles de la vue."""
    IDLE = "idle"
    SCANNING = "scanning"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class HighlightViewModel:
    """ModÃ¨le de vue pour un highlight."""
    id: str
    page: int
    text: str
    confidence: float
    
    @classmethod
    def from_domain(cls, highlight: Highlight) -> "HighlightViewModel":
        """CrÃ©e un ViewModel depuis l'entitÃ© domaine."""
        return cls(
            id=str(highlight.id),
            page=highlight.page_number,
            text=highlight.text,
            confidence=highlight.confidence
        )


@dataclass
class MainViewModel:
    """
    ViewModel principal pour l'interface.
    GÃ¨re l'Ã©tat de prÃ©sentation et la communication avec le use case.
    """
    
    # Ã‰tat de l'interface
    state: ViewState = ViewState.IDLE
    can_start: bool = True
    can_stop: bool = False
    can_validate: bool = False
    
    # Progression
    current_progress: float = 0.0
    phase1_progress: float = 0.0
    phase2_progress: float = 0.0
    progress_message: str = ""
    
    # DonnÃ©es
    highlights: List[HighlightViewModel] = field(default_factory=list)
    pages_scanned: int = 0
    pages_with_content: int = 0
    highlights_count: int = 0
    
    # Messages et logs
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # Zone personnalisÃ©e
    custom_scan_zone: Optional[Tuple[int, int, int, int]] = None
    
    # Callbacks pour la vue
    on_state_changed: Optional[Callable] = None
    on_progress_changed: Optional[Callable] = None
    on_highlight_added: Optional[Callable] = None
    on_log_added: Optional[Callable] = None
    
    def __init__(self, extraction_usecase: ExtractHighlightsUseCase, event_bus: EventBus):
        """
        Initialise le ViewModel.
        
        Args:
            extraction_usecase: Use case d'extraction
            event_bus: Bus d'Ã©vÃ©nements pour la communication
        """
        self.usecase = extraction_usecase
        self.event_bus = event_bus
        self._current_task: Optional[asyncio.Task] = None
        self._current_extraction: Optional[ExtractionTask] = None
        
        # S'abonner aux Ã©vÃ©nements
        self._subscribe_to_events()
        
        # Initialiser les champs dataclass
        self.state = ViewState.IDLE
        self.can_start = True
        self.can_stop = False
        self.can_validate = False
        self.current_progress = 0.0
        self.phase1_progress = 0.0
        self.phase2_progress = 0.0
        self.progress_message = ""
        self.highlights = []
        self.pages_scanned = 0
        self.pages_with_content = 0
        self.highlights_count = 0
        self.logs = []
        self.error_message = None
        self.custom_scan_zone = None
        self.on_state_changed = None
        self.on_progress_changed = None
        self.on_highlight_added = None
        self.on_log_added = None
        self.page_detector = None  # Sera assigné par app.py
        self.detected_pages = None  # Nombre de pages détectées
        self.is_detecting = False  # État de la détection
        
        self.add_log("Alambik v3.0 - PrÃªt pour l'extraction")
    
    def _subscribe_to_events(self):
        """S'abonne aux Ã©vÃ©nements du domaine."""
        self.event_bus.subscribe(TaskStartedEvent, self._on_task_started)
        self.event_bus.subscribe(TaskProgressEvent, self._on_task_progress)
        self.event_bus.subscribe(HighlightFoundEvent, self._on_highlight_found)
        self.event_bus.subscribe(TaskCompletedEvent, self._on_task_completed)
        self.event_bus.subscribe(TaskCancelledEvent, self._on_task_cancelled)
        self.event_bus.subscribe(TaskFailedEvent, self._on_task_failed)
    
    # Commandes (actions dÃ©clenchÃ©es par la vue)
    
    async def start_extraction_command(self, total_pages: int = 200):
        """
        Commande: DÃ©marrer l'extraction.
        
        Args:
            total_pages: Nombre total de pages du livre
        """
        if not self.can_start:
            return
        
        self.add_log("DÃ©marrage de l'extraction...")
        self._reset_state()
        self._update_state(ViewState.SCANNING)
        
        # Zones de scan par dÃ©faut
        scan_regions = [(50, 100, 1600, 980)]  # Zone par dÃ©faut
        
        # Utiliser la zone personnalisÃ©e si dÃ©finie
        if self.custom_scan_zone:
            scan_regions = [self.custom_scan_zone]
            x, y, w, h = self.custom_scan_zone
            self.add_log(f"Utilisation de la zone personnalisÃ©e: {w}x{h} Ã  ({x},{y})")
        else:
            self.add_log("Utilisation de la zone de scan par dÃ©faut")
        
        # ParamÃ¨tres d'extraction
        params = ExtractionParams(
            total_pages=total_pages,
            start_page=1,
            end_page=total_pages,
            scan_regions=scan_regions,
            min_text_length=10,
            min_confidence=60.0,  # RÃ©duit pour dÃ©tecter plus de texte
            navigation_delay=0.3,
            ocr_delay=1.5  # AugmentÃ© pour laisser le temps Ã  l'OCR
        )
        
        # Lancer l'extraction de maniÃ¨re asynchrone
        self._current_task = asyncio.create_task(
            self.usecase.execute(params)
        )
    
    async def stop_extraction_command(self):
        """Commande: ArrÃªter l'extraction."""
        if not self.can_stop:
            return
        
        self.add_log("ArrÃªt demandÃ©...")
        await self.usecase.cancel()
        
        self.can_stop = False
        self.progress_message = "ArrÃªt en cours..."
    
    async def validate_phase1_command(self):
        """Commande: Valider la phase 1 et passer Ã  l'extraction."""
        if not self.can_validate:
            return
        
        self.add_log("Phase 1 validÃ©e - Passage Ã  l'extraction OCR")
        self.can_validate = False
        # La phase 2 se lance automatiquement dans notre architecture
    
    # Handlers d'Ã©vÃ©nements
    
    async def _on_task_started(self, event: TaskStartedEvent):
        """GÃ¨re l'Ã©vÃ©nement de dÃ©marrage."""
        self._current_extraction = event.task
        self.add_log("Scan des pages dÃ©marrÃ©")
        self.can_start = False
        self.can_stop = True
    
    async def _on_task_progress(self, event: TaskProgressEvent):
        """GÃ¨re les mises Ã  jour de progression."""
        self.progress_message = event.message
        
        # DÃ©terminer la phase en cours
        if self._current_extraction:
            if self._current_extraction.status == TaskStatus.SCANNING:
                self.phase1_progress = event.progress * 2  # Phase 1 = 0-50%
                self.current_progress = event.progress
            elif self._current_extraction.status == TaskStatus.EXTRACTING:
                self.phase1_progress = 100
                self.phase2_progress = (event.progress - 50) * 2  # Phase 2 = 50-100%
                self.current_progress = event.progress
                self._update_state(ViewState.EXTRACTING)
        
        if self.on_progress_changed:
            self.on_progress_changed()
    
    async def _on_highlight_found(self, event: HighlightFoundEvent):
        """GÃ¨re la dÃ©couverte d'un highlight."""
        highlight_vm = HighlightViewModel.from_domain(event.highlight)
        self.highlights.append(highlight_vm)
        self.highlights_count = len(self.highlights)
        
        self.add_log(f"Highlight trouvÃ© page {highlight_vm.page} ({highlight_vm.confidence:.0f}%)")
        
        if self.on_highlight_added:
            self.on_highlight_added(highlight_vm)
    
    async def _on_task_completed(self, event: TaskCompletedEvent):
        """GÃ¨re la fin de l'extraction."""
        self._update_state(ViewState.COMPLETED)
        self.can_stop = False
        self.can_start = True
        
        # Mettre Ã  jour les statistiques finales
        task = event.task
        self.pages_scanned = task.pages_scanned
        self.pages_with_content = task.pages_with_content
        self.highlights_count = len(task.highlights_extracted)
        
        self.add_log(f"Extraction terminÃ©e - {self.highlights_count} highlights extraits")
        self.progress_message = "Extraction terminÃ©e avec succÃ¨s"
        
        # Fin de phase 1 -> activer validation
        if task.status == TaskStatus.SCANNING and task.pages_with_content > 0:
            self.can_validate = True
            self.add_log("Phase 1 terminÃ©e - Validation disponible")
    
    async def _on_task_cancelled(self, event: TaskCancelledEvent):
        """GÃ¨re l'annulation."""
        self._update_state(ViewState.IDLE)
        self.can_stop = False
        self.can_start = True
        self.add_log("Extraction annulÃ©e")
        self.progress_message = "Extraction annulÃ©e"
    
    async def _on_task_failed(self, event: TaskFailedEvent):
        """GÃ¨re les erreurs."""
        self._update_state(ViewState.ERROR)
        self.can_stop = False
        self.can_start = True
        self.error_message = str(event.error)
        self.add_log(f"ERREUR: {event.error}")
        self.progress_message = "Erreur pendant l'extraction"
    
    # MÃ©thodes utilitaires
    
    def add_log(self, message: str):
        """Ajoute un message de log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        if self.on_log_added:
            self.on_log_added(log_entry)
    
    def _update_state(self, new_state: ViewState):
        """Met Ã  jour l'Ã©tat de la vue."""
        self.state = new_state
        
        # Mettre Ã  jour les permissions selon l'Ã©tat
        if new_state == ViewState.IDLE:
            self.can_start = True
            self.can_stop = False
        elif new_state in [ViewState.SCANNING, ViewState.EXTRACTING]:
            self.can_start = False
            self.can_stop = True
        elif new_state == ViewState.COMPLETED:
            self.can_start = True
            self.can_stop = False
        elif new_state == ViewState.ERROR:
            self.can_start = True
            self.can_stop = False
        
        if self.on_state_changed:
            self.on_state_changed(new_state)
    
    
    async def detect_pages_command(self):
        """Commande pour détecter automatiquement le nombre de pages."""
        if not self.page_detector or self.is_detecting:
            return
        
        self.is_detecting = True
        self.add_log("Détection automatique du nombre de pages en cours...")
        self.progress_message = "Détection des pages..."
        
        try:
            # Callback pour la progression
            async def progress_callback(page, message):
                self.progress_message = message
                if self.on_progress_changed:
                    self.on_progress_changed()
            
            # Lancer la détection
            total_pages = await self.page_detector.detect_total_pages(progress_callback)
            self.detected_pages = total_pages
            
            self.add_log(f"Détection terminée: {total_pages} pages trouvées")
            self.progress_message = f"{total_pages} pages détectées - Prêt pour l'extraction"
            
        except Exception as e:
            self.add_log(f"Erreur lors de la détection: {e}")
            self.progress_message = "Erreur de détection"
        finally:
            self.is_detecting = False
            if self.on_state_changed:
                self.on_state_changed(self.state)

    def _reset_state(self):
        """RÃ©initialise l'Ã©tat."""
        self.highlights.clear()
        self.pages_scanned = 0
        self.pages_with_content = 0
        self.highlights_count = 0
        self.current_progress = 0
        self.phase1_progress = 0
        self.phase2_progress = 0
        self.error_message = None
        self.can_validate = False
