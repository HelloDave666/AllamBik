"""
Use Case principal - Extraction des highlights avec traitement individuel
"""
import asyncio
from typing import List, Optional, AsyncIterator
from dataclasses import dataclass
import uuid
from datetime import datetime
import logging

from src.domain.entities.highlight import Highlight
from src.domain.entities.extraction_task import ExtractionTask, TaskStatus
from src.application.ports.ocr_engine import OCREngine
from src.application.ports.kindle_controller import KindleController
from src.application.ports.event_bus import EventBus, Event

logger = logging.getLogger(__name__)


# Événements du domaine
@dataclass
class TaskStartedEvent(Event):
    """Événement: tâche démarrée."""
    task: ExtractionTask = None


@dataclass
class TaskProgressEvent(Event):
    """Événement: progression mise à jour."""
    task_id: uuid.UUID = None
    progress: float = 0.0
    message: str = ""


@dataclass
class HighlightFoundEvent(Event):
    """Événement: highlight trouvé."""
    task_id: uuid.UUID = None
    highlight: Highlight = None


@dataclass
class TaskCompletedEvent(Event):
    """Événement: tâche terminée."""
    task: ExtractionTask = None


@dataclass
class TaskCancelledEvent(Event):
    """Événement: tâche annulée."""
    task: ExtractionTask = None


@dataclass
class TaskFailedEvent(Event):
    """Événement: tâche échouée."""
    task: ExtractionTask = None
    error: Exception = None


# Paramètres d'extraction
@dataclass
class ExtractionParams:
    """Paramètres pour l'extraction."""
    total_pages: int
    start_page: int = 1
    end_page: Optional[int] = None
    
    # Zones à analyser (x, y, width, height)
    scan_regions: List[tuple[int, int, int, int]] = None
    
    # Paramètres de filtrage pour surlignements individuels
    min_text_length: int = 3  # Réduit pour accepter des surlignements courts
    min_confidence: float = 30.0  # Réduit pour la détection de surlignements
    
    # Paramètres de navigation
    navigation_delay: float = 0.3
    ocr_delay: float = 1.0
    
    def __post_init__(self):
        if self.end_page is None:
            self.end_page = self.total_pages
        
        if self.scan_regions is None:
            # Zone par défaut Kindle (à ajuster selon vos paramètres)
            self.scan_regions = [(50, 100, 1600, 980)]


class ExtractHighlightsUseCase:
    """
    Use case principal pour l'extraction des highlights avec traitement individuel.
    Orchestrateur de la logique métier.
    """
    
    def __init__(
        self,
        ocr_engine: OCREngine,
        kindle_controller: KindleController,
        event_bus: EventBus,
        highlight_repository=None  # Repository pour sauvegarder
    ):
        self.ocr = ocr_engine
        self.kindle = kindle_controller
        self.events = event_bus
        self.repository = highlight_repository  # Stocker le repository
        self._cancellation_token: Optional[asyncio.Event] = None
    
    async def execute(self, params: ExtractionParams) -> ExtractionTask:
        """
        Exécute l'extraction complète avec traitement individuel des surlignements.
        
        Args:
            params: Paramètres d'extraction
            
        Returns:
            ExtractionTask avec les résultats individuels
        """
        # Créer la tâche
        task = ExtractionTask()
        self._cancellation_token = asyncio.Event()
        
        try:
            # Vérifications préliminaires
            await self._validate_prerequisites()
            
            # Démarrer la tâche
            task.transition_to(TaskStatus.SCANNING)
            await self.events.publish(TaskStartedEvent(task=task))
            
            # Phase 1: Scan pour identifier les pages avec contenu
            pages_with_content = await self._scan_phase(task, params)
            
            if self._cancellation_token.is_set():
                task.transition_to(TaskStatus.CANCELLED)
                await self.events.publish(TaskCancelledEvent(task=task))
                return task
            
            # Phase 2: Extraction OCR avec traitement individuel sur les pages identifiées
            if pages_with_content:  # Seulement si on a trouvé du contenu
                task.transition_to(TaskStatus.EXTRACTING)
                await self._extraction_phase_individual(task, params, pages_with_content)
            else:
                logger.warning("Aucune page avec contenu trouvée")
            
            # Finalisation
            if self._cancellation_token.is_set():
                task.transition_to(TaskStatus.CANCELLED)
                await self.events.publish(TaskCancelledEvent(task=task))
            else:
                task.transition_to(TaskStatus.COMPLETED)
                await self.events.publish(TaskCompletedEvent(task=task))
            
            # SAUVEGARDE DES RÉSULTATS INDIVIDUELS
            if self.repository and task.highlights_extracted:
                try:
                    await self.repository.save_task(task)
                    logger.info(f"✓ Résultats sauvegardés - {len(task.highlights_extracted)} highlights individuels")
                    await self.events.publish(TaskProgressEvent(
                        task_id=task.id,
                        progress=100,
                        message=f"Résultats sauvegardés: {len(task.highlights_extracted)} surlignements dans le dossier 'extractions'"
                    ))
                except Exception as e:
                    logger.error(f"Échec de la sauvegarde: {e}")
            
        except Exception as e:
            task.error = str(e)
            task.transition_to(TaskStatus.FAILED)
            await self.events.publish(TaskFailedEvent(task=task, error=e))
            raise
        
        return task
    
    async def cancel(self) -> None:
        """Annule l'extraction en cours."""
        if self._cancellation_token:
            self._cancellation_token.set()
    
    async def _validate_prerequisites(self) -> None:
        """Valide que tout est prêt pour l'extraction."""
        if not await self.ocr.is_available():
            raise RuntimeError("OCR engine not available")
        
        if not await self.kindle.is_kindle_running():
            raise RuntimeError("Kindle application not running")
    
    async def _scan_phase(
        self, 
        task: ExtractionTask, 
        params: ExtractionParams
    ) -> List[int]:
        """
        Phase 1: Scan rapide pour identifier les pages avec surlignements.
        
        Returns:
            Liste des numéros de pages contenant des highlights
        """
        pages_with_content = []
        
        logger.info(f"=== PHASE 1: SCAN DES PAGES {params.start_page} à {params.end_page} ===")
        
        for page_num in range(params.start_page, params.end_page + 1):
            # Vérifier l'annulation
            if self._cancellation_token.is_set():
                break
            
            logger.info(f"--- Scan page {page_num} ---")
            
            # Navigation
            await self.kindle.navigate_to_page(page_num)
            await asyncio.sleep(params.navigation_delay)
            
            # Capture
            screen_data = await self.kindle.capture_screen()
            
            # Analyse rapide pour détecter des surlignements
            has_highlights = await self._quick_highlight_check(screen_data, params)
            
            if has_highlights:
                pages_with_content.append(page_num)
                task.pages_with_content += 1
                logger.info(f"✓ Page {page_num} contient des surlignements")
            else:
                logger.info(f"✗ Page {page_num} est vide")
            
            # Mise à jour progression
            task.pages_scanned += 1
            task.update_progress(task.pages_scanned, params.total_pages)
            
            await self.events.publish(TaskProgressEvent(
                task_id=task.id,
                progress=task.progress * 0.5,  # Phase 1 = 50% du total
                message=f"Scan page {page_num}/{params.end_page}"
            ))
        
        logger.info(f"=== FIN PHASE 1: {len(pages_with_content)} pages avec contenu ===")
        return pages_with_content
    
    async def _extraction_phase_individual(
        self,
        task: ExtractionTask,
        params: ExtractionParams,
        pages_with_content: List[int]
    ) -> None:
        """
        Phase 2: Extraction OCR avec traitement individuel des surlignements.
        """
        total_pages = len(pages_with_content)
        logger.info(f"=== PHASE 2: EXTRACTION INDIVIDUELLE sur {total_pages} pages ===")
        
        for idx, page_num in enumerate(pages_with_content):
            # Vérifier l'annulation
            if self._cancellation_token.is_set():
                break
            
            logger.info(f"--- Extraction page {page_num} ({idx+1}/{total_pages}) ---")
            
            # Navigation
            await self.kindle.navigate_to_page(page_num)
            await asyncio.sleep(params.ocr_delay)
            
            # Capture
            screen_data = await self.kindle.capture_screen()
            
            # Extraction des surlignements individuels sur toutes les régions
            page_highlights_count = 0
            for region_idx, region in enumerate(params.scan_regions):
                
                # NOUVELLE MÉTHODE: Extraction individuelle des surlignements
                if hasattr(self.ocr, 'extract_highlights'):
                    # Utiliser la nouvelle méthode qui retourne une liste de surlignements
                    highlight_results = await self.ocr.extract_highlights(screen_data, region)
                    
                    logger.info(f"  Région {region_idx + 1}: {len(highlight_results)} surlignement(s) détecté(s)")
                    
                    # Traiter chaque surlignement individuellement
                    for highlight_result in highlight_results:
                        if self._is_valid_highlight_result(highlight_result, params):
                            # Créer un objet Highlight pour chaque surlignement individuel
                            highlight = Highlight.create(
                                book_id=task.book_id,
                                page_number=page_num,
                                text=highlight_result.text,
                                confidence=highlight_result.confidence,
                                position=(
                                    highlight_result.position[0],  # x
                                    highlight_result.position[1],  # y
                                    highlight_result.size[0],      # width
                                    highlight_result.size[1]       # height
                                ),
                                highlight_number=highlight_result.highlight_number  # Nouveau champ
                            )
                            
                            task.add_highlight(highlight)
                            page_highlights_count += 1
                            await self.events.publish(HighlightFoundEvent(task_id=task.id, highlight=highlight))
                            
                            logger.info(f"  ✓ Surlignement #{highlight_result.highlight_number} extrait: '{highlight_result.text[:50]}{'...' if len(highlight_result.text) > 50 else ''}' (confiance: {highlight_result.confidence:.0f}%)")
                
                else:
                    # COMPATIBILITÉ: Méthode classique (fallback)
                    logger.warning("Méthode extract_highlights non disponible, utilisation de extract_text")
                    text, confidence = await self.ocr.extract_text(screen_data, region)
                    
                    if self._is_valid_highlight_text(text, confidence, params):
                        highlight = Highlight.create(
                            book_id=task.book_id,
                            page_number=page_num,
                            text=text,
                            confidence=confidence,
                            position=region
                        )
                        
                        task.add_highlight(highlight)
                        page_highlights_count += 1
                        await self.events.publish(HighlightFoundEvent(task_id=task.id, highlight=highlight))
                        logger.info(f"✓ Highlight classique extrait: '{text[:50]}...' (confiance: {confidence:.0f}%)")
            
            if page_highlights_count == 0:
                logger.warning(f"Aucun highlight valide trouvé sur la page {page_num}")
            else:
                logger.info(f"✓ Page {page_num}: {page_highlights_count} surlignement(s) extrait(s)")
            
            # Mise à jour progression
            phase2_progress = (idx + 1) / total_pages * 50  # Phase 2 = 50% du total
            total_progress = 50 + phase2_progress
            
            await self.events.publish(TaskProgressEvent(
                task_id=task.id,
                progress=total_progress,
                message=f"Extraction page {page_num}: {page_highlights_count} surlignement(s) ({idx+1}/{total_pages})"
            ))
        
        logger.info(f"=== FIN PHASE 2: {len(task.highlights_extracted)} highlights individuels extraits ===")
    
    async def _quick_highlight_check(
        self,
        screen_data: bytes,
        params: ExtractionParams
    ) -> bool:
        """
        Vérification rapide si la page contient des surlignements.
        """
        # Utiliser la première région définie ou une zone par défaut
        if params.scan_regions and len(params.scan_regions) > 0:
            test_region = params.scan_regions[0]
            logger.debug(f"Quick check using custom region: {test_region}")
        else:
            # Zone de test par défaut
            test_region = (500, 400, 600, 200)
            logger.debug("Quick check using default region")
        
        # Utiliser la nouvelle méthode de détection si disponible
        if hasattr(self.ocr, 'extract_highlights'):
            highlight_results = await self.ocr.extract_highlights(screen_data, test_region)
            has_highlights = len(highlight_results) > 0
            
            if has_highlights:
                logger.info(f"Quick check found {len(highlight_results)} surlignement(s)")
            else:
                logger.debug("Quick check found no highlights")
            
            return has_highlights
        else:
            # Fallback sur l'ancienne méthode
            text, confidence = await self.ocr.extract_text(screen_data, test_region)
            has_content = len(text.strip()) > params.min_text_length
            
            if has_content:
                logger.info(f"Quick check found text: '{text[:50]}...' (confidence: {confidence:.1f})")
            else:
                logger.debug("Quick check found no text")
            
            return has_content
    
    def _is_valid_highlight_result(
        self,
        highlight_result,  # HighlightResult object
        params: ExtractionParams
    ) -> bool:
        """
        Vérifie si un HighlightResult est valide.
        """
        is_valid = (
            len(highlight_result.text.strip()) >= params.min_text_length and
            highlight_result.confidence >= params.min_confidence
        )
        
        if not is_valid:
            logger.debug(f"Surlignement #{highlight_result.highlight_number} rejeté: len={len(highlight_result.text.strip())}, conf={highlight_result.confidence:.0f}%")
        
        return is_valid
    
    def _is_valid_highlight_text(
        self,
        text: str,
        confidence: float,
        params: ExtractionParams
    ) -> bool:
        """
        Vérifie si le texte extrait est un highlight valide (méthode classique).
        """
        is_valid = (
            len(text.strip()) >= params.min_text_length and
            confidence >= params.min_confidence
        )
        
        if not is_valid:
            logger.debug(f"Texte rejeté: len={len(text.strip())}, conf={confidence:.0f}%")
        
        return is_valid