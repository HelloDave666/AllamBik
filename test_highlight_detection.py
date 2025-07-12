"""
Script de test pour la détection des surlignements Kindle
Utilise PyAutoGui pour capturer l'écran et tester la détection
"""
import pyautogui
import time
import logging
from pathlib import Path
import sys

# Ajouter le chemin du projet
sys.path.append("src")

from infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
from infrastructure.ocr.tesseract_adapter import TesseractOCREngine

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_screen_capture_and_detection():
    """
    Test complet : capture d'écran + détection + OCR
    """
    print("=== TEST DE DÉTECTION DE SURLIGNEMENTS KINDLE ===")
    print()
    
    # Zone de test (ajustez selon votre écran Kindle)
    # Ces coordonnées correspondent à la zone de contenu Kindle
    test_region = (1202, 2, 705, 999)  # Votre zone actuelle
    
    print(f"Zone de test : {test_region}")
    print("Position Kindle et appuyez sur Entrée pour capturer...")
    input()
    
    # Capture d'écran
    print("Capture d'écran en cours...")
    screenshot = pyautogui.screenshot()
    
    # Sauvegarder la capture
    screenshot.save("test_capture.png")
    print("✓ Capture sauvegardée : test_capture.png")
    
    # Convertir en bytes
    import io
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format='PNG')
    image_bytes = img_bytes.getvalue()
    
    # Tester la détection
    print("\n1. Test de détection des surlignements...")
    detector = KindleHighlightDetector(debug_mode=True)
    
    highlight_regions = detector.detect_highlights(image_bytes, test_region)
    
    if highlight_regions:
        print(f"✓ {len(highlight_regions)} surlignement(s) détecté(s) :")
        for i, (x, y, w, h) in enumerate(highlight_regions, 1):
            print(f"  Surlignement {i}: position ({x}, {y}), taille {w}x{h}")
    else:
        print("✗ Aucun surlignement détecté")
        print("Vérifiez que :")
        print("  - Kindle est ouvert")
        print("  - Il y a des surlignements jaunes visibles")
        print("  - La zone de capture est correcte")
        return
    
    # Tester l'OCR avec détection
    print("\n2. Test de l'OCR avec détection de surlignements...")
    ocr_engine = TesseractOCREngine(
        tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        debug_mode=True
    )
    
    import asyncio
    
    async def test_ocr():
        text, confidence = await ocr_engine.extract_text(image_bytes, test_region)
        return text, confidence
    
    text, confidence = asyncio.run(test_ocr())
    
    if text:
        print(f"✓ Texte extrait des surlignements :")
        print(f"  Confiance : {confidence:.1f}%")
        print(f"  Texte : '{text}'")
    else:
        print("✗ Aucun texte extrait")
    
    # Comparaison avec l'OCR classique
    print("\n3. Comparaison avec l'OCR classique (tout le texte)...")
    from infrastructure.ocr.tesseract_adapter import TesseractOCREngineClassic
    
    classic_ocr = TesseractOCREngineClassic(
        tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        debug_mode=True
    )
    
    async def test_classic_ocr():
        text, confidence = await classic_ocr.extract_text(image_bytes, test_region)
        return text, confidence
    
    classic_text, classic_confidence = asyncio.run(test_classic_ocr())
    
    print(f"✓ OCR classique (tout le texte) :")
    print(f"  Confiance : {classic_confidence:.1f}%")
    print(f"  Texte : '{classic_text[:200]}...'")
    
    # Résumé
    print("\n=== RÉSUMÉ ===")
    print(f"Surlignements détectés : {len(highlight_regions)}")
    print(f"Texte surlignements uniquement : {len(text)} caractères")
    print(f"Texte complet (classique) : {len(classic_text)} caractères")
    
    if len(text) > 0 and len(text) < len(classic_text):
        print("✓ La détection semble fonctionner ! Le texte filtré est plus court.")
    else:
        print("⚠ Vérifiez les résultats dans les dossiers debug_*")
    
    print("\nFichiers générés :")
    print("  - test_capture.png : capture d'écran complète")
    print("  - debug_highlights/ : étapes de détection")
    print("  - debug_ocr_highlights/ : surlignements extraits")


def test_highlight_detection_only():
    """
    Test rapide de détection uniquement
    """
    print("=== TEST RAPIDE DE DÉTECTION ===")
    print("Position Kindle et appuyez sur Entrée...")
    input()
    
    # Capture
    screenshot = pyautogui.screenshot()
    import io
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format='PNG')
    image_bytes = img_bytes.getvalue()
    
    # Détection
    detector = KindleHighlightDetector(debug_mode=True)
    test_region = (1202, 2, 705, 999)
    
    regions = detector.detect_highlights(image_bytes, test_region)
    
    print(f"Résultat : {len(regions)} surlignement(s) détecté(s)")
    for i, region in enumerate(regions, 1):
        print(f"  {i}. {region}")


if __name__ == "__main__":
    print("Choisissez un test :")
    print("1. Test complet (détection + OCR + comparaison)")
    print("2. Test rapide (détection uniquement)")
    
    choice = input("Votre choix (1 ou 2) : ").strip()
    
    try:
        if choice == "1":
            test_screen_capture_and_detection()
        elif choice == "2":
            test_highlight_detection_only()
        else:
            print("Choix invalide")
    except Exception as e:
        logger.error(f"Erreur lors du test : {e}", exc_info=True)
        print(f"\nErreur : {e}")
        print("Vérifiez que :")
        print("  - OpenCV est installé (poetry add opencv-python)")
        print("  - Tesseract est disponible")
        print("  - Kindle est ouvert")