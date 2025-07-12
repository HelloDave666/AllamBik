"""
Script de calibration pour ajuster les paramètres de détection de surlignements
"""
import os
import sys
import json
from datetime import datetime

# Ajout du chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_with_parameters(**params):
    """Test la détection avec des paramètres personnalisés"""
    from infrastructure.ocr.kindle_highlight_detector import KindleHighlightDetector
    
    # Créer un détecteur avec les paramètres modifiés
    detector = KindleHighlightDetector()
    
    # Appliquer les paramètres personnalisés
    for param, value in params.items():
        if hasattr(detector, param):
            setattr(detector, param, value)
            print(f"📝 {param} = {value}")
    
    # Test avec l'image existante
    test_image = "test_simple.png"
    if not os.path.exists(test_image):
        print(f"❌ Image de test '{test_image}' non trouvée")
        print("Lancez d'abord: poetry run python test_simple.py")
        return []
    
    with open(test_image, 'rb') as f:
        image_data = f.read()
    
    # Région Kindle typique
    region = (1202, 2, 705, 999)
    highlights = detector.detect_highlights(image_data, region)
    
    print(f"✅ {len(highlights)} surlignement(s) détecté(s)")
    for i, (x, y, w, h) in enumerate(highlights):
        print(f"  {i+1}. Position ({x}, {y}), taille {w}x{h}")
    
    return highlights

def save_best_parameters(params, num_highlights):
    """Sauvegarde les meilleurs paramètres trouvés"""
    config = {
        "timestamp": datetime.now().isoformat(),
        "num_highlights": num_highlights,
        "parameters": params
    }
    
    with open("best_detection_params.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"💾 Paramètres sauvegardés dans best_detection_params.json")

def load_saved_parameters():
    """Charge les paramètres sauvegardés"""
    if os.path.exists("best_detection_params.json"):
        with open("best_detection_params.json", "r") as f:
            config = json.load(f)
        return config["parameters"]
    return {}

def main():
    print("🔧 CALIBRATEUR DE DÉTECTION DE SURLIGNEMENTS")
    print("=" * 50)
    
    # Paramètres de base (valeurs par défaut)
    base_params = {
        "min_area": 300,
        "min_width": 40,
        "min_height": 15,
        "max_aspect_ratio": 20,
        "min_yellow_ratio": 0.35,
        "expand_x": 10,
        "expand_y": 5
    }
    
    # Charger les paramètres sauvegardés si disponibles
    saved_params = load_saved_parameters()
    if saved_params:
        print("📂 Paramètres sauvegardés trouvés, les charger? (o/n)")
        if input().lower().startswith('o'):
            base_params.update(saved_params)
            print("✅ Paramètres chargés")
    
    while True:
        print("\nOPTIONS DISPONIBLES:")
        print("1. Test avec paramètres actuels")
        print("2. Réduire la précision (détecter plus)")
        print("3. Augmenter la précision (détecter moins)")
        print("4. Ajustement manuel des paramètres")
        print("5. Test avec paramètres optimaux pour Kindle")
        print("6. Sauvegarder les paramètres actuels")
        print("7. Afficher les paramètres actuels")
        print("8. Quitter")
        
        choice = input("\nVotre choix (1-8): ").strip()
        
        if choice == "1":
            print("\n🔍 TEST AVEC PARAMÈTRES ACTUELS")
            print("-" * 30)
            highlights = test_with_parameters(**base_params)
            
        elif choice == "2":
            print("\n📉 RÉDUCTION DE LA PRÉCISION (détecter plus)")
            print("-" * 40)
            relaxed_params = base_params.copy()
            relaxed_params.update({
                "min_area": max(100, base_params["min_area"] - 100),
                "min_width": max(20, base_params["min_width"] - 10),
                "min_height": max(10, base_params["min_height"] - 5),
                "min_yellow_ratio": max(0.15, base_params["min_yellow_ratio"] - 0.1),
                "max_aspect_ratio": base_params["max_aspect_ratio"] + 5
            })
            highlights = test_with_parameters(**relaxed_params)
            
            if input("\nConserver ces paramètres? (o/n): ").lower().startswith('o'):
                base_params = relaxed_params
                print("✅ Paramètres mis à jour")
        
        elif choice == "3":
            print("\n📈 AUGMENTATION DE LA PRÉCISION (détecter moins)")
            print("-" * 42)
            strict_params = base_params.copy()
            strict_params.update({
                "min_area": base_params["min_area"] + 100,
                "min_width": base_params["min_width"] + 10,
                "min_height": base_params["min_height"] + 5,
                "min_yellow_ratio": min(0.8, base_params["min_yellow_ratio"] + 0.1),
                "max_aspect_ratio": max(5, base_params["max_aspect_ratio"] - 5)
            })
            highlights = test_with_parameters(**strict_params)
            
            if input("\nConserver ces paramètres? (o/n): ").lower().startswith('o'):
                base_params = strict_params
                print("✅ Paramètres mis à jour")
        
        elif choice == "4":
            print("\n⚙️  AJUSTEMENT MANUEL DES PARAMÈTRES")
            print("-" * 35)
            
            for param, current_value in base_params.items():
                new_value = input(f"{param} (actuel: {current_value}): ").strip()
                if new_value:
                    try:
                        if isinstance(current_value, int):
                            base_params[param] = int(new_value)
                        else:
                            base_params[param] = float(new_value)
                    except ValueError:
                        print(f"❌ Valeur invalide pour {param}, conservé: {current_value}")
            
            highlights = test_with_parameters(**base_params)
        
        elif choice == "5":
            print("\n🎯 PARAMÈTRES OPTIMAUX POUR KINDLE")
            print("-" * 35)
            kindle_optimal = {
                "min_area": 250,
                "min_width": 35,
                "min_height": 12,
                "max_aspect_ratio": 25,
                "min_yellow_ratio": 0.4,
                "expand_x": 8,
                "expand_y": 4
            }
            highlights = test_with_parameters(**kindle_optimal)
            
            if input("\nConserver ces paramètres optimaux? (o/n): ").lower().startswith('o'):
                base_params = kindle_optimal
                print("✅ Paramètres optimaux appliqués")
        
        elif choice == "6":
            num_highlights = int(input("Nombre de surlignements correctement détectés: ") or "0")
            save_best_parameters(base_params, num_highlights)
        
        elif choice == "7":
            print("\n📋 PARAMÈTRES ACTUELS")
            print("-" * 20)
            for param, value in base_params.items():
                print(f"  {param}: {value}")
        
        elif choice == "8":
            print("👋 Calibration terminée")
            break
        
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()