"""
Application principale - Point d'entrée GUI avec détection de surlignements
"""
import asyncio
import threading
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

from src.presentation.gui.views.main_window import MainWindow
from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel
from src.application.use_cases.extract_highlights_use_case import ExtractHighlightsUseCase
from src.infrastructure.ocr.tesseract_adapter import TesseractOCREngine
from src.infrastructure.kindle.pyautogui_adapter import PyAutoGuiKindleController
from src.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from src.infrastructure.persistence.json_repository import JsonHighlightRepository


class AlambikApp:
    """
    Application Alambik v3 avec détection de surlignements Kindle.
    Coordonne l'initialisation et le lancement de l'interface.
    """
    
    def __init__(self):
        """Initialise l'application."""
        self.logger = self._setup_logging()
        self.event_loop = None
        self.window = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def _setup_logging(self):
        """Configure le système de logs."""
        logging.basicConfig(
            level=logging.INFO,  # Réduire à INFO pour moins de verbosité
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _setup_infrastructure(self):
        """Configure l'infrastructure (adaptateurs)."""
        self.logger.info("=== CONFIGURATION DE L'INFRASTRUCTURE ALAMBIK v3 ===")
        
        # OCR Engine avec DÉTECTION DE SURLIGNEMENTS ACTIVÉE
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(tesseract_path).exists():
            self.logger.info(f"✓ Tesseract trouvé: {tesseract_path}")
        else:
            self.logger.warning("⚠ Tesseract non trouvé - l'OCR ne fonctionnera pas")
        
        # NOUVEAU : OCR avec détection de surlignements
        ocr_engine = TesseractOCREngine(
            tesseract_cmd=tesseract_path,
            debug_mode=False  # Désactiver le debug en production pour de meilleures performances
        )
        
        self.logger.info("✓ Moteur OCR configuré avec détection de surlignements Kindle")
        
        # Kindle Controller
        kindle_controller = PyAutoGuiKindleController(
            debug_mode=False  # Désactiver le debug en production
        )
        
        self.logger.info("✓ Contrôleur Kindle configuré")
        
        # Event Bus
        event_bus = InMemoryEventBus()
        
        # Repository pour sauvegarder les résultats
        highlight_repository = JsonHighlightRepository(
            output_dir="extractions"
        )
        
        self.logger.info("✓ Système de sauvegarde configuré (dossier: extractions/)")
        
        return ocr_engine, kindle_controller, event_bus, highlight_repository
    
    def _setup_application(self, ocr_engine, kindle_controller, event_bus, highlight_repository):
        """Configure la couche application."""
        # Use Case principal avec repository
        extraction_usecase = ExtractHighlightsUseCase(
            ocr_engine=ocr_engine,
            kindle_controller=kindle_controller,
            event_bus=event_bus,
            highlight_repository=highlight_repository
        )
        
        self.logger.info("✓ Use case d'extraction configuré avec détection de surlignements")
        
        return extraction_usecase
    
    def _setup_presentation(self, extraction_usecase, event_bus):
        """Configure la couche présentation."""
        # ViewModel
        viewmodel = MainViewModel(
            extraction_usecase=extraction_usecase,
            event_bus=event_bus
        )
        
        # Vue avec référence à la loop asyncio
        self.window = MainWindow(viewmodel)
        self.window.async_loop = self.event_loop
        
        return viewmodel
    
    def _run_async_loop(self):
        """Lance la boucle asyncio dans un thread séparé."""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        # Garder la boucle active
        self.event_loop.run_forever()
    
    def run(self):
        """Lance l'application."""
        try:
            self.logger.info("=== DÉMARRAGE D'ALAMBIK v3.0 AVEC DÉTECTION DE SURLIGNEMENTS ===")
            self.logger.info("")
            self.logger.info("NOUVEAU : L'application extrait maintenant UNIQUEMENT les surlignements jaunes")
            self.logger.info("- Fini l'extraction de tout le texte de la page")
            self.logger.info("- Seuls les passages surlignés dans Kindle seront extraits")
            self.logger.info("- Réduction drastique du bruit et amélioration de la précision")
            self.logger.info("")
            
            # Démarrer la boucle asyncio dans un thread séparé
            async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
            async_thread.start()
            
            # Attendre que la boucle soit prête
            import time
            time.sleep(0.1)
            
            # Configuration des couches
            self.logger.info("Configuration de l'infrastructure...")
            ocr_engine, kindle_controller, event_bus, highlight_repository = self._setup_infrastructure()
            
            self.logger.info("Configuration de l'application...")
            extraction_usecase = self._setup_application(
                ocr_engine, kindle_controller, event_bus, highlight_repository
            )
            
            self.logger.info("Configuration de la présentation...")
            viewmodel = self._setup_presentation(extraction_usecase, event_bus)
            
            # Message final avant lancement
            self.logger.info("")
            self.logger.info("=== APPLICATION PRÊTE ===")
            self.logger.info("UTILISATION :")
            self.logger.info("1. Ouvrez Kindle avec un livre contenant des surlignements jaunes")
            self.logger.info("2. Utilisez l'outil de sélection de zone pour définir la zone de lecture")
            self.logger.info("3. Lancez l'extraction - seuls les surlignements seront extraits")
            self.logger.info("4. Les résultats seront sauvegardés dans le dossier 'extractions/'")
            self.logger.info("")
            
            # Lancer l'interface
            self.logger.info("Lancement de l'interface utilisateur...")
            self.window.mainloop()
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage: {e}", exc_info=True)
            raise
        finally:
            # Nettoyer
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            self.executor.shutdown(wait=True)


def main():
    """Point d'entrée principal."""
    app = AlambikApp()
    app.run()


if __name__ == "__main__":
    main()