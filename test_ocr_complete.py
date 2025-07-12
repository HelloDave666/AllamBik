"""
Test OCR complet avec détection de surlignements
Script de test pour vérifier que la détection et l'OCR des surlignements fonctionne
"""
import sys
import os
import asyncio

# Ajouter le chemin du projet pour les imports
sys.path.append("src")

def test_complete_ocr():
    """Test complet : détection + OCR + comparaison avec l'ancien système"""
    
    print("TEST OCR COMPLET AVEC DÉTECTION DE SURLIGNEMENTS")
    print("=" * 60)
    
    # Vérifier que l'image de test existe
    image_path = "test_simple.png"
    if not os.path.exists(image_path):
        print(f"ERREUR: Fichier {image_path} non trouvé")
        print("Lancez d'abord le script de capture pour créer cette image")
        return
    
    try:
        # Imports des modules nécessaires
        from infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
        from infrastructure.ocr.tesseract_adapter import TesseractOCREngine, TesseractOCREngineClassic
        
        print("Modules importés avec succès")
        
        # Charger l'image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Configuration de la région Kindle (ajustez si nécessaire)
        region = (1202, 2, 705, 999)
        
        print(f"Analyse de l'image: {image_path}")
        print(f"Région analysée: {region}")
        print()
        
        # ÉTAPE 1: Test de détection seule
        print("ÉTAPE 1: TEST DE DÉTECTION DES SURLIGNEMENTS")
        print("-" * 50)
        
        detector = KindleHighlightDetector(debug_mode=True)
        regions = detector.detect_highlights(image_bytes, region)
        
        print(f"Résultat: {len(regions)} surlignement(s) détecté(s)")
        for i, (x, y, w, h) in enumerate(regions, 1):
            print(f"   {i}. Zone {w}x{h} pixels à la position ({x}, {y})")
        
        if not regions:
            print("ÉCHEC: Aucun surlignement détecté")
            print("Vérifiez que l'image contient bien des surlignements jaunes")
            return
        
        print()
        
        # ÉTAPE 2: Test OCR avec détection (nouveau système)
        print("ÉTAPE 2: TEST OCR AVEC DÉTECTION (NOUVEAU SYSTÈME)")
        print("-" * 50)
        
        # Configuration du chemin Tesseract
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        # Créer l'engine OCR avec détection
        ocr_engine = TesseractOCREngine(
            tesseract_cmd=tesseract_path,
            debug_mode=True
        )
        
        # Fonction async pour le test
        async def test_new_ocr():
            return await ocr_engine.extract_text(image_bytes, region)
        
        # Exécuter l'OCR avec détection
        print("Lancement de l'OCR avec détection...")
        new_text, new_confidence = asyncio.run(test_new_ocr())
        
        print(f"RÉSULTAT (nouveau système):")
        print(f"   Confiance: {new_confidence:.1f}%")
        print(f"   Longueur: {len(new_text)} caractères")
        print(f"   Texte extrait: '{new_text}'")
        print()
        
        # ÉTAPE 3: Test OCR classique (ancien système) pour comparaison
        print("ÉTAPE 3: TEST OCR CLASSIQUE (ANCIEN SYSTÈME)")
        print("-" * 45)
        
        # Créer l'engine OCR classique
        classic_ocr = TesseractOCREngineClassic(
            tesseract_cmd=tesseract_path,
            debug_mode=True
        )
        
        # Fonction async pour le test classique
        async def test_classic_ocr():
            return await classic_ocr.extract_text(image_bytes, region)
        
        # Exécuter l'OCR classique
        print("Lancement de l'OCR classique...")
        classic_text, classic_confidence = asyncio.run(test_classic_ocr())
        
        print(f"RÉSULTAT (système classique):")
        print(f"   Confiance: {classic_confidence:.1f}%")
        print(f"   Longueur: {len(classic_text)} caractères")
        print(f"   Aperçu du texte: '{classic_text[:200]}...'")
        print()
        
        # ÉTAPE 4: Comparaison des résultats
        print("ÉTAPE 4: COMPARAISON DES RÉSULTATS")
        print("-" * 35)
        
        print(f"Statistiques de comparaison:")
        print(f"   Nombre de surlignements détectés: {len(regions)}")
        print(f"   Texte nouveau système: {len(new_text)} caractères")
        print(f"   Texte ancien système: {len(classic_text)} caractères")
        
        if len(classic_text) > 0:
            reduction = 100 - (len(new_text) / len(classic_text) * 100)
            print(f"   Réduction du texte: {reduction:.1f}%")
        print()
        
        # ÉTAPE 5: Analyse qualitative
        print("ÉTAPE 5: ANALYSE QUALITATIVE")
        print("-" * 25)
        
        # Critères de succès
        success_criteria = []
        
        # Critère 1: Le nouveau système doit extraire moins de texte
        if len(new_text) > 0 and len(new_text) < len(classic_text):
            success_criteria.append("✓ Le nouveau système extrait moins de texte (filtrage réussi)")
            criterion1_passed = True
        elif len(new_text) == 0:
            success_criteria.append("✗ Le nouveau système n'a extrait aucun texte")
            criterion1_passed = False
        else:
            success_criteria.append("✗ Le nouveau système extrait autant ou plus de texte")
            criterion1_passed = False
        
        # Critère 2: Vérifier la présence de mots-clés des surlignements
        expected_keywords = ["Président", "dialogue", "robot", "Nao", "Montebourg", "475000", "emplois", "TF1"]
        found_keywords = []
        
        for keyword in expected_keywords:
            if keyword.lower() in new_text.lower():
                found_keywords.append(keyword)
        
        if len(found_keywords) >= 3:
            success_criteria.append(f"✓ Mots-clés des surlignements trouvés: {', '.join(found_keywords)}")
            criterion2_passed = True
        elif len(found_keywords) >= 1:
            success_criteria.append(f"~ Quelques mots-clés trouvés: {', '.join(found_keywords)}")
            criterion2_passed = True
        else:
            success_criteria.append("✗ Aucun mot-clé des surlignements trouvé")
            criterion2_passed = False
        
        # Afficher les critères
        for criterion in success_criteria:
            print(f"   {criterion}")
        
        print()
        
        # ÉTAPE 6: Résultat final et recommandations
        print("ÉTAPE 6: RÉSULTAT FINAL")
        print("-" * 20)
        
        # Déterminer le succès global
        if criterion1_passed and criterion2_passed and len(new_text) > 0:
            print("RÉSULTAT: SUCCÈS COMPLET")
            print("   ✓ La détection de surlignements fonctionne correctement")
            print("   ✓ L'OCR extrait le texte des surlignements uniquement")
            print("   ✓ Le filtrage élimine efficacement le texte non-surligné")
            print("   ✓ Les mots-clés attendus sont présents")
            print()
            print("RECOMMANDATION: SYSTÈME PRÊT POUR L'INTÉGRATION")
            print("Vous pouvez maintenant utiliser le nouveau système dans votre application principale.")
            
        elif len(new_text) > 0 and criterion2_passed:
            print("RÉSULTAT: SUCCÈS PARTIEL")
            print("   ✓ La détection et l'OCR fonctionnent")
            print("   ~ Le filtrage pourrait être amélioré")
            print()
            print("RECOMMANDATION: SYSTÈME UTILISABLE AVEC AJUSTEMENTS")
            
        else:
            print("RÉSULTAT: ÉCHEC OU PROBLÈME")
            print("   ✗ Le système nécessite des ajustements")
            print()
            print("RECOMMANDATION: VÉRIFIER LA CONFIGURATION")
            print("   - Vérifiez que Tesseract est bien installé")
            print("   - Vérifiez que les surlignements sont bien visibles")
            print("   - Consultez les fichiers de debug pour analyser le problème")
        
        print()
        print("FICHIERS DE DEBUG CRÉÉS:")
        print("   - debug_highlights/ : étapes de détection des couleurs")
        print("   - debug_ocr_highlights/ : images des surlignements extraits")
        print("   - test_simple.png : capture d'écran utilisée")
        
    except ImportError as e:
        print(f"ERREUR D'IMPORT: {e}")
        print()
        print("SOLUTIONS POSSIBLES:")
        print("   1. Vérifiez que le fichier kindle_highlight_detector.py existe")
        print("      dans src/infrastructure/ocr/")
        print("   2. Vérifiez que opencv-python est installé:")
        print("      poetry add opencv-python")
        print("   3. Vérifiez que tous les fichiers ont été créés correctement")
        
    except Exception as e:
        print(f"ERREUR GÉNÉRALE: {e}")
        print()
        print("Informations de debug:")
        import traceback
        traceback.print_exc()


def show_extracted_highlights():
    """Affiche la liste des surlignements extraits"""
    
    print("ANALYSE DES SURLIGNEMENTS EXTRAITS")
    print("=" * 40)
    
    highlight_dir = "debug_highlights"
    if not os.path.exists(highlight_dir):
        print(f"ERREUR: Dossier {highlight_dir} non trouvé")
        print("Lancez d'abord le test complet pour créer les fichiers de debug")
        return
    
    # Chercher les fichiers d'highlights extraits
    extracted_files = [f for f in os.listdir(highlight_dir) if f.startswith("extracted_highlight_")]
    
    if not extracted_files:
        print("Aucun fichier de surlignement extrait trouvé")
        print("Relancez le test complet (option 1) pour générer ces fichiers")
        return
    
    print(f"Fichiers de surlignements extraits trouvés: {len(extracted_files)}")
    for i, filename in enumerate(sorted(extracted_files), 1):
        print(f"   {i}. {filename}")
    
    print()
    print("INSTRUCTIONS:")
    print("   - Ouvrez ces fichiers avec un visualiseur d'images")
    print("   - Chaque fichier montre un surlignement isolé")
    print("   - Vérifiez que seul le texte surligné est visible")
    print(f"   - Les fichiers se trouvent dans: {os.path.abspath(highlight_dir)}")


def main():
    """Point d'entrée principal du script de test"""
    
    print("TESTEUR OCR COMPLET - SYSTÈME DE DÉTECTION DE SURLIGNEMENTS")
    print("=" * 65)
    print()
    print("Ce script teste la détection de surlignements Kindle et l'extraction OCR.")
    print()
    print("OPTIONS DISPONIBLES:")
    print("   1. Test OCR complet (détection + OCR + comparaison)")
    print("   2. Afficher les surlignements extraits")
    print("   3. Quitter")
    print()
    
    while True:
        try:
            choice = input("Votre choix (1, 2 ou 3) : ").strip()
            
            if choice == "1":
                print()
                test_complete_ocr()
                break
                
            elif choice == "2":
                print()
                show_extracted_highlights()
                break
                
            elif choice == "3":
                print("Au revoir!")
                break
                
            else:
                print("Choix invalide. Veuillez choisir 1, 2 ou 3.")
                
        except KeyboardInterrupt:
            print("\nInterrompu par l'utilisateur. Au revoir!")
            break
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            break


if __name__ == "__main__":
    main()