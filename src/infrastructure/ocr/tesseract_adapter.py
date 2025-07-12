"""
Adaptateur Tesseract - Implémentation concrète de OCREngine avec détection de surlignements
Version corrigée pour créer des fiches individuelles par surlignement
"""
import asyncio
from typing import Tuple, List
import pytesseract
from PIL import Image, ImageEnhance
import io
import logging
import os
from datetime import datetime
from dataclasses import dataclass

from src.application.ports.ocr_engine import OCREngine

logger = logging.getLogger(__name__)

@dataclass
class HighlightResult:
    """Résultat d'extraction d'un surlignement individuel"""
    text: str
    confidence: float
    position: Tuple[int, int]  # (x, y) - position du surlignement
    size: Tuple[int, int]      # (width, height) - taille du surlignement
    highlight_number: int      # Numéro du surlignement (1, 2, 3...)

# Import dynamique pour éviter les imports circulaires
def get_highlight_detector():
    """Import dynamique du détecteur de surlignements"""
    from src.infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
    return KindleHighlightDetector


class TesseractOCREngine(OCREngine):
    """Implémentation Tesseract du moteur OCR avec détection de surlignements."""
    
    def __init__(self, tesseract_cmd: str = None, debug_mode: bool = False):
        """
        Initialise l'adaptateur Tesseract.
        
        Args:
            tesseract_cmd: Chemin vers l'exécutable Tesseract
            debug_mode: Si True, sauvegarde les captures pour debug
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._executor = None
        self.debug_mode = debug_mode
        self.debug_counter = 0
        self.extraction_counter = 0
        
        # Détecteur de surlignements (import dynamique)
        detector_class = get_highlight_detector()
        self.highlight_detector = detector_class(debug_mode=debug_mode)
    
    async def extract_text(self, image: bytes, region: Tuple[int, int, int, int]) -> Tuple[str, float]:
        """
        MÉTHODE DE COMPATIBILITÉ - Retourne le premier surlignement trouvé
        Pour maintenir la compatibilité avec l'ancienne interface
        """
        highlights = await self.extract_highlights(image, region)
        if highlights:
            first_highlight = highlights[0]
            return first_highlight.text, first_highlight.confidence
        return "", 0.0
    
    async def extract_highlights(self, image: bytes, region: Tuple[int, int, int, int]) -> List[HighlightResult]:
        """
        NOUVELLE MÉTHODE - Extrait tous les surlignements individuellement
        
        Args:
            image: Image en bytes
            region: Tuple (x, y, width, height)
            
        Returns:
            Liste des HighlightResult (un par surlignement détecté)
        """
        self.extraction_counter += 1
        logger.info(f"=== EXTRACTION #{self.extraction_counter} - Region: {region} ===")
        
        loop = asyncio.get_event_loop()
        
        # Exécuter dans un thread pool pour ne pas bloquer
        result = await loop.run_in_executor(
            self._executor,
            self._extract_highlights_individual_sync,
            image,
            region
        )
        
        return result
    
    def _extract_highlights_individual_sync(self, image_bytes: bytes, region: Tuple[int, int, int, int]) -> List[HighlightResult]:
        """Extraction synchrone des surlignements INDIVIDUELS dans un thread séparé."""
        try:
            logger.info(f"Recherche de surlignements dans la région {region}")
            
            # 1. Détecter les zones de surlignement avec leurs positions
            highlight_regions = self.highlight_detector.detect_highlights(image_bytes, region)
            highlight_images = self.highlight_detector.extract_highlight_text_regions(image_bytes, region)
            
            if not highlight_images or not highlight_regions:
                logger.info("Aucun surlignement détecté dans cette région")
                return []
            
            logger.info(f"=== TRAITEMENT INDIVIDUEL DE {len(highlight_images)} SURLIGNEMENT(S) ===")
            
            # 2. Traitement individuel de chaque surlignement
            individual_results = []
            
            for i, (highlight_bytes, region_info) in enumerate(zip(highlight_images, highlight_regions)):
                highlight_num = i + 1
                x, y, w, h = region_info
                
                logger.info(f"--- SURLIGNEMENT {highlight_num}/{len(highlight_images)} ---")
                logger.info(f"Position: ({x}, {y}), Taille: {w}x{h}")
                
                try:
                    # OCR sur le surlignement individuel
                    text, confidence = self._ocr_single_highlight_improved(highlight_bytes, highlight_num)
                    
                    if text.strip() and confidence > 20:  # Seuil de qualité
                        result = HighlightResult(
                            text=text.strip(),
                            confidence=confidence,
                            position=(x, y),
                            size=(w, h),
                            highlight_number=highlight_num
                        )
                        individual_results.append(result)
                        
                        logger.info(f"✓ Surlignement {highlight_num} extrait: '{text[:50]}{'...' if len(text) > 50 else ''}' (confiance: {confidence:.1f}%)")
                    else:
                        logger.info(f"✗ Surlignement {highlight_num}: texte vide ou confiance trop faible ({confidence:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"✗ Erreur OCR sur surlignement {highlight_num}: {e}")
                    continue
            
            logger.info(f"=== RÉSULTAT FINAL: {len(individual_results)} surlignement(s) avec texte extrait ===")
            return individual_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des surlignements: {e}", exc_info=True)
            return []
    
    def _ocr_single_highlight_improved(self, highlight_bytes: bytes, highlight_num: int) -> Tuple[str, float]:
        """
        Fait l'OCR sur un seul surlignement avec plusieurs tentatives d'amélioration.
        
        Args:
            highlight_bytes: Image du surlignement en bytes
            highlight_num: Numéro du surlignement (pour debug)
            
        Returns:
            Tuple (meilleur texte, meilleure confiance)
        """
        try:
            # Charger l'image du surlignement
            original_image = Image.open(io.BytesIO(highlight_bytes))
            
            # Debug: sauvegarder l'image originale
            if self.debug_mode:
                self._save_debug_highlight(original_image, highlight_num, "original")
            
            # Essayer plusieurs configurations d'OCR
            attempts = []
            
            # Tentative 1: Image originale avec PSM 7 (ligne unique)
            text1, conf1 = self._try_ocr_config(original_image, r'--oem 3 --psm 7', "psm7")
            attempts.append((text1, conf1, "PSM7"))
            
            # Tentative 2: Image originale avec PSM 6 (bloc de texte)
            text2, conf2 = self._try_ocr_config(original_image, r'--oem 3 --psm 6', "psm6")
            attempts.append((text2, conf2, "PSM6"))
            
            # Tentative 3: Image agrandie x2 avec PSM 6 (bloc de texte)
            if original_image.width * original_image.height < 10000:  # Agrandir seulement les petites images
                enlarged_image = original_image.resize((original_image.width * 2, original_image.height * 2), Image.LANCZOS)
                if self.debug_mode:
                    self._save_debug_highlight(enlarged_image, highlight_num, "enlarged")
                text3, conf3 = self._try_ocr_config(enlarged_image, r'--oem 3 --psm 6', "enlarged")
                attempts.append((text3, conf3, "Enlarged"))
            
            # Tentative 4: Image avec contraste amélioré
            enhancer = ImageEnhance.Contrast(original_image)
            enhanced_image = enhancer.enhance(1.5)  # Augmenter le contraste
            if self.debug_mode:
                self._save_debug_highlight(enhanced_image, highlight_num, "enhanced")
            text4, conf4 = self._try_ocr_config(enhanced_image, r'--oem 3 --psm 6', "enhanced")
            attempts.append((text4, conf4, "Enhanced"))
            
            # Sélectionner le meilleur résultat
            best_text, best_conf, best_method = "", 0.0, "None"
            
            for text, conf, method in attempts:
                # Privilégier les résultats avec du texte et une confiance décente
                if text and len(text.strip()) > 2:  # Au moins 3 caractères
                    # Favoriser les résultats plus longs avec une confiance raisonnable
                    score = conf + (len(text) * 0.1)  # Bonus pour la longueur
                    current_score = best_conf + (len(best_text) * 0.1)
                    
                    if score > current_score and conf > 30:  # Confiance minimum de 30%
                        best_text, best_conf, best_method = text, conf, method
            
            logger.debug(f"    Surlignement {highlight_num}: Meilleur résultat avec {best_method}")
            return best_text, best_conf
            
        except Exception as e:
            logger.error(f"OCR amélioré échoué pour le surlignement {highlight_num}: {e}", exc_info=True)
            return "", 0.0
    
    def _try_ocr_config(self, image: Image.Image, config: str, method_name: str) -> Tuple[str, float]:
        """Essaie une configuration OCR spécifique."""
        try:
            data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT,
                lang='fra+eng',
                config=config
            )
            
            # Extraire texte et confiance
            texts = []
            confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                if text and conf > 0:
                    texts.append(text)
                    confidences.append(conf)
            
            # Combiner les résultats
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.debug(f"      {method_name}: '{full_text}' (conf: {avg_confidence:.1f}%)")
            return full_text, avg_confidence
            
        except Exception as e:
            logger.debug(f"      {method_name}: Échec - {e}")
            return "", 0.0
    
    def _save_debug_highlight(self, image: Image.Image, highlight_num: int, suffix: str = ""):
        """Sauvegarde l'image d'un surlignement pour debug."""
        try:
            debug_dir = "debug_ocr_highlights"
            os.makedirs(debug_dir, exist_ok=True)
            
            self.debug_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if suffix:
                filename = f"{debug_dir}/highlight_{timestamp}_{highlight_num}_{suffix}.png"
            else:
                filename = f"{debug_dir}/highlight_{timestamp}_{highlight_num}.png"
            
            image.save(filename)
            logger.debug(f"Debug: Surlignement sauvegardé dans {filename}")
            
        except Exception as e:
            logger.error(f"Échec de la sauvegarde du surlignement: {e}")
    
    async def is_available(self) -> bool:
        """Vérifie si Tesseract est disponible."""
        try:
            loop = asyncio.get_event_loop()
            version = await loop.run_in_executor(
                self._executor,
                pytesseract.get_tesseract_version
            )
            logger.info(f"Tesseract available: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            return False


# Version de compatibilité pour les tests sans détection
class TesseractOCREngineClassic(OCREngine):
    """Version classique sans détection de surlignements (pour comparaison)."""
    
    def __init__(self, tesseract_cmd: str = None, debug_mode: bool = False):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._executor = None
        self.debug_mode = debug_mode
        self.extraction_counter = 0
    
    async def extract_text(self, image: bytes, region: Tuple[int, int, int, int]) -> Tuple[str, float]:
        """Version classique qui extrait tout le texte."""
        self.extraction_counter += 1
        logger.info(f"=== EXTRACTION CLASSIQUE #{self.extraction_counter} - Region: {region} ===")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._extract_classic_sync,
            image,
            region
        )
    
    def _extract_classic_sync(self, image_bytes: bytes, region: Tuple[int, int, int, int]) -> Tuple[str, float]:
        """Extraction classique de tout le texte."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            x, y, w, h = region
            cropped = image.crop((x, y, x + w, y + h))
            
            custom_config = r'--oem 3 --psm 6'
            data = pytesseract.image_to_data(
                cropped, 
                output_type=pytesseract.Output.DICT,
                lang='fra+eng',
                config=custom_config
            )
            
            texts = []
            confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                if text and conf > 0:
                    texts.append(text)
                    confidences.append(conf)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"TEXTE CLASSIQUE: '{full_text[:100]}...' (confiance: {avg_confidence:.1f}%)")
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"OCR classique échoué: {e}", exc_info=True)
            return "", 0.0
    
    async def is_available(self) -> bool:
        return True