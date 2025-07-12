"""
Script de lancement rapide
"""
import subprocess
import sys

def main():
    """Lance l'application avec Poetry."""
    try:
        # Lancer avec poetry
        subprocess.run([sys.executable, "-m", "poetry", "run", "python", "main.py"])
    except KeyboardInterrupt:
        print("\nApplication fermée.")
    except Exception as e:
        print(f"Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")

if __name__ == "__main__":
    main()