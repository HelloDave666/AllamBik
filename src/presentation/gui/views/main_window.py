"""
Fenêtre principale - Version corrigée sans bugs d'ascenseur
"""
import customtkinter as ctk
import asyncio
from typing import Optional, Tuple, Dict, Any
import threading
import json
import os
from datetime import datetime
from tkinter import filedialog, messagebox

# Import conditionnel pour Word
try:
    from docx import Document
    from docx.shared import Inches
    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False
    print("⚠️ python-docx non disponible. Export Word désactivé.")

from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel, ViewState, HighlightViewModel
from src.presentation.gui.components.progress_circle import ProgressCircle
from src.presentation.gui.components.highlight_card import HighlightGrid
from src.presentation.gui.components.zone_picker import ZonePickerButton


class IntegratedEditPanel(ctk.CTkFrame):
    """Panneau d'édition intégré en bas de l'interface."""
    
    def __init__(self, parent, on_save=None, on_cancel=None):
        super().__init__(parent)
        self.configure(fg_color="#2a2a2a", corner_radius=10)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.current_highlight = None
        
        self._create_content()
        self.pack_forget()  # Caché par défaut
    
    def _create_content(self):
        """Crée le contenu du panneau d'édition."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="ÉDITION DU HIGHLIGHT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(side="left")
        
        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#ff4444",
            command=self._cancel_edit
        )
        close_btn.pack(side="right")
        
        # Corps principal avec 2 colonnes
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Colonne gauche - Informations
        left_column = ctk.CTkFrame(main_frame, fg_color="#3a3a3a")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Page et confiance
        info_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=15)
        
        self.page_label = ctk.CTkLabel(
            info_frame,
            text="Page: -",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.page_label.pack(side="left")
        
        self.confidence_label = ctk.CTkLabel(
            info_frame,
            text="Confiance: -",
            font=ctk.CTkFont(size=12)
        )
        self.confidence_label.pack(side="right")
        
        # Champ nom personnalisé
        name_label = ctk.CTkLabel(
            left_column,
            text="Nom personnalisé:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x", padx=15, pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            left_column,
            placeholder_text="Nom pour ce highlight...",
            font=ctk.CTkFont(size=11)
        )
        self.name_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        copy_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Copier",
            command=self._copy_text,
            fg_color="#0078d4",
            hover_color="#106ebe",
            height=35
        )
        copy_btn.pack(fill="x", pady=(0, 5))
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Sauvegarder",
            command=self._save_changes,
            fg_color="#00aa44",
            hover_color="#008833",
            height=35
        )
        save_btn.pack(fill="x", pady=(0, 5))
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Annuler",
            command=self._cancel_edit,
            fg_color="#666666",
            hover_color="#777777",
            height=35
        )
        cancel_btn.pack(fill="x")
        
        # Colonne droite - Texte
        right_column = ctk.CTkFrame(main_frame, fg_color="#3a3a3a")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        text_label = ctk.CTkLabel(
            right_column,
            text="Texte extrait:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        text_label.pack(fill="x", padx=15, pady=(15, 5))
        
        self.text_editor = ctk.CTkTextbox(
            right_column,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.text_editor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def show_highlight(self, highlight_data):
        """Affiche un highlight pour édition."""
        self.current_highlight = highlight_data.copy()
        
        # Remplir les champs
        page = highlight_data.get('page', '?')
        confidence = highlight_data.get('confidence', 0)
        
        self.page_label.configure(text=f"Page: {page}")
        self.confidence_label.configure(text=f"Confiance: {confidence:.1f}%")
        
        # Nom personnalisé
        custom_name = highlight_data.get('custom_name', '')
        self.name_entry.delete(0, 'end')
        if custom_name:
            self.name_entry.insert(0, custom_name)
        
        # Texte
        text = highlight_data.get('text', '')
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text)
        
        # Afficher le panneau
        self.pack(fill="x", pady=(10, 0))
    
    def hide_panel(self):
        """Cache le panneau d'édition."""
        self.pack_forget()
        self.current_highlight = None
    
    def _copy_text(self):
        """Copie le texte vers le clipboard."""
        text = self.text_editor.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        
        # Feedback
        original_text = self.text_editor.get("1.0", "end-1c")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "✅ Copié dans le presse-papiers!")
        self.after(1000, lambda: (
            self.text_editor.delete("1.0", "end"),
            self.text_editor.insert("1.0", original_text)
        ))
    
    def _save_changes(self):
        """Sauvegarde les modifications."""
        if not self.current_highlight:
            return
        
        # Récupérer les nouvelles valeurs
        new_text = self.text_editor.get("1.0", "end-1c")
        new_name = self.name_entry.get().strip()
        
        # Mettre à jour les données
        self.current_highlight['text'] = new_text
        if new_name:
            self.current_highlight['custom_name'] = new_name
        elif 'custom_name' in self.current_highlight:
            del self.current_highlight['custom_name']
        
        # Marquer comme modifié
        self.current_highlight['modified'] = True
        self.current_highlight['modified_date'] = datetime.now().isoformat()
        
        # Callback de sauvegarde
        if self.on_save:
            self.on_save(self.current_highlight)
        
        self.hide_panel()
    
    def _cancel_edit(self):
        """Annule l'édition."""
        if self.on_cancel:
            self.on_cancel()
        self.hide_panel()


class MainWindow(ctk.CTk):
    """
    Fenêtre principale de l'application Alambik v3 - Version corrigée.
    """
    
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        
        self.viewmodel = viewmodel
        self.async_loop = None
        
        # Variables d'état (AVANT _create_ui())
        self.view_mode = "grid"  # "grid" (2 col) ou "list" (1 col)
        self.current_search = ""
        self.extraction_file_path = None  # Chemin vers le fichier d'extraction
        
        # Pour gérer les mises à jour
        self._update_queue = []
        
        self._setup_window()
        self._create_ui()
        self._bind_viewmodel()
        self._start_update_loop()
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
        self.title("Alambik v3.0 - Extracteur de Highlights Kindle")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2a2a2a',
            'bg_tertiary': '#3a3a3a',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'text_muted': '#808080',
            'accent': '#00aaff',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'error': '#ff4444'
        }
        
        self.configure(fg_color=self.colors['bg_primary'])
    
    def _create_ui(self):
        """Crée l'interface utilisateur."""
        # Container principal
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configuration de la grille
        main_container.grid_columnconfigure(0, weight=1, minsize=400)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Panneau gauche (contrôles)
        self._create_left_panel(main_container)
        
        # Panneau droit (highlights + édition)
        self._create_right_panel(main_container)
    
    def _create_left_panel(self, parent):
        """Crée le panneau gauche avec contrôles et progression."""
        left_panel = ctk.CTkFrame(parent, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header
        header_frame = ctk.CTkFrame(
            left_panel,
            fg_color=self.colors['bg_secondary'],
            height=60,
            corner_radius=10
        )
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="ALAMBIK v3.0",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.pack(expand=True)
        
        # Section Progression
        progress_section = self._create_section(left_panel, "PROGRESSION")
        self.progress_circle = ProgressCircle(progress_section)
        self.progress_circle.pack(pady=10)
        
        self.progress_label = ctk.CTkLabel(
            progress_section,
            text="Prêt pour l'extraction",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.progress_label.pack(pady=(0, 15))
        
        # Section Contrôles
        controls_section = self._create_section(left_panel, "CONTRÔLES")
        
        # Bouton Zone Picker
        self.zone_picker_button = ZonePickerButton(
            controls_section,
            on_zone_selected=self._on_zone_selected,
            text="DÉFINIR ZONE DE SCAN",
            fg_color=self.colors['warning'],
            hover_color="#ff8800"
        )
        self.zone_picker_button.pack(fill="x", padx=20, pady=(10, 5))
        
        # Bouton Démarrer
        self.start_button = ctk.CTkButton(
            controls_section,
            text="DÉMARRER EXTRACTION",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=self.colors['accent'],
            hover_color="#0088cc",
            command=self._on_start_clicked
        )
        self.start_button.pack(fill="x", padx=20, pady=(5, 5))
        
        # Bouton Arrêter (pleine largeur, plus de Valider)
        self.stop_button = ctk.CTkButton(
            controls_section,
            text="ARRÊTER EXTRACTION",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['error'],
            state="disabled",
            command=self._on_stop_clicked
        )
        self.stop_button.pack(fill="x", padx=20, pady=(5, 15))
        
        # Section Statistiques
        stats_section = self._create_section(left_panel, "STATISTIQUES")
        
        stats_frame = ctk.CTkFrame(stats_section, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        # Créer les stats
        self.stats_labels = {}
        stats = [
            ("pages_scanned", "Pages scannées"),
            ("pages_with_content", "Pages avec contenu"),
            ("highlights_count", "Highlights extraits")
        ]
        
        for i, (key, label) in enumerate(stats):
            stat_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_container.pack(fill="x", pady=5)
            
            label_widget = ctk.CTkLabel(
                stat_container,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color=self.colors['text_muted'],
                anchor="w"
            )
            label_widget.pack(side="left", fill="x", expand=True)
            
            value_widget = ctk.CTkLabel(
                stat_container,
                text="0",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.colors['text_primary'],
                anchor="e"
            )
            value_widget.pack(side="right")
            
            self.stats_labels[key] = value_widget
        
        # Section Actions Rapides
        actions_section = self._create_section(left_panel, "ACTIONS RAPIDES")
        
        # Bouton Exporter Word (TOUJOURS visible)
        self.export_word_button = ctk.CTkButton(
            actions_section,
            text="📄 EXPORTER WORD",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=self._on_export_word_clicked
        )
        self.export_word_button.pack(fill="x", padx=20, pady=(10, 5))
        
        # Bouton Exporter TXT
        self.export_txt_button = ctk.CTkButton(
            actions_section,
            text="📝 EXPORTER TXT",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=self._on_export_txt_clicked
        )
        self.export_txt_button.pack(fill="x", padx=20, pady=(5, 5))
        
        # Bouton Effacer Tout
        self.clear_button = ctk.CTkButton(
            actions_section,
            text="🗑️ EFFACER TOUT",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color="#663333",
            hover_color="#774444",
            command=self._on_clear_all_clicked
        )
        self.clear_button.pack(fill="x", padx=20, pady=(5, 15))
    
    def _create_right_panel(self, parent):
        """Crée le panneau droit avec highlights et panneau d'édition."""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configuration - highlights en haut, édition en bas si nécessaire
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Container pour highlights et édition
        highlights_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        highlights_container.grid(row=0, column=0, sticky="nsew")
        
        # Section Highlights
        highlights_section = self._create_section_frame(highlights_container, "HIGHLIGHTS EXTRAITS")
        highlights_section.pack(fill="both", expand=True)
        
        # Header avec compteur et contrôles SIMPLIFIÉS
        header_frame = ctk.CTkFrame(highlights_section, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Titre avec compteur
        self.highlights_title = ctk.CTkLabel(
            header_frame,
            text="HIGHLIGHTS EXTRAITS (0)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary']
        )
        self.highlights_title.pack(side="left")
        
        # Contrôles simplifiés (SEULEMENT 2 boutons)
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right")
        
        # Bouton mode liste (1 colonne large)
        self.list_view_button = ctk.CTkButton(
            controls_frame,
            text="☰",  # Icône sandwich/hamburger
            width=35,
            height=35,
            font=ctk.CTkFont(size=16),
            fg_color="#4a4a4a" if self.view_mode != "list" else self.colors['accent'],
            hover_color="#5a5a5a",
            command=self._set_list_view
        )
        self.list_view_button.pack(side="right", padx=(5, 0))
        
        # Bouton mode grille (2 colonnes)
        self.grid_view_button = ctk.CTkButton(
            controls_frame,
            text="⊞",  # Icône grille
            width=35,
            height=35,
            font=ctk.CTkFont(size=16),
            fg_color="#4a4a4a" if self.view_mode != "grid" else self.colors['accent'],
            hover_color="#5a5a5a",
            command=self._set_grid_view
        )
        self.grid_view_button.pack(side="right", padx=(5, 0))
        
        # Zone de recherche
        search_frame = ctk.CTkFrame(highlights_section, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Rechercher dans les highlights...",
            font=ctk.CTkFont(size=11),
            height=30
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # Bouton effacer recherche
        clear_search_btn = ctk.CTkButton(
            search_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#444444",
            command=self._clear_search
        )
        clear_search_btn.pack(side="right")
        
        # Grille de highlights
        self.highlights_grid = HighlightGrid(
            highlights_section,
            columns=2,  # Démarre en mode grille
            fg_color="transparent",
            on_edit_requested=self._on_edit_requested
        )
        self.highlights_grid.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Panneau d'édition intégré (caché par défaut)
        self.edit_panel = IntegratedEditPanel(
            highlights_container,
            on_save=self._on_edit_saved,
            on_cancel=self._on_edit_cancelled
        )
    
    def _create_section(self, parent, title: str) -> ctk.CTkFrame:
        """Crée une section avec titre."""
        section = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_secondary'],
            corner_radius=10
        )
        section.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.pack(pady=(15, 5))
        
        return section
    
    def _create_section_frame(self, parent, title: str) -> ctk.CTkFrame:
        """Crée une section frame pour la grille."""
        section = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_secondary'],
            corner_radius=10
        )
        return section
    
    def _bind_viewmodel(self):
        """Lie le ViewModel à la vue."""
        self.viewmodel.on_state_changed = self._on_state_changed
        self.viewmodel.on_progress_changed = self._on_progress_changed
        self.viewmodel.on_highlight_added = self._on_highlight_added
    
    def _start_update_loop(self):
        """Démarre la boucle de mise à jour UI."""
        def update_ui():
            try:
                for update_func in self._update_queue[:]:
                    update_func()
                    self._update_queue.remove(update_func)
            except:
                pass
            self.after(100, update_ui)
        
        self.after(100, update_ui)
    
    def _schedule_update(self, func):
        """Planifie une mise à jour UI thread-safe."""
        self._update_queue.append(func)
    
    # Gestion des vues SIMPLIFIÉE
    
    def _set_grid_view(self):
        """Active le mode grille (2 colonnes)."""
        if self.view_mode != "grid":
            self.view_mode = "grid"
            self._update_view_buttons()
            self._recreate_grid(2)
    
    def _set_list_view(self):
        """Active le mode liste (1 colonne large)."""
        if self.view_mode != "list":
            self.view_mode = "list"
            self._update_view_buttons()
            self._recreate_grid(1)
    
    def _update_view_buttons(self):
        """Met à jour l'apparence des boutons de vue."""
        # Bouton grille
        grid_color = self.colors['accent'] if self.view_mode == "grid" else "#4a4a4a"
        self.grid_view_button.configure(fg_color=grid_color)
        
        # Bouton liste
        list_color = self.colors['accent'] if self.view_mode == "list" else "#4a4a4a"
        self.list_view_button.configure(fg_color=list_color)
    
    def _recreate_grid(self, columns):
        """Recrée la grille avec le nombre de colonnes spécifié - CORRECTION DEFINITIVE BUG ASCENSEUR."""
        
        # NOUVELLE APPROCHE: Modifier la grille existante au lieu de la détruire
        
        # Sauvegarder les données
        highlights_data = self.highlights_grid.get_highlights_data()
        
        # Supprimer toutes les cartes existantes de la grille
        for card in self.highlights_grid.cards:
            card.destroy()
        
        # Réinitialiser les listes
        self.highlights_grid.cards.clear()
        self.highlights_grid.highlights_data.clear()
        
        # Mettre à jour le nombre de colonnes de la grille existante
        self.highlights_grid.columns = columns
        
        # Reconfigurer les colonnes de la grille existante
        for i in range(columns):
            self.highlights_grid.grid_columnconfigure(i, weight=1, uniform="column")
        
        # Supprimer la configuration des colonnes supplémentaires si on réduit
        if columns < 4:  # Maximum de 4 colonnes possible
            for i in range(columns, 4):
                self.highlights_grid.grid_columnconfigure(i, weight=0, uniform="")
        
        # Forcer la mise à jour du scrollable frame
        self.highlights_grid.update_idletasks()
        
        # Attendre un cycle d'événements puis restaurer les données
        self.after_idle(lambda: self._restore_highlights_data(highlights_data))
    
    def _restore_highlights_data(self, highlights_data):
        """Restaure les données des highlights dans la grille modifiée."""
        # Restaurer toutes les données
        for highlight_data in highlights_data:
            self.highlights_grid.add_highlight(highlight_data)
        
        self._update_highlights_count()
        
        # Forcer la mise à jour complète de l'affichage
        self.highlights_grid.update_idletasks()
        self.update_idletasks()
    
    # Gestion de l'édition intégrée
    
    def _on_edit_requested(self, highlight_data):
        """Callback quand l'édition d'un highlight est demandée."""
        self.edit_panel.show_highlight(highlight_data)
    
    def _on_edit_saved(self, updated_data):
        """Callback quand un highlight est sauvegardé après édition - CORRECTION."""
        # CORRECTION: Debug pour voir quel highlight est sauvegardé
        print(f"🔧 Sauvegarde highlight: Page {updated_data.get('page')}, Nom: {updated_data.get('custom_name', 'Sans nom')}")
        
        # Mettre à jour dans la grille avec gestion d'erreur
        try:
            self.highlights_grid.update_highlight(updated_data)
            
            # Sauvegarder dans le fichier d'extraction
            self._save_to_extraction_file()
            
            print(f"✅ Highlight sauvegardé: {updated_data.get('custom_name', 'Sans nom')}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde highlight: {e}")
            # Essayer de forcer la mise à jour
            self._force_refresh_all_cards()
    
    def _on_edit_cancelled(self):
        """Callback quand l'édition est annulée."""
        print("Édition annulée")
    
    def _force_refresh_all_cards(self):
        """Force le rafraîchissement de toutes les cartes."""
        try:
            for i, (card, data) in enumerate(zip(self.highlights_grid.cards, self.highlights_grid.highlights_data)):
                card.update_data(data)
            print("🔄 Toutes les cartes ont été rafraîchies")
        except Exception as e:
            print(f"❌ Erreur rafraîchissement: {e}")
    
    # Gestion des fichiers
    
    def _save_to_extraction_file(self):
        """Sauvegarde les modifications dans le fichier d'extraction."""
        if not self.extraction_file_path or not os.path.exists(self.extraction_file_path):
            # Trouver ou créer le fichier d'extraction
            self._find_or_create_extraction_file()
        
        if self.extraction_file_path:
            try:
                highlights_data = self.highlights_grid.get_highlights_data()
                
                # Créer le contenu mis à jour
                content = "=== HIGHLIGHTS KINDLE EXTRAITS ===\n"
                content += f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
                content += f"Nombre total: {len(highlights_data)}\n\n"
                
                for i, highlight in enumerate(highlights_data, 1):
                    # Utiliser le nom personnalisé ou le numéro de page
                    title = highlight.get('custom_name', f"Page {highlight.get('page', '?')}")
                    content += f"--- {i}. {title} ---\n"
                    content += f"Page: {highlight.get('page', '?')}\n"
                    content += f"Confiance: {highlight.get('confidence', 0):.1f}%\n"
                    
                    if highlight.get('modified'):
                        content += f"Modifié le: {highlight.get('modified_date', 'N/A')}\n"
                    
                    content += f"\nTexte:\n{highlight.get('text', '')}\n\n"
                    content += "-" * 50 + "\n\n"
                
                # Écrire le fichier
                with open(self.extraction_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fichier d'extraction mis à jour: {self.extraction_file_path}")
                
            except Exception as e:
                print(f"Erreur lors de la sauvegarde: {e}")
    
    def _find_or_create_extraction_file(self):
        """Trouve ou crée le fichier d'extraction."""
        # Chercher dans le dossier extractions
        extractions_dir = "extractions"
        if os.path.exists(extractions_dir):
            # Trouver le fichier le plus récent
            txt_files = [f for f in os.listdir(extractions_dir) if f.endswith('.txt')]
            if txt_files:
                latest_file = max(txt_files, key=lambda f: os.path.getctime(os.path.join(extractions_dir, f)))
                self.extraction_file_path = os.path.join(extractions_dir, latest_file)
                return
        
        # Créer un nouveau fichier
        if not os.path.exists(extractions_dir):
            os.makedirs(extractions_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"highlights_extraits_{timestamp}.txt"
        self.extraction_file_path = os.path.join(extractions_dir, filename)
    
    # Export Word
    
    def _on_export_word_clicked(self):
        """Exporte tous les highlights vers un document Word."""
        # Vérifier la disponibilité de python-docx
        if not WORD_AVAILABLE:
            messagebox.showerror(
                "Export Word indisponible", 
                "La bibliothèque python-docx n'est pas installée.\n\n" +
                "Installez-la avec: poetry add python-docx\n" +
                "Puis redémarrez l'application."
            )
            return
        
        highlights_data = self.highlights_grid.get_highlights_data()
        
        if not highlights_data:
            messagebox.showwarning("Aucun highlight", "Aucun highlight à exporter.")
            return
        
        # Choisir le fichier de destination
        file_path = filedialog.asksaveasfilename(
            title="Exporter vers Word",
            defaultextension=".docx",
            filetypes=[("Documents Word", "*.docx"), ("Tous les fichiers", "*.*")],
            initialname=f"highlights_kindle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        )
        
        if file_path:
            try:
                # Créer le document Word
                doc = Document()
                
                # Titre principal
                title = doc.add_heading('Highlights Kindle Extraits', 0)
                title.alignment = 1  # Centré
                
                # Informations générales
                info_para = doc.add_paragraph()
                info_para.add_run(f"Généré le: ").bold = True
                info_para.add_run(f"{datetime.now().strftime('%d/%m/%Y à %H:%M')}\n")
                info_para.add_run(f"Nombre total: ").bold = True
                info_para.add_run(f"{len(highlights_data)} highlights")
                
                # Ligne de séparation
                doc.add_paragraph("=" * 60)
                
                # Ajouter chaque highlight
                for i, highlight in enumerate(highlights_data, 1):
                    # Titre du highlight
                    title = highlight.get('custom_name', f"Page {highlight.get('page', '?')}")
                    heading = doc.add_heading(f"{i}. {title}", level=2)
                    
                    # Métadonnées
                    meta_para = doc.add_paragraph()
                    meta_para.add_run("Page: ").bold = True
                    meta_para.add_run(f"{highlight.get('page', '?')}    ")
                    meta_para.add_run("Confiance: ").bold = True
                    meta_para.add_run(f"{highlight.get('confidence', 0):.1f}%")
                    
                    if highlight.get('modified'):
                        meta_para.add_run("\nModifié le: ").bold = True
                        meta_para.add_run(highlight.get('modified_date', 'N/A'))
                    
                    # Texte du highlight
                    text_para = doc.add_paragraph()
                    text_para.add_run("Texte: ").bold = True
                    doc.add_paragraph(highlight.get('text', ''))
                    
                    # Séparateur entre highlights
                    if i < len(highlights_data):
                        doc.add_paragraph("-" * 40)
                
                # Sauvegarder
                doc.save(file_path)
                messagebox.showinfo("Export réussi", f"Document Word créé:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Erreur lors de l'export Word:\n{str(e)}")
    
    def _on_export_txt_clicked(self):
        """Exporte tous les highlights vers un fichier TXT."""
        highlights_data = self.highlights_grid.get_highlights_data()
        
        if not highlights_data:
            messagebox.showwarning("Aucun highlight", "Aucun highlight à exporter.")
            return
        
        # Choisir le fichier de destination
        file_path = filedialog.asksaveasfilename(
            title="Exporter vers TXT",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialname=f"highlights_kindle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                content = "=== HIGHLIGHTS KINDLE EXTRAITS ===\n"
                content += f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
                content += f"Nombre total: {len(highlights_data)}\n\n"
                
                for i, highlight in enumerate(highlights_data, 1):
                    title = highlight.get('custom_name', f"Page {highlight.get('page', '?')}")
                    content += f"--- {i}. {title} ---\n"
                    content += f"Page: {highlight.get('page', '?')}\n"
                    content += f"Confiance: {highlight.get('confidence', 0):.1f}%\n"
                    
                    if highlight.get('modified'):
                        content += f"Modifié le: {highlight.get('modified_date', 'N/A')}\n"
                    
                    content += f"\nTexte:\n{highlight.get('text', '')}\n\n"
                    content += "-" * 50 + "\n\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("Export réussi", f"Fichier TXT créé:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Erreur lors de l'export:\n{str(e)}")
    
    # Autres handlers
    
    def _on_search_changed(self, event):
        """Gère les changements de recherche."""
        search_text = self.search_entry.get().lower()
        self.current_search = search_text
        # TODO: Implémenter le filtrage réel
        self._update_highlights_count()
    
    def _clear_search(self):
        """Efface la recherche."""
        self.search_entry.delete(0, "end")
        self.current_search = ""
        # TODO: Mettre à jour le filtrage
        self._update_highlights_count()
    
    def _on_clear_all_clicked(self):
        """Efface tous les highlights après confirmation."""
        if len(self.highlights_grid.get_highlights_data()) > 0:
            if messagebox.askyesno("Confirmation", 
                                   "Êtes-vous sûr de vouloir effacer TOUS les highlights?\n\n" +
                                   "Cette action est irréversible."):
                self.highlights_grid.clear()
                self._update_highlights_count()
                # Mettre à jour le fichier d'extraction
                self._save_to_extraction_file()
    
    def _update_highlights_count(self):
        """Met à jour le compteur de highlights."""
        count = self.highlights_grid.get_count()
        self.highlights_title.configure(text=f"HIGHLIGHTS EXTRAITS ({count})")
    
    # Handlers existants
    
    def _on_zone_selected(self, zone: Tuple[int, int, int, int]):
        """Callback quand une zone est sélectionnée."""
        if hasattr(self.viewmodel, 'custom_scan_zone'):
            self.viewmodel.custom_scan_zone = zone
        else:
            self.viewmodel.custom_scan_zone = zone
        
        x, y, w, h = zone
        print(f"Zone de scan définie: {w}x{h} pixels à la position ({x},{y})")
    
    def _on_start_clicked(self):
        """Gère le clic sur Démarrer."""
        dialog = ctk.CTkInputDialog(
            text="Nombre total de pages du livre:",
            title="Configuration"
        )
        pages_str = dialog.get_input()
        
        if pages_str:
            try:
                total_pages = int(pages_str)
                if total_pages > 0:
                    if self.async_loop:
                        asyncio.run_coroutine_threadsafe(
                            self.viewmodel.start_extraction_command(total_pages),
                            self.async_loop
                        )
            except ValueError:
                pass
    
    def _on_stop_clicked(self):
        """Gère le clic sur Arrêter."""
        if self.async_loop:
            asyncio.run_coroutine_threadsafe(
                self.viewmodel.stop_extraction_command(),
                self.async_loop
            )
    
    # Callbacks du ViewModel
    
    def _on_state_changed(self, state: ViewState):
        """Met à jour l'UI selon l'état."""
        def update():
            self.start_button.configure(
                state="normal" if self.viewmodel.can_start else "disabled"
            )
            self.stop_button.configure(
                state="normal" if self.viewmodel.can_stop else "disabled"
            )
            # Plus de bouton validate
            
            # Mettre à jour les boutons d'actions
            has_highlights = self.highlights_grid.get_count() > 0
            
            self.export_word_button.configure(
                state="normal" if has_highlights else "disabled"
            )
            self.export_txt_button.configure(
                state="normal" if has_highlights else "disabled"
            )
            self.clear_button.configure(
                state="normal" if has_highlights else "disabled"
            )
            
            if state == ViewState.ERROR:
                self.progress_circle.configure(fg_color=self.colors['error'])
        
        self._schedule_update(update)
    
    def _on_progress_changed(self):
        """Met à jour la progression."""
        def update():
            self.progress_circle.update_progress(
                current=self.viewmodel.current_progress,
                phase1=self.viewmodel.phase1_progress,
                phase2=self.viewmodel.phase2_progress
            )
            self.progress_label.configure(text=self.viewmodel.progress_message)
            
            # Mettre à jour les stats
            self.stats_labels["pages_scanned"].configure(
                text=str(self.viewmodel.pages_scanned)
            )
            self.stats_labels["pages_with_content"].configure(
                text=str(self.viewmodel.pages_with_content)
            )
            self.stats_labels["highlights_count"].configure(
                text=str(self.viewmodel.highlights_count)
            )
        
        self._schedule_update(update)
    
    def _on_highlight_added(self, highlight: HighlightViewModel):
        """Ajoute un highlight à la grille."""
        def update():
            highlight_data = {
                'page': highlight.page,
                'text': highlight.text,
                'confidence': highlight.confidence,
                'timestamp': datetime.now().isoformat(),
                'source_image': None,
                'coordinates': None,
                'validated': False,
                'modified': False
            }
            
            self.highlights_grid.add_highlight(highlight_data)
            self._update_highlights_count()
            
            # Sauvegarder automatiquement
            self._save_to_extraction_file()
        
        self._schedule_update(update)