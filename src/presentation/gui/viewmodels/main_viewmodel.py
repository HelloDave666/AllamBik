"""
ViewModel principal - Logique de présentation
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
    """États possibles de la vue."""
    IDLE = "idle"
    SCANNING = "scanning"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class HighlightViewModel:
    """Modèle de vue pour un highlight."""
    id: str
    page: int
    text: str
    confidence: float
    
    @classmethod
    def from_domain(cls, highlight: Highlight) -> "HighlightViewModel":
        """Crée un ViewModel depuis l'entité domaine."""
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
    Gère l'état de présentation et la communication avec le use case.
    """
    
    # État de l'interface
    state: ViewState = ViewState.IDLE
    can_start: bool = True
    can_stop: bool = False
    can_validate: bool = False
    
    # Progression
    current_progress: float = 0.0
    phase1_progress: float = 0.0
    phase2_progress: float = 0.0
    progress_message: str = ""
    
    # Données
    highlights: List[HighlightViewModel] = field(default_factory=list)
    pages_scanned: int = 0
    pages_with_content: int = 0
    highlights_count: int = 0
    
    # Messages et logs
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # Zone personnalisée
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
            event_bus: Bus d'événements pour la communication
        """
        self.usecase = extraction_usecase
        self.event_bus = event_bus
        self._current_task: Optional[asyncio.Task] = None
        self._current_extraction: Optional[ExtractionTask] = None
        
        # S'abonner aux événements
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
        
        self.add_log("Alambik v3.0 - Prêt pour l'extraction")
    
    def _subscribe_to_events(self):
        """S'abonne aux événements du domaine."""
        self.event_bus.subscribe(TaskStartedEvent, self._on_task_started)
        self.event_bus.subscribe(TaskProgressEvent, self._on_task_progress)
        self.event_bus.subscribe(HighlightFoundEvent, self._on_highlight_found)
        self.event_bus.subscribe(TaskCompletedEvent, self._on_task_completed)
        self.event_bus.subscribe(TaskCancelledEvent, self._on_task_cancelled)
        self.event_bus.subscribe(TaskFailedEvent, self._on_task_failed)
    
    # Commandes (actions déclenchées par la vue)
    
    async def start_extraction_command(self, total_pages: int = 200):
        """
        Commande: Démarrer l'extraction.
        
        Args:
            total_pages: Nombre total de pages du livre
        """
        if not self.can_start:
            return
        
        self.add_log("Démarrage de l'extraction...")
        self._reset_state()
        self._update_state(ViewState.SCANNING)
        
        # Zones de scan par défaut
        scan_regions = [(50, 100, 1600, 980)]  # Zone par défaut
        
        # Utiliser la zone personnalisée si définie
        if self.custom_scan_zone:
            scan_regions = [self.custom_scan_zone]
            x, y, w, h = self.custom_scan_zone
            self.add_log(f"Utilisation de la zone personnalisée: {w}x{h} à ({x},{y})")
        else:
            self.add_log("Utilisation de la zone de scan par défaut")
        
        # Paramètres d'extraction
        params = ExtractionParams(
            total_pages=total_pages,
            start_page=1,
            end_page=total_pages,
            scan_regions=scan_regions,
            min_text_length=10,
            min_confidence=60.0,  # Réduit pour détecter plus de texte
            navigation_delay=0.3,
            ocr_delay=1.5  # Augmenté pour laisser le temps à l'OCR
        )
        
        # Lancer l'extraction de manière asynchrone
        self._current_task = asyncio.create_task(
            self.usecase.execute(params)
        )
    
    async def stop_extraction_command(self):
        """Commande: Arrêter l'extraction."""
        if not self.can_stop:
            return
        
        self.add_log("Arrêt demandé...")
        await self.usecase.cancel()
        
        self.can_stop = False
        self.progress_message = "Arrêt en cours..."
    
    async def validate_phase1_command(self):
        """Commande: Valider la phase 1 et passer à l'extraction."""
        if not self.can_validate:
            return
        
        self.add_log("Phase 1 validée - Passage à l'extraction OCR")
        self.can_validate = False
        # La phase 2 se lance automatiquement dans notre architecture
    
    # Handlers d'événements
    
    async def _on_task_started(self, event: TaskStartedEvent):
        """Gère l'événement de démarrage."""
        self._current_extraction = event.task
        self.add_log("Scan des pages démarré")
        self.can_start = False
        self.can_stop = True
    
    async def _on_task_progress(self, event: TaskProgressEvent):
        """Gère les mises à jour de progression."""
        self.progress_message = event.message
        
        # Déterminer la phase en cours
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
        """Gère la découverte d'un highlight."""
        highlight_vm = HighlightViewModel.from_domain(event.highlight)
        self.highlights.append(highlight_vm)
        self.highlights_count = len(self.highlights)
        
        self.add_log(f"Highlight trouvé page {highlight_vm.page} ({highlight_vm.confidence:.0f}%)")
        
        if self.on_highlight_added:
            self.on_highlight_added(highlight_vm)
    
    async def _on_task_completed(self, event: TaskCompletedEvent):
        """Gère la fin de l'extraction."""
        self._update_state(ViewState.COMPLETED)
        self.can_stop = False
        self.can_start = True
        
        # Mettre à jour les statistiques finales
        task = event.task
        self.pages_scanned = task.pages_scanned
        self.pages_with_content = task.pages_with_content
        self.highlights_count = len(task.highlights_extracted)
        
        self.add_log(f"Extraction terminée - {self.highlights_count} highlights extraits")
        self.progress_message = "Extraction terminée avec succès"
        
        # Fin de phase 1 -> activer validation
        if task.status == TaskStatus.SCANNING and task.pages_with_content > 0:
            self.can_validate = True
            self.add_log("Phase 1 terminée - Validation disponible")
    
    async def _on_task_cancelled(self, event: TaskCancelledEvent):
        """Gère l'annulation."""
        self._update_state(ViewState.IDLE)
        self.can_stop = False
        self.can_start = True
        self.add_log("Extraction annulée")
        self.progress_message = "Extraction annulée"
    
    async def _on_task_failed(self, event: TaskFailedEvent):
        """Gère les erreurs."""
        self._update_state(ViewState.ERROR)
        self.can_stop = False
        self.can_start = True
        self.error_message = str(event.error)
        self.add_log(f"ERREUR: {event.error}")
        self.progress_message = "Erreur pendant l'extraction"
    
    # Méthodes utilitaires
    
    def add_log(self, message: str):
        """Ajoute un message de log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        if self.on_log_added:
            self.on_log_added(log_entry)
    
    def _update_state(self, new_state: ViewState):
        """Met à jour l'état de la vue."""
        self.state = new_state
        
        # Mettre à jour les permissions selon l'état
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
    
    def _reset_state(self):
        """Réinitialise l'état."""
        self.highlights.clear()
        self.pages_scanned = 0
        self.pages_with_content = 0
        self.highlights_count = 0
        self.current_progress = 0
        self.phase1_progress = 0
        self.phase2_progress = 0
        self.error_message = None
        self.can_validate = False