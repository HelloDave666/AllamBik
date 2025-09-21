"""
Détecteur de surlignements Kindle avec masquage précis des zones jaunes
Version améliorée pour extraire uniquement le texte surligné
"""
import cv2
import numpy as np
from PIL import Image
import io
from typing import List, Tuple
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class KindleHighlightDetector:
    def __init__(self, debug_mode=True):
        # Paramètres configurables
        
        # Plages de couleurs HSV pour détecter les surlignements jaunes
        self.yellow_ranges = [
            ((20, 40, 100), (30, 255, 255)),   # Jaune principal Kindle
            ((15, 30, 80), (35, 200, 255)),    # Jaune plus large
            ((18, 50, 120), (28, 255, 255)),   # Jaune saturé
        ]
        
        # Filtrage des zones détectées
        self.min_area = 250              # Surface minimale en pixels 
        self.min_width = 35              # Largeur minimale en pixels
        self.min_height = 12             # Hauteur minimale en pixels
        self.max_aspect_ratio = 25       # Ratio largeur/hauteur max
        self.min_yellow_ratio = 0.4      # Pourcentage minimum de pixels jaunes
        
        # Morphologie pour nettoyage des masques
        self.morphology_kernel_size = 3
        self.morphology_iterations = 2
        
        # Expansion des zones détectées
        self.expand_x = 8                # Pixels à ajouter horizontalement
        self.expand_y = 4                # Pixels à ajouter verticalement
        
        # Configuration debug
        self.debug_enabled = debug_mode
        self.debug_dir = "debug_highlights"
        
        if self.debug_enabled:
            os.makedirs(self.debug_dir, exist_ok=True)
    
    def extract_highlight_text_regions(self, image_data: bytes, region: Tuple[int, int, int, int] = None) -> List[bytes]:
        """
        Extrait les images des zones de surlignement avec masquage précis
        
        Args:
            image_data: Données de l'image en bytes
            region: Région à analyser (x, y, width, height)
            
        Returns:
            Liste des images des surlignements avec masquage précis en bytes
        """
        try:
            # Détecter les surlignements et leurs masques précis
            highlight_regions, precise_masks = self.detect_highlights_with_masks(image_data, region)
            
            if not highlight_regions:
                logger.info("Aucun surlignement détecté")
                return []
            
            # Conversion en image PIL pour extraction
            pil_image = Image.open(io.BytesIO(image_data))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            highlight_images = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            logger.info(f"Extraction des surlignements avec masquage précis:")
            
            for i, ((x, y, w, h), mask) in enumerate(zip(highlight_regions, precise_masks)):
                logger.info(f"  Extraction du surlignement {i+1}/{len(highlight_regions)}: Y={y}, taille {w}x{h}")
                
                # Extraction de l'image avec masquage précis
                masked_image = self._apply_precise_mask(pil_image, (x, y, w, h), mask)
                
                # Conversion en bytes
                img_bytes = io.BytesIO()
                masked_image.save(img_bytes, format='PNG')
                highlight_images.append(img_bytes.getvalue())
                
                # Debug : sauvegarde de l'image extraite
                if self.debug_enabled:
                    debug_dir = "debug_ocr_highlights"
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = os.path.join(debug_dir, f"precise_highlight_{timestamp}_ordre{i+1:02d}_Y{y}.png")
                    masked_image.save(debug_file)
                    logger.info(f"Debug: Image masquée sauvegardée -> {debug_file}")
            
            logger.info(f"Résultat: {len(highlight_images)} image(s) de surlignement avec masquage précis extraite(s)")
            return highlight_images
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des images de surlignements : {e}")
            return []

    def detect_highlights_with_masks(self, image_data: bytes, region: Tuple[int, int, int, int] = None) -> Tuple[List[Tuple[int, int, int, int]], List[np.ndarray]]:
        """
        Détecte les surlignements jaunes et leurs masques précis
        
        Returns:
            Tuple (liste_rectangles, liste_masques_précis)
        """
        try:
            # Conversion en image OpenCV
            pil_image = Image.open(io.BytesIO(image_data))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            image_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Application de la région si spécifiée
            if region:
                x, y, w, h = region
                image_cv = image_cv[y:y+h, x:x+w]
                offset_x, offset_y = x, y
            else:
                offset_x, offset_y = 0, 0
            
            # Debug : sauvegarde de l'image originale
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.debug_enabled:
                debug_original = os.path.join(self.debug_dir, f"step_{timestamp}_01_original.png")
                cv2.imwrite(debug_original, image_cv)
                logger.info(f"Image originale sauvegardée : {debug_original}")
            
            # Conversion en HSV
            hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)
            
            # Création du masque combiné pour toutes les plages de jaune
            combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            for i, (lower, upper) in enumerate(self.yellow_ranges):
                lower_np = np.array(lower)
                upper_np = np.array(upper)
                mask = cv2.inRange(hsv, lower_np, upper_np)
                combined_mask = cv2.bitwise_or(combined_mask, mask)
                
                if self.debug_enabled:
                    debug_mask = os.path.join(self.debug_dir, f"step_{timestamp}_03_mask_range_{i+1}.png")
                    cv2.imwrite(debug_mask, mask)
            
            if self.debug_enabled:
                debug_combined = os.path.join(self.debug_dir, f"step_{timestamp}_04_mask_combined.png")
                cv2.imwrite(debug_combined, combined_mask)
            
            # Nettoyage morphologique
            kernel = np.ones((self.morphology_kernel_size, self.morphology_kernel_size), np.uint8)
            cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=self.morphology_iterations)
            cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            if self.debug_enabled:
                debug_cleaned = os.path.join(self.debug_dir, f"step_{timestamp}_05_mask_cleaned.png")
                cv2.imwrite(debug_cleaned, cleaned_mask)
            
            # Détection des contours
            contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtrage et extraction des régions avec leurs masques
            highlight_regions = []
            precise_masks = []
            debug_image = image_cv.copy()
            
            for i, contour in enumerate(contours):
                # Rectangle englobant
                x, y, w, h = cv2.boundingRect(contour)
                
                # Application des filtres de qualité
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Calcul du ratio de pixels jaunes dans la région
                roi_mask = cleaned_mask[y:y+h, x:x+w]
                yellow_pixels = cv2.countNonZero(roi_mask)
                total_pixels = w * h
                yellow_ratio = yellow_pixels / total_pixels if total_pixels > 0 else 0
                
                logger.info(f"Contour {i+1}: area={area}, size={w}x{h}, ratio={aspect_ratio:.1f}, yellow_ratio={yellow_ratio:.3f}")
                
                # Vérification des critères
                if (area >= self.min_area and 
                    w >= self.min_width and 
                    h >= self.min_height and 
                    aspect_ratio <= self.max_aspect_ratio and
                    yellow_ratio >= self.min_yellow_ratio):
                    
                    # Expansion de la région pour une meilleure capture du texte
                    x_expanded = max(0, x - self.expand_x)
                    y_expanded = max(0, y - self.expand_y)
                    w_expanded = min(image_cv.shape[1] - x_expanded, w + 2 * self.expand_x)
                    h_expanded = min(image_cv.shape[0] - y_expanded, h + 2 * self.expand_y)
                    
                    # Extraction du masque précis pour cette région
                    precise_mask = cleaned_mask[y_expanded:y_expanded+h_expanded, x_expanded:x_expanded+w_expanded]
                    
                    # Ajout de l'offset de la région
                    final_region = (
                        x_expanded + offset_x,
                        y_expanded + offset_y,
                        w_expanded,
                        h_expanded
                    )
                    
                    highlight_regions.append(final_region)
                    precise_masks.append(precise_mask)
                    
                    # Debug : dessiner le rectangle sur l'image
                    cv2.rectangle(debug_image, (x_expanded, y_expanded), 
                                (x_expanded + w_expanded, y_expanded + h_expanded), (0, 255, 0), 2)
                    cv2.putText(debug_image, f"{len(highlight_regions)}", 
                              (x_expanded, y_expanded - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    logger.info(f"Surlignement valide {len(highlight_regions)}: {final_region}")
                else:
                    # Debug : dessiner en rouge les régions rejetées
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 0, 255), 1)
                    
                    # Raison du rejet
                    reject_reason = []
                    if area < self.min_area: reject_reason.append(f"area<{self.min_area}")
                    if w < self.min_width: reject_reason.append(f"w<{self.min_width}")
                    if h < self.min_height: reject_reason.append(f"h<{self.min_height}")
                    if aspect_ratio > self.max_aspect_ratio: reject_reason.append(f"ratio>{self.max_aspect_ratio}")
                    if yellow_ratio < self.min_yellow_ratio: reject_reason.append(f"yellow<{self.min_yellow_ratio:.2f}")
                    
                    logger.info(f"Région rejetée: {' '.join(reject_reason)}")
            
            # Sauvegarde de l'image avec détections
            if self.debug_enabled:
                debug_detected = os.path.join(self.debug_dir, f"step_{timestamp}_06_detected_highlights.png")
                cv2.imwrite(debug_detected, debug_image)
                logger.info(f"Détections sauvegardées : {debug_detected}")
            
            # Tri des régions du haut vers le bas
            sorted_indices = sorted(range(len(highlight_regions)), key=lambda i: highlight_regions[i][1])
            highlight_regions = [highlight_regions[i] for i in sorted_indices]
            precise_masks = [precise_masks[i] for i in sorted_indices]
            
            logger.info(f"Résultat: {len(highlight_regions)} surlignement(s) détecté(s) avec masques précis")
            return highlight_regions, precise_masks
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des surlignements : {e}")
            return [], []

    def _apply_precise_mask(self, pil_image: Image.Image, region: Tuple[int, int, int, int], mask: np.ndarray) -> Image.Image:
        """
        Applique le masque précis à l'image pour ne garder que les pixels surlignés
        
        Args:
            pil_image: Image PIL originale
            region: Rectangle de la région (x, y, width, height)
            mask: Masque binaire des pixels jaunes
            
        Returns:
            Image PIL avec seulement les pixels surlignés sur fond blanc
        """
        x, y, w, h = region
        
        # Extraction de la région
        cropped = pil_image.crop((x, y, x + w, y + h))
        
        # Conversion en numpy pour manipulation
        img_array = np.array(cropped)
        
        # Redimensionner le masque si nécessaire
        if mask.shape != img_array.shape[:2]:
            mask = cv2.resize(mask, (img_array.shape[1], img_array.shape[0]))
        
        # Créer une image de fond blanc
        white_background = np.ones_like(img_array) * 255
        
        # Appliquer le masque : garder les pixels surlignés, reste en blanc
        mask_3d = np.stack([mask, mask, mask], axis=2) > 0
        result = np.where(mask_3d, img_array, white_background)
        
        return Image.fromarray(result.astype(np.uint8))

    def detect_highlights(self, image_data: bytes, region: Tuple[int, int, int, int] = None) -> List[Tuple[int, int, int, int]]:
        """
        Méthode de compatibilité - retourne seulement les rectangles
        """
        highlight_regions, _ = self.detect_highlights_with_masks(image_data, region)
        return highlight_regions

    def print_current_settings(self):
        """Affiche les paramètres actuels pour le debug"""
        print("=== PARAMÈTRES ACTUELS DE DÉTECTION ===")
        print(f"Plages de couleurs HSV: {len(self.yellow_ranges)} plages")
        for i, (lower, upper) in enumerate(self.yellow_ranges):
            print(f"  Plage {i+1}: {lower} -> {upper}")
        print(f"Surface minimale: {self.min_area} pixels")
        print(f"Dimensions minimales: {self.min_width}x{self.min_height} pixels")
        print(f"Ratio aspect max: {self.max_aspect_ratio}")
        print(f"Ratio jaune minimum: {self.min_yellow_ratio*100:.1f}%")
        print(f"Expansion: +{self.expand_x}x{self.expand_y} pixels")
        print(f"Debug activé: {self.debug_enabled}")
        print("=========================================")

# Test principal si exécuté directement
if __name__ == "__main__":
    detector = KindleHighlightDetector()
    detector.print_current_settings()
    
    # Test avec une image existante si disponible
    test_image = "test_simple.png"
    if os.path.exists(test_image):
        print(f"\nTest avec l'image: {test_image}")
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        # Test avec région Kindle typique
        region = (1202, 2, 705, 999)
        highlights, masks = detector.detect_highlights_with_masks(image_data, region)
        
        print(f"Résultat: {len(highlights)} surlignement(s) détecté(s) avec masques précis")
        for i, ((x, y, w, h), mask) in enumerate(zip(highlights, masks)):
            yellow_pixels = cv2.countNonZero(mask)
            total_pixels = w * h
            precision = yellow_pixels / total_pixels * 100 if total_pixels > 0 else 0
            print(f"  {i+1}. Position ({x}, {y}), taille {w}x{h}, précision masque: {precision:.1f}%")
    else:
        print(f"\nImage de test '{test_image}' non trouvée")
        print("Lancez d'abord un test pour créer une image de test")