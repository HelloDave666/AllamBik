"""
Entité ExtractionTask - Représente une tâche d'extraction
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .highlight import Highlight


class TaskStatus(Enum):
    """États possibles d'une tâche d'extraction."""
    CREATED = auto()
    SCANNING = auto()
    EXTRACTING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()


@dataclass
class ExtractionTask:
    """
    Tâche d'extraction avec gestion d'état.
    
    Attributes:
        id: Identifiant unique de la tâche
        book_id: Identifiant du livre à extraire
        status: État actuel de la tâche
        progress: Progression en pourcentage (0-100)
        pages_scanned: Nombre de pages scannées
        pages_with_content: Pages contenant des surlignements
        highlights_extracted: Liste des highlights extraits
        created_at: Date de création
        started_at: Date de début d'exécution
        completed_at: Date de fin
        error: Message d'erreur si échec
        metadata: Données additionnelles
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    book_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: TaskStatus = TaskStatus.CREATED
    progress: float = 0.0
    pages_scanned: int = 0
    pages_with_content: int = 0
    highlights_extracted: List[Highlight] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation des invariants."""
        if not 0 <= self.progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
    
    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """
        Vérifie si la transition vers un nouvel état est valide.
        
        Args:
            new_status: Le nouvel état souhaité
            
        Returns:
            True si la transition est autorisée
        """
        valid_transitions = {
            TaskStatus.CREATED: [TaskStatus.SCANNING, TaskStatus.CANCELLED, TaskStatus.FAILED],  # FAILED ajouté ici
            TaskStatus.SCANNING: [
                TaskStatus.EXTRACTING, 
                TaskStatus.PAUSED, 
                TaskStatus.CANCELLED, 
                TaskStatus.FAILED
            ],
            TaskStatus.EXTRACTING: [
                TaskStatus.COMPLETED, 
                TaskStatus.PAUSED, 
                TaskStatus.CANCELLED, 
                TaskStatus.FAILED
            ],
            TaskStatus.PAUSED: [
                TaskStatus.SCANNING, 
                TaskStatus.EXTRACTING, 
                TaskStatus.CANCELLED
            ],
            TaskStatus.COMPLETED: [],
            TaskStatus.CANCELLED: [],
            TaskStatus.FAILED: []
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status: TaskStatus) -> None:
        """
        Effectue la transition vers un nouvel état.
        
        Args:
            new_status: Le nouvel état
            
        Raises:
            ValueError: Si la transition n'est pas autorisée
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status.name} to {new_status.name}"
            )
        
        self.status = new_status
        
        # Actions spécifiques selon les transitions
        if new_status == TaskStatus.SCANNING and not self.started_at:
            self.started_at = datetime.now()
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
            self.completed_at = datetime.now()
    
    def add_highlight(self, highlight: Highlight) -> None:
        """Ajoute un highlight extrait."""
        self.highlights_extracted.append(highlight)
    
    def update_progress(self, scanned: int, total: int) -> None:
        """Met à jour la progression."""
        if total > 0:
            self.progress = (scanned / total) * 100
            self.progress = min(100, max(0, self.progress))
    
    @property
    def duration(self) -> Optional[float]:
        """Durée d'exécution en secondes."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_running(self) -> bool:
        """Indique si la tâche est en cours."""
        return self.status in [TaskStatus.SCANNING, TaskStatus.EXTRACTING]
    
    @property
    def is_finished(self) -> bool:
        """Indique si la tâche est terminée."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]