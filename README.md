# AllamBik v3.0

**Extracteur de surlignements Kindle avec détection automatique des pages**

Outil d'extraction automatique des highlights Kindle utilisant l'OCR avancé, une interface graphique professionnelle et un système de détection automatique du nombre de pages.

## 🆕 Nouveautés v3.0

### Détection automatique du nombre de pages
- **Comptage intelligent** : Parcourt automatiquement le livre pour déterminer le nombre exact de pages
- **Bouton dédié** : "DÉTECTER NOMBRE DE PAGES" orange dans l'interface
- **Utilisation automatique** : Le nombre détecté est automatiquement utilisé lors de l'extraction
- **Fiabilité** : Détection par hash MD5 pour identifier la fin du livre

## Fonctionnalités principales

### Détection et extraction intelligente
- **🆕 Détection automatique des pages** : Plus besoin d'entrer manuellement le nombre de pages
- **OCR deux phases** : Détection automatique + extraction précise des surlignements
- **Zone de scan personnalisable** : Définition manuelle de la zone d'extraction
- **Extraction ciblée** : UNIQUEMENT les surlignements jaunes (pas tout le texte)
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
│   └── use_cases/
│       ├── extract_highlights_use_case.py
│       └── auto_page_detector.py  # 🆕 Détecteur de pages
├── infrastructure/       # OCR, I/O, dépendances
│   ├── ocr/             # Tesseract adapter
│   ├── kindle/          # PyAutoGUI controller
│   └── persistence/     # Sauvegarde JSON
└── presentation/         # Interface utilisateur
    └── gui/             # Interface graphique
        ├── views/       # Fenêtres principales
        ├── components/  # Composants réutilisables
        └── viewmodels/  # Logique de présentation
```

## Installation

### Prérequis
- **Python 3.8+** (testé avec 3.13)
- **Poetry** (gestionnaire de dépendances)
- **Tesseract OCR** installé dans `C:\Program Files\Tesseract-OCR\`
- **Kindle pour PC** en mode plein écran

### Setup
```bash
# Cloner le repository
git clone https://github.com/HelloDave666/AllamBik.git
cd AllamBik

# Installer les dépendances
poetry install

# Lancer l'application
poetry run python main.py
```

## Utilisation

### 1. Configuration initiale
1. Lancer l'application avec `poetry run python main.py`
2. Ouvrir Kindle pour PC avec un livre contenant des surlignements jaunes
3. Définir la zone de scan avec le bouton "DÉFINIR ZONE DE SCAN"
4. Placer le rectangle sur la zone de texte du livre

### 2. Détection automatique des pages (🆕)
1. Cliquer sur le bouton orange **"DÉTECTER NOMBRE DE PAGES"**
2. Confirmer dans la boîte de dialogue
3. L'application parcourt automatiquement le livre
4. Le nombre de pages s'affiche sur le bouton (ex: "✓ 161 PAGES")

### 3. Extraction
1. Cliquer "DÉMARRER EXTRACTION"
2. Si détection effectuée : l'extraction démarre automatiquement
3. Sinon : entrer manuellement le nombre de pages
4. Progression en temps réel affichée
5. Les surlignements apparaissent dans la liste

### 4. Gestion des highlights
- **Sélection** : Clic simple sur une fiche
- **Édition** : Modification directe dans le panneau droit
- **Recherche** : Tapez dans la barre de recherche
- **Sauvegarde** : Automatique (Entrée ou changement focus)
- **Annulation** : Ctrl+Z dans tous les champs

### 5. Export
1. Cliquer "EXPORTER WORD"
2. Choisir l'emplacement de sauvegarde
3. Document Word généré avec tous les highlights

## Résolution de problèmes

### ❌ Module customtkinter non trouvé
```bash
# Réinstaller les dépendances
cd D:\AllamBik
poetry install
poetry run python main.py
```

### ❌ Détecteur de pages non configuré
Si le message apparaît après clic sur le bouton :
1. Redémarrer l'application
2. Vérifier dans la console : "✓ Détecteur de pages configuré"
3. Si absent, vérifier que `auto_page_detector.py` existe

### ❌ La détection s'arrête au milieu
**Comportement normal** : Le détecteur compte jusqu'à la fin puis revient au début. Il peut s'arrêter au milieu lors du retour mais le compte total est correct.

### 🔧 Vérifications environnement
```bash
# Version Poetry
poetry --version

# Environnement actuel
poetry env info

# Dépendances installées
poetry show

# Vérifier Tesseract
tesseract --version
```

## Développement

### Commandes utiles
```bash
# Tests
poetry run pytest

# Formatage du code
poetry run black .

# Vérification qualité
poetry run ruff check .

# Lancement en mode debug
poetry run python main.py --debug
```

### Technologies utilisées
- **Interface** : CustomTkinter 5.2.2 (moderne, responsive)
- **OCR** : Tesseract 5.x + OpenCV (extraction précise)
- **Automation** : PyAutoGUI (contrôle Kindle)
- **Export** : python-docx (format professionnel)
- **Architecture** : Clean Architecture pattern
- **Gestion deps** : Poetry 1.8+ (environnement isolé)
- **Python** : 3.8+ (testé avec 3.13)

## Performances

- **Vitesse détection** : ~1-2 secondes par page
- **Vitesse extraction** : 10-20 pages/minute
- **Précision OCR** : 85-95% pour les surlignements
- **Mémoire** : <200MB pour 500+ highlights
- **Compatibilité** : Windows 10/11 (principal), macOS, Linux

## Changelog

### v3.0.0 (30 août 2025)
- 🆕 Détection automatique du nombre de pages
- 🆕 Extraction exclusive des surlignements jaunes
- 🔧 Correction du stockage de `kindle_controller`
- 🔧 Amélioration de la connexion entre composants
- 📝 Documentation complète mise à jour

### v2.0.0
- Interface moderne CustomTkinter
- Système d'édition en temps réel
- Export Word professionnel

### v1.0.0
- Version initiale
- OCR basique
- Interface simple

## Contribution

Les contributions sont bienvenues ! Merci de :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Auteur

**HelloDave666** - [GitHub](https://github.com/HelloDave666)

## Remerciements

- **Catherine Le Hir** pour l'aide apportée pendant la rédaction et la correction du manuscrit
- **Groupe de recherche sur l'explicitation (GREX)** depuis 1991
- Tous les membres du GREX pour leur soutien continu

---

**AllamBik v3.0** - Extraction de highlights Kindle professionnelle avec détection automatique