"""
Application principale - Point d'entrÃ©e GUI avec dÃ©tection de surlignements
"""
import asyncio
import threading
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

from src.presentation.gui.views.main_window import MainWindow
from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel
from src.application.use_cases.extract_highlights_use_case import ExtractHighlightsUseCase
from src.application.use_cases.auto_page_detector import AutoPageDetector
from src.infrastructure.ocr.tesseract_adapter import TesseractOCREngine
from src.infrastructure.kindle.pyautogui_adapter import PyAutoGuiKindleController
from src.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from src.infrastructure.persistence.json_repository import JsonHighlightRepository
import time


class AllamBikApp:
    """
    Application AllamBik v3 avec dÃ©tection de surlignements Kindle.
    Coordonne l'initialisation et le lancement de l'interface.
    """
    
    def __init__(self):
        """Initialise l'application."""
        self.logger = self._setup_logging()
        self.event_loop = None
        self.window = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def _setup_logging(self):
        """Configure le systÃ¨me de logs."""
        logging.basicConfig(
            level=logging.INFO,  # RÃ©duire Ã  INFO pour moins de verbositÃ©
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _setup_infrastructure(self):
        """Configure l'infrastructure (adaptateurs)."""
        self.logger.info("=== CONFIGURATION DE L'INFRASTRUCTURE ALLAMBIK v3 ===")
        
        # OCR Engine avec DÃ‰TECTION DE SURLIGNEMENTS ACTIVÃ‰E
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(tesseract_path).exists():
            self.logger.info(f"âœ“ Tesseract trouvÃ©: {tesseract_path}")
        else:
            self.logger.warning("âš  Tesseract non trouvÃ© - l'OCR ne fonctionnera pas")
        
        # NOUVEAU : OCR avec dÃ©tection de surlignements
        ocr_engine = TesseractOCREngine(
            tesseract_cmd=tesseract_path,
            debug_mode=False  # DÃ©sactiver le debug en production pour de meilleures performances
        )
        
        self.logger.info("âœ“ Moteur OCR configurÃ© avec dÃ©tection de surlignements Kindle")
        
        # Kindle Controller
        kindle_controller = PyAutoGuiKindleController(
            debug_mode=False  # DÃ©sactiver le debug en production
        )
        
        self.logger.info("âœ“ ContrÃ´leur Kindle configurÃ©")
        
        # Event Bus
        event_bus = InMemoryEventBus()
        
        # Repository pour sauvegarder les rÃ©sultats
        highlight_repository = JsonHighlightRepository(
            output_dir="extractions"
        )
        
        self.logger.info("âœ“ SystÃ¨me de sauvegarde configurÃ© (dossier: extractions/)")
        
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
        
        self.logger.info("âœ“ Use case d'extraction configurÃ© avec dÃ©tection de surlignements")
        
        return extraction_usecase
    
    def _setup_presentation(self, extraction_usecase, event_bus):
        """Configure la couche présentation avec détecteur de pages."""
        # ViewModel principal
        viewmodel = MainViewModel(
            extraction_usecase=extraction_usecase,
            event_bus=event_bus
        )
        
        # Créer et assigner le détecteur de pages
        try:
            if hasattr(self, 'kindle_controller') and self.kindle_controller:
                from src.application.use_cases.auto_page_detector import AutoPageDetector
                page_detector = AutoPageDetector(self.kindle_controller)
                viewmodel.page_detector = page_detector
                self.logger.info("✓ Détecteur de pages configuré et assigné au ViewModel")
            else:
                self.logger.warning("kindle_controller non disponible pour le détecteur")
        except Exception as e:
            self.logger.error(f"Erreur création détecteur: {e}")
            import traceback
            traceback.print_exc()
        
        # Binding des événements
        viewmodel.on_state_changed = lambda state: self.logger.debug(f"État: {state}")
        
        return viewmodel
    
    def _run_async_loop(self):
        """Lance la boucle asyncio dans un thread sÃ©parÃ©."""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        # Garder la boucle active
        self.event_loop.run_forever()
    
    def run(self):
        """Lance l'application avec configuration complète."""
        try:
            self.logger.info("=== DÉMARRAGE D'ALLAMBIK v3.0 AVEC DÉTECTION DE SURLIGNEMENTS ===")
            self.logger.info("")
            self.logger.info("NOUVEAU : L'application extrait maintenant UNIQUEMENT les surlignements jaunes")
            self.logger.info("- Fini l'extraction de tout le texte de la page")
            self.logger.info("- Seuls les passages surlignés dans Kindle seront extraits")
            self.logger.info("- Réduction drastique du bruit et amélioration de la précision")
            self.logger.info("")
            
            # 1. Configuration de l'infrastructure
            self.logger.info("Configuration de l'infrastructure...")
            ocr_engine, kindle_controller, event_bus, highlight_repository = self._setup_infrastructure()
            
            # IMPORTANT: Stocker kindle_controller comme attribut de classe
            self.kindle_controller = kindle_controller
            
            # 2. Configuration de la couche application
            self.logger.info("Configuration de l'application...")
            extraction_usecase = self._setup_application(
                ocr_engine, kindle_controller, event_bus, highlight_repository
            )
            
            # 3. Configuration de la présentation (peut maintenant utiliser self.kindle_controller)
            self.logger.info("Configuration de la présentation...")
            viewmodel = self._setup_presentation(extraction_usecase, event_bus)
            
            # 4. Configuration de l'interface
            self.window = MainWindow(viewmodel)
            
            # 5. Démarrage de la boucle async
            async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
            async_thread.start()
            
            # Attendre que la boucle soit prête
            while not hasattr(self, 'async_loop') or not self.async_loop:
                time.sleep(0.1)
            
            self.window.async_loop = self.async_loop
            
            self.logger.info("")
            self.logger.info("=== APPLICATION PRÊTE ===")
            self.logger.info("UTILISATION :")
            self.logger.info("1. Ouvrez Kindle avec un livre contenant des surlignements jaunes")
            self.logger.info("2. Utilisez l'outil de sélection de zone pour définir la zone de lecture")
            self.logger.info("3. Lancez l'extraction - seuls les surlignements seront extraits")
            self.logger.info("4. Les résultats seront sauvegardés dans le dossier 'extractions/'")
            self.logger.info("")
            
            # 6. Lancer l'interface
            self.logger.info("Lancement de l'interface utilisateur...")
            self.window.mainloop()
            
        except Exception as e:
            self.logger.error(f"Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            raise
if __name__ == "__main__":
    main()


def main():
    """Point d'entrée principal de l'application."""
    app = AllamBikApp()
    app.run()


if __name__ == "__main__":
    main()
