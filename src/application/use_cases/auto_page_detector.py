"""
Module de détection automatique du nombre de pages pour AllamBik
Ce module est indépendant et n'interfère pas avec le fonctionnement existant
"""
import asyncio
import logging
import hashlib
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class AutoPageDetector:
    """
    Détecteur automatique du nombre de pages d'un livre Kindle.
    Utilise la navigation et la comparaison de hash pour détecter la fin du livre.
    """
    
    def __init__(self, kindle_controller):
        """
        Args:
            kindle_controller: Instance de PyAutoGuiKindleController
        """
        self.kindle = kindle_controller
        self.is_detecting = False
        self.should_cancel = False
        self.detected_pages = None
        
    async def detect_total_pages(self, progress_callback: Optional[Callable] = None) -> int:
        """
        Détecte le nombre total de pages en naviguant dans le livre.
        
        Args:
            progress_callback: Fonction appelée avec (current_page, message)
            
        Returns:
            Nombre total de pages détectées
        """
        if self.is_detecting:
            logger.warning("Détection déjà en cours")
            return 0
            
        self.is_detecting = True
        self.should_cancel = False
        
        try:
            logger.info("=== DÉBUT DÉTECTION AUTOMATIQUE DU NOMBRE DE PAGES ===")
            
            # Étape 1: Retour au début du livre
            if progress_callback:
                await progress_callback(0, "Retour au début du livre...")
            
            await self._go_to_start()
            
            # Étape 2: Parcourir jusqu'à la fin
            page_count = await self._count_pages_forward(progress_callback)
            
            # Étape 3: Retour au début pour être prêt pour l'extraction
            if progress_callback:
                await progress_callback(page_count, f"Détection terminée: {page_count} pages. Retour au début...")
            
            await self._go_to_start()
            
            self.detected_pages = page_count
            logger.info(f"=== DÉTECTION TERMINÉE: {page_count} pages trouvées ===")
            
            return page_count
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection: {e}")
            raise
        finally:
            self.is_detecting = False
    
    def cancel_detection(self):
        """Annule la détection en cours."""
        self.should_cancel = True
        logger.info("Annulation de la détection demandée")
    
    async def _go_to_start(self):
        """Retourne au début du livre."""
        logger.info("Navigation vers le début...")
        
        # Appuyer sur page précédente plusieurs fois
        for i in range(30):
            if self.should_cancel:
                break
                
            # Naviguer vers la page précédente
            current = self.kindle.current_page
            if current > 1:
                await self.kindle.navigate_to_page(current - 1)
            await asyncio.sleep(0.1)
            
            if i % 10 == 0:
                logger.debug(f"Retour arrière... {i}/30")
        
        # Réinitialiser la position
        self.kindle.current_page = 1
        logger.info("Position: début du livre (page 1)")
    
    async def _count_pages_forward(self, progress_callback: Optional[Callable] = None) -> int:
        """
        Compte les pages en avançant jusqu'à détecter la fin.
        """
        page_count = 1
        previous_hash = None
        identical_count = 0
        max_identical = 3  # 3 pages identiques = fin du livre
        
        logger.info("Début du comptage des pages...")
        
        while not self.should_cancel:
            # Capturer l'écran actuel
            try:
                screen_data = await self.kindle.capture_screen()
                
                # Calculer le hash de la page
                current_hash = hashlib.md5(screen_data).hexdigest()
                
                # Comparer avec la page précédente
                if previous_hash and current_hash == previous_hash:
                    identical_count += 1
                    logger.debug(f"Page identique détectée ({identical_count}/{max_identical})")
                    
                    if identical_count >= max_identical:
                        logger.info(f"Fin du livre détectée à la page {page_count}")
                        break
                else:
                    # Page différente, continuer
                    if previous_hash:  # Pas la première page
                        identical_count = 0
                        page_count += 1
                    
                    # Progress update
                    if progress_callback and page_count % 10 == 0:
                        await progress_callback(page_count, f"Détection en cours... Page {page_count}")
                
                previous_hash = current_hash
                
                # Passer à la page suivante
                self.kindle.current_page = page_count
                await self.kindle.navigate_to_page(page_count + 1)
                await asyncio.sleep(0.3)  # Délai pour laisser Kindle tourner la page
                
                # Limite de sécurité
                if page_count > 1000:
                    logger.warning("Limite de sécurité atteinte (1000 pages)")
                    break
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la page {page_count}: {e}")
                break
        
        return page_count
    
    def get_detected_pages(self) -> Optional[int]:
        """Retourne le nombre de pages détectées lors de la dernière détection."""
        return self.detected_pages
