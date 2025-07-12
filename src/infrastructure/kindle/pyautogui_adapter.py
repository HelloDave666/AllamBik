"""
Adaptateur PyAutoGUI - Implémentation concrète de KindleController
"""
import asyncio
from typing import Optional
import pyautogui
from PIL import ImageGrab
import io
import logging
import os
from datetime import datetime

from src.application.ports.kindle_controller import KindleController

logger = logging.getLogger(__name__)


class PyAutoGuiKindleController(KindleController):
    """Contrôleur Kindle utilisant PyAutoGUI."""
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialise le contrôleur.
        
        Args:
            debug_mode: Si True, sauvegarde les captures d'écran
        """
        # Configuration PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        self.current_page = 0
        self._executor = None
        self.debug_mode = debug_mode
    
    async def navigate_to_page(self, page: int) -> None:
        """
        Navigue vers une page spécifique.
        
        Args:
            page: Numéro de page cible
        """
        pages_to_move = page - self.current_page
        
        if pages_to_move == 0:
            return
        
        logger.info(f"Navigating from page {self.current_page} to {page}")
        
        # Exécuter dans le thread pool
        loop = asyncio.get_event_loop()
        
        if pages_to_move > 0:
            # Aller vers l'avant
            for _ in range(pages_to_move):
                await loop.run_in_executor(
                    self._executor,
                    pyautogui.press,
                    'right'
                )
                await asyncio.sleep(0.1)
        else:
            # Aller vers l'arrière
            for _ in range(abs(pages_to_move)):
                await loop.run_in_executor(
                    self._executor,
                    pyautogui.press,
                    'left'
                )
                await asyncio.sleep(0.1)
        
        self.current_page = page
    
    async def capture_screen(self) -> bytes:
        """
        Capture l'écran actuel.
        
        Returns:
            Image de l'écran en bytes
        """
        loop = asyncio.get_event_loop()
        
        # Capture dans le thread pool
        screenshot = await loop.run_in_executor(
            self._executor,
            ImageGrab.grab
        )
        
        # Mode debug : sauvegarder la capture complète
        if self.debug_mode:
            self._save_debug_screenshot(screenshot)
        
        # Convertir en bytes
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.debug(f"Screen captured: {screenshot.size} for page {self.current_page}")
        
        return buffer.read()
    
    def _save_debug_screenshot(self, screenshot):
        """Sauvegarde la capture d'écran pour debug."""
        try:
            # Créer le dossier debug si nécessaire
            debug_dir = "debug_captures"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Nom de fichier avec timestamp et page
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{debug_dir}/page_{self.current_page}_{timestamp}.png"
            
            # Sauvegarder
            screenshot.save(filename)
            logger.info(f"Debug: Screenshot saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save debug screenshot: {e}")
    
    async def get_current_page(self) -> Optional[int]:
        """
        Obtient le numéro de page actuel.
        
        Returns:
            Numéro de page actuel
        """
        return self.current_page
    
    async def is_kindle_running(self) -> bool:
        """
        Vérifie si Kindle est en cours d'exécution.
        
        Pour l'instant, vérifie juste si une fenêtre Kindle est visible.
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Chercher la fenêtre Kindle
            windows = await loop.run_in_executor(
                self._executor,
                pyautogui.getWindowsWithTitle,
                'Kindle'
            )
            
            is_running = len(windows) > 0
            logger.info(f"Kindle running: {is_running}")
            
            return is_running
            
        except Exception as e:
            logger.error(f"Failed to check Kindle status: {e}")
            return False