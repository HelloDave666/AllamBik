# AllamBik v3.0

**Extracteur de surlignements avec interface moderne**

Outil d'extraction automatique des highlights utilisant l'OCR avancé et une interface graphique professionnelle pour la gestion et l'export des notes de lecture.

## Fonctionnalités principales

### Extraction intelligente
- **OCR deux phases** : Détection automatique + extraction précise
- **Zone de scan personnalisable** : Définition manuelle de la zone d'extraction
- **Confidence scoring** : Évaluation automatique de la qualité d'extraction
- **Support multi-pages** : Traitement batch avec progression en temps réel

### Gestion des highlights
- **Édition en temps réel** : Modification directe des textes extraits
- **Noms personnalisés** : Attribution de titres custom aux extraits
- **Sauvegarde automatique** : Entrée + changement focus + changement fiche
- **Annulation intelligente** : Ctrl+Z fonctionnel avec historique 50 niveaux
- **Recherche temps réel** : Filtrage instantané avec surbrillance

### Interface moderne
- **Design dark professionnel** : Interface épurée sans distractions
- **États visuels multiples** : Normal/Hover/Sélectionné/Recherche
- **Sélection persistante** : Surbrillance verte maintenue
- **Modes d'affichage** : Grille (2 colonnes) ou Liste (1 colonne)
- **Panneau d'édition intégré** : Workflow fluide sans popups

### Export professionnel
- **Format Word (.docx)** : Compatible Zotero, Obsidian, Notion
- **Métadonnées complètes** : Page, confiance, dates de modification
- **Formatage structuré** : Titres, citations, tags automatiques

## Architecture

**Clean Architecture / Hexagonal pattern** avec séparation claire des responsabilités :

```
src/
├── domain/               # Logique métier
├── application/          # Use cases et services
├── infrastructure/       # OCR, I/O, dépendances
└── presentation/         # Interface utilisateur
    ├── gui/             # Interface graphique
    │   ├── views/       # Fenêtres principales
    │   ├── components/  # Composants réutilisables
    │   └── viewmodels/  # Logique de présentation
    └── api/             # API REST (futur)
```

## Installation

### Prérequis
- **Python 3.8+**
- **Poetry** (gestionnaire de dépendances)

### Setup
```bash
# Cloner le repository
git clone https://github.com/HelloDave666/AllamBik.git
cd AllamBik

# Installer les dépendances
poetry install

# Installer la dépendance pour l'export Word
poetry add python-docx

# Lancer l'application
poetry run python main.py
```

## Résolution de problèmes

### ❌ Erreur ModuleNotFoundError customtkinter

**Symptôme :**
```bash
PS D:\alambik-v3> poetry run python main.py
ModuleNotFoundError: No module named 'customtkinter'
```

**Cause :** Environnement Poetry non initialisé (après redémarrage système, pause longue, etc.)

**✅ Solution :**
```bash
# Aller dans le répertoire du projet
cd D:\alambik-v3

# Réinstaller les dépendances
poetry install

# Lancer l'application
poetry run python main.py
```

**Solutions alternatives si `poetry install` échoue :**
```bash
# Recréer l'environnement Poetry
poetry env remove python
poetry install

# Vérifier l'installation
poetry show customtkinter

# Mode développement (optionnel)
poetry install --with dev
```

### 🔧 Vérifications environnement
```bash
# Vérifier Poetry installé
poetry --version

# Voir l'environnement actuel
poetry env info

# Lister les dépendances installées
poetry show
```

**Note :** Ce problème est courant lors de la reprise du projet après une pause. Le `pyproject.toml` et `poetry.lock` contiennent bien toutes les dépendances, il suffit de les réinstaller.

## Utilisation

### Configuration initiale
- Lancer l'application
- Définir la zone de scan avec le bouton "DÉFINIR ZONE DE SCAN"
- Ouvrir le document en mode plein écran

### Extraction
- Cliquer "DÉMARRER EXTRACTION"
- Entrer le nombre total de pages
- L'extraction se lance automatiquement
- Progression en temps réel affichée

### Gestion des highlights
- **Sélection** : Clic simple sur une fiche
- **Édition** : Modification directe dans le panneau droit
- **Recherche** : Tapez dans la barre de recherche
- **Sauvegarde** : Automatique (Entrée ou changement focus)
- **Annulation** : Ctrl+Z dans tous les champs

### Export
- Cliquer "EXPORTER WORD"
- Choisir l'emplacement de sauvegarde
- Document Word généré prêt pour Zotero

## Développement

### Commandes utiles
```bash
# Tests
poetry run pytest
poetry run black .
poetry run ruff check .

# Lancement développement
poetry run python main.py
```

### Technologies utilisées
- **Interface** : CustomTkinter (moderne, responsive)
- **OCR** : OpenCV + Tesseract (extraction précise)
- **Export** : python-docx (format professionnel)
- **Architecture** : Clean Architecture pattern
- **Gestion deps** : Poetry (environnement isolé)

## Performances

- **Vitesse extraction** : 10-20 pages/minute (selon complexité)
- **Précision OCR** : 85-95% confidence moyenne
- **Mémoire** : <200MB pour 500+ highlights
- **Compatibilité** : Windows 10/11, macOS, Linux

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

**AllamBik v3.0** - Extraction de highlights professionnelle