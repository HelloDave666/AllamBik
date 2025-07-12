"""
Script de test CORRIGÉ pour la détection de surlignements
"""
import pyautogui
import time
import sys
import os

def test_with_existing_image():
    """Test avec l'image déjà capturée"""
    print("🔍 TEST AVEC L'IMAGE EXISTANTE")
    print("=" * 40)
    
    image_path = "test_simple.png"
    if not os.path.exists(image_path):
        print(f"❌ Fichier {image_path} non trouvé")
        print("Lancez d'abord le test de capture")
        return
    
    try:
        # Import du détecteur
        sys.path.append("src")
        from infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
        
        print(f"✅ Détecteur importé avec succès")
        print(f"📁 Analyse de {image_path}...")
        
        # Charger l'image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Tester la détection
        detector = KindleHighlightDetector(debug_mode=True)
        region = (1202, 2, 705, 999)  # Zone Kindle
        
        print(f"🔍 Recherche de surlignements dans la région {region}...")
        regions = detector.detect_highlights(image_bytes, region)
        
        print()
        print("📊 RÉSULTAT :")
        if regions:
            print(f"✅ {len(regions)} surlignement(s) détecté(s) !")
            for i, (x, y, w, h) in enumerate(regions, 1):
                print(f"   {i}. Zone {w}x{h} pixels à la position ({x}, {y})")
            
            print()
            print("🎉 FÉLICITATIONS ! La détection fonctionne.")
            print("📁 Vérifiez les fichiers dans debug_highlights/ pour voir le processus")
            
        else:
            print("❌ Aucun surlignement détecté")
            print()
            print("💡 DIAGNOSTIC :")
            print("   - Vérifiez debug_highlights/ pour voir le processus de détection")
            print("   - Les paramètres de couleur peuvent nécessiter un ajustement")
        
        # Test d'extraction des images
        if regions:
            print()
            print("🖼️  Test d'extraction des images de surlignements...")
            highlight_images = detector.extract_highlight_text_regions(image_bytes, region)
            print(f"✅ {len(highlight_images)} images extraites pour l'OCR")
        
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        print("💡 Vérifiez que le fichier kindle_highlight_detector.py est bien créé")
        print("   dans src/infrastructure/ocr/")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()


def test_new_capture():
    """Nouveau test avec capture"""
    print("📸 NOUVEAU TEST AVEC CAPTURE")
    print("=" * 35)
    
    print("📋 Préparez Kindle avec des surlignements jaunes")
    print("👆 Appuyez sur Entrée quand vous êtes prêt...")
    input()
    
    for i in range(5, 0, -1):
        print(f"⏰ Capture dans {i} secondes...")
        time.sleep(1)
    
    print("📸 CAPTURE...")
    screenshot = pyautogui.screenshot()
    screenshot.save("test_new_capture.png")
    print("✅ Nouvelle capture sauvée : test_new_capture.png")
    
    # Test immédiat avec la nouvelle capture
    try:
        sys.path.append("src")
        from infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
        
        # Convertir en bytes
        import io
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        image_bytes = img_bytes.getvalue()
        
        # Test
        detector = KindleHighlightDetector(debug_mode=True)
        region = (1202, 2, 705, 999)
        regions = detector.detect_highlights(image_bytes, region)
        
        print(f"📊 {len(regions)} surlignement(s) détecté(s) dans la nouvelle capture")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")


if __name__ == "__main__":
    print("🔍 TESTEUR DE DÉTECTION (VERSION CORRIGÉE)")
    print("=" * 45)
    print()
    print("Options :")
    print("1. Tester avec l'image existante (test_simple.png)")
    print("2. Nouvelle capture + test")
    print("3. Test du détecteur uniquement (sans interface)")
    print()
    
    choice = input("Votre choix (1, 2 ou 3) : ").strip()
    
    if choice == "1":
        test_with_existing_image()
    elif choice == "2":
        test_new_capture()
    elif choice == "3":
        # Test direct du module
        os.system("poetry run python src/infrastructure/ocr/kindle_highlight_detector.py")
    else:
        print("❌ Choix invalide")