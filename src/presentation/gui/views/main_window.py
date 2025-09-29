"""
Fenetre principale - Version corrigee avec pagination et selection multiple fonctionnelle
"""
import customtkinter as ctk
import asyncio
from typing import Optional, Tuple, Dict, Any
import threading
import json
import os
from datetime import datetime
from tkinter import filedialog, messagebox
import tkinter as tk

# Import conditionnel pour Word
try:
    from docx import Document
    from docx.shared import Inches
    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False
    print("ATTENTION: python-docx non disponible. Export Word desactive.")

from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel, ViewState, HighlightViewModel
from src.presentation.gui.components.progress_circle import ProgressCircle
from src.presentation.gui.components.highlight_card import HighlightGrid
from src.presentation.gui.components.zone_picker import ZonePickerButton
from src.presentation.gui.components.pagination_controller import PaginationController, PaginationBar


class IntegratedEditPanel(ctk.CTkFrame):
    """Panneau d'edition integre en bas de l'interface."""
    
    def __init__(self, parent, main_window=None, on_save=None, on_cancel=None, on_delete=None):
        super().__init__(parent)
        self.configure(fg_color="#2a2a2a", corner_radius=10)
        self.main_window = main_window  # Reference directe a MainWindow
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.on_delete = on_delete
        self.current_highlight = None
        
        # Variables pour l'etat initial
        self.initial_text = ""
        self.initial_name = ""
        
        self._create_content()
        
        # Variables pour l'historique d'annulation
        self._text_history = []
        self._name_history = []
        self._max_history = 50
    
    def _on_key_press_name(self, event):
        """Sauvegarde dans l'historique avant modification du nom."""
        if event.keysym not in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 
                               'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab']:
            current_value = self.name_entry.get()
            if not self._name_history or (self._name_history and self._name_history[-1] != current_value):
                if len(self._name_history) >= self._max_history:
                    self._name_history.pop(0)
                self._name_history.append(current_value)
    
    def _on_key_press_text(self, event):
        """Sauvegarde dans l'historique avant modification du texte."""
        if event.keysym not in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R',
                               'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab', 'Prior', 'Next']:
            current_value = self.text_editor.get("1.0", "end-1c")
            if not self._text_history or (self._text_history and self._text_history[-1] != current_value):
                if len(self._text_history) >= self._max_history:
                    self._text_history.pop(0)
                self._text_history.append(current_value)
    
    def _on_focus_out(self, event):
        """Sauvegarde automatique quand on perd le focus."""
        self._save_changes()
    
    def _on_enter_pressed(self, event):
        """Sauvegarde automatique quand on appuie sur Entree."""
        self._save_changes()
        return "break"
    
    def _on_undo_pressed(self, event):
        """Gere l'annulation (Ctrl+Z)."""
        widget = event.widget
        
        try:
            if hasattr(widget, '_entry'):
                tk_widget = widget._entry
                if hasattr(tk_widget, 'edit_undo'):
                    try:
                        tk_widget.edit_undo()
                        return "break"
                    except tk.TclError:
                        pass
            
            elif hasattr(widget, '_textbox'):
                tk_widget = widget._textbox
                if hasattr(tk_widget, 'edit_undo'):
                    try:
                        tk_widget.edit_undo()
                        return "break"
                    except tk.TclError:
                        pass
        except:
            pass
        
        return "break"
    
    def _save_text_to_history(self):
        """Sauvegarde l'etat actuel dans l'historique."""
        if self.current_highlight:
            try:
                current_name = self.name_entry.get()
                if not self._name_history or (self._name_history and self._name_history[-1] != current_name):
                    if len(self._name_history) >= self._max_history:
                        self._name_history.pop(0)
                    self._name_history.append(current_name)
                
                current_text = self.text_editor.get("1.0", "end-1c")
                if not self._text_history or (self._text_history and self._text_history[-1] != current_text):
                    if len(self._text_history) >= self._max_history:
                        self._text_history.pop(0)
                    self._text_history.append(current_text)
            except:
                pass
    
    def _create_content(self):
        """Cree le contenu du panneau d'edition."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="EDITION DU HIGHLIGHT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(side="left")
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        left_column = ctk.CTkFrame(main_frame, fg_color="#3a3a3a")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
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
        
        name_label = ctk.CTkLabel(
            left_column,
            text="Nom personnalise:",
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
        
        self.name_entry.bind("<Return>", self._on_enter_pressed)
        self.name_entry.bind("<Control-z>", self._on_undo_pressed)
        self.name_entry.bind("<FocusOut>", self._on_focus_out)
        self.name_entry.bind("<KeyPress>", self._on_key_press_name)
        
        try:
            if hasattr(self.name_entry, '_entry'):
                self.name_entry._entry.configure(undo=True, maxundo=20)
        except:
            pass
        
        buttons_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Bouton supprimer (stocke en attribut pour mise a jour du texte)
        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="SUPPRIMER FICHE",
            command=self._delete_highlight,
            fg_color="#cc4444",
            hover_color="#dd5555",
            height=35
        )
        self.clear_btn.pack(fill="x")
        
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
        
        self.text_editor.bind("<Return>", self._on_enter_pressed)
        self.text_editor.bind("<Control-z>", self._on_undo_pressed)
        self.text_editor.bind("<FocusOut>", self._on_focus_out)
        self.text_editor.bind("<KeyPress>", self._on_key_press_text)
        
        try:
            if hasattr(self.text_editor, '_textbox'):
                self.text_editor._textbox.configure(undo=True, maxundo=20)
        except:
            pass
        
        self._show_default_message()
    
    def _show_default_message(self):
        """Affiche un message par defaut."""
        self.page_label.configure(text="Page: -")
        self.confidence_label.configure(text="Confiance: -")
        self.name_entry.delete(0, 'end')
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "Selectionnez un highlight ci-dessus pour l'afficher ici...")
        self.current_highlight = None
        self.initial_text = ""
        self.initial_name = ""
    
    def show_highlight(self, highlight_data):
        """Affiche un highlight pour edition."""
        self._save_text_to_history()
        
        self.current_highlight = highlight_data.copy()
        
        page = highlight_data.get('page', '?')
        confidence = highlight_data.get('confidence', 0)
        
        self.page_label.configure(text=f"Page: {page}")
        self.confidence_label.configure(text=f"Confiance: {confidence:.1f}%")
        
        custom_name = highlight_data.get('custom_name', '')
        self.name_entry.delete(0, 'end')
        if custom_name:
            self.name_entry.insert(0, custom_name)
        
        text = highlight_data.get('text', '')
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text)
        
        self.initial_name = custom_name
        self.initial_text = text
        
        self._text_history.clear()
        self._name_history.clear()
    
    def _save_changes(self):
        """Sauvegarde les modifications."""
        if not self.current_highlight:
            return
        
        new_text = self.text_editor.get("1.0", "end-1c")
        new_name = self.name_entry.get().strip()
        
        has_changes = False
        
        if new_text != self.initial_text:
            has_changes = True
        
        if new_name != self.initial_name:
            has_changes = True
        
        self.current_highlight['text'] = new_text
        if new_name:
            self.current_highlight['custom_name'] = new_name
        elif 'custom_name' in self.current_highlight:
            del self.current_highlight['custom_name']
        
        if has_changes:
            self.current_highlight['modified'] = True
            self.current_highlight['modified_date'] = datetime.now().isoformat()
        
        if self.on_save:
            self.on_save(self.current_highlight)
    
    def _delete_highlight(self):
        """Supprime la fiche highlight ou les fiches selectionnees (multi-selection)."""
        print("=== BOUTON SUPPRIMER CLIQUE ===")
        
        # Utiliser la reference directe a MainWindow
        if self.main_window and hasattr(self.main_window, 'highlights_grid'):
            selected_cards = self.main_window.highlights_grid.selected_cards
            print(f"Nombre de cartes selectionnees: {len(selected_cards)}")
            
            if len(selected_cards) > 1:
                print(f"MODE MULTI-SUPPRESSION pour {len(selected_cards)} fiches")
                
                if messagebox.askyesno(
                    "Supprimer les highlights",
                    f"Etes-vous sur de vouloir supprimer {len(selected_cards)} highlights ?\n\nCette action est irreversible."
                ):
                    # Recuperer toutes les donnees a supprimer AVANT la suppression
                    data_to_delete = []
                    for card in selected_cards:
                        data_to_delete.append({
                            'page': card.highlight_data.get('page'),
                            'text': card.highlight_data.get('text', ''),
                            'timestamp': card.highlight_data.get('timestamp')
                        })
                        print(f"  Preparant suppression: Page {card.highlight_data.get('page')}")
                    
                    # Supprimer de all_highlights_data (source complete)
                    if hasattr(self.main_window, 'all_highlights_data'):
                        initial_count = len(self.main_window.all_highlights_data)
                        print(f"Taille initiale all_highlights_data: {initial_count}")
                        
                        # Creer une nouvelle liste sans les elements a supprimer
                        new_data = []
                        deleted_count = 0
                        
                        for stored_data in self.main_window.all_highlights_data:
                            should_delete = False
                            for delete_data in data_to_delete:
                                if (stored_data.get('page') == delete_data['page'] and
                                    stored_data.get('text', '') == delete_data['text'] and
                                    stored_data.get('timestamp') == delete_data['timestamp']):
                                    should_delete = True
                                    deleted_count += 1
                                    print(f"    -> Suppression confirmee Page {delete_data['page']}")
                                    break
                            
                            if not should_delete:
                                new_data.append(stored_data)
                        
                        print(f"Resultat: {deleted_count} supprime(s), {len(new_data)} restant(s)")
                        
                        # Remplacer les donnees
                        self.main_window.all_highlights_data = new_data
                        
                        # Mettre a jour la pagination avec les nouvelles donnees
                        self.main_window.pagination_controller.set_data(self.main_window.all_highlights_data)
                        
                        # Afficher la page courante mise a jour
                        self.main_window._display_current_page()
                    
                    # Mettre a jour l'interface
                    self.main_window._update_highlights_count()
                    self.main_window._save_to_extraction_file()
                    self.main_window._update_delete_button_text()
                    self._show_default_message()
                    
                    messagebox.showinfo("Suppression reussie", f"{deleted_count} highlights supprimes.")
                return
        
        print("MODE SUPPRESSION SIMPLE")
        
        # Suppression simple (code existant)
        if not self.current_highlight:
            messagebox.showwarning("Aucune selection", "Aucun highlight selectionne a supprimer.")
            return
        
        page = self.current_highlight.get('page', '?')
        name = self.current_highlight.get('custom_name', f"Page {page}")
        
        if messagebox.askyesno(
            "Supprimer le highlight",
            f"Etes-vous sur de vouloir supprimer definitivement :\n\n'{name}'\n\nCette action est irreversible."
        ):
            if self.on_delete:
                self.on_delete(self.current_highlight)
            
            self._show_default_message()


class MainWindow(ctk.CTk):
    """Fenetre principale de l'application AllamBik v3 avec pagination."""
    
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        
        self.viewmodel = viewmodel
        self.async_loop = None
        
        # Variables d'etat
        self.view_mode = "grid"
        self.current_search = ""
        self.extraction_file_path = None
        self.selected_card = None
        
        # Pagination pour grandes listes
        self.pagination_controller = PaginationController(items_per_page=50)
        self.all_highlights_data = []  # Donnees completes du JSON
        
        self._update_queue = []
        
        self._setup_window()
        self._create_ui()
        self._bind_viewmodel()
        self._start_update_loop()
    
    def _setup_window(self):
        """Configure la fenetre principale."""
        self.title("AllamBik v3.0 - Extracteur de Highlights Kindle")
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
        """Cree l'interface utilisateur."""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        main_container.grid_columnconfigure(0, weight=1, minsize=400)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(0, weight=1)
        
        self._create_left_panel(main_container)
        self._create_right_panel(main_container)
    
    def _create_left_panel(self, parent):
        """Cree le panneau gauche."""
        left_panel = ctk.CTkFrame(parent, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
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
            text="ALLAMBIK v3.0",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.pack(expand=True)
        
        progress_section = self._create_section(left_panel, "PROGRESSION")
        self.progress_circle = ProgressCircle(progress_section)
        self.progress_circle.pack(pady=10)
        
        self.progress_label = ctk.CTkLabel(
            progress_section,
            text="Pret pour l'extraction",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.progress_label.pack(pady=(0, 15))
        
        controls_section = self._create_section(left_panel, "CONTROLES")
        
        self.zone_picker_button = ZonePickerButton(
            controls_section,
            on_zone_selected=self._on_zone_selected,
            text="DEFINIR ZONE DE SCAN",
            fg_color=self.colors['warning'],
            hover_color="#ff8800"
        )
        self.zone_picker_button.pack(fill="x", padx=20, pady=(10, 5))
        
        self.start_button = ctk.CTkButton(
            controls_section,
            text="DEMARRER EXTRACTION",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=self.colors['accent'],
            hover_color="#0088cc",
            command=self._on_start_clicked
        )
        self.start_button.pack(fill="x", padx=20, pady=(5, 5))
        
        self.stop_button = ctk.CTkButton(
            controls_section,
            text="ARRETER EXTRACTION",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['error'],
            state="disabled",
            command=self._on_stop_clicked
        )
        self.stop_button.pack(fill="x", padx=20, pady=(5, 5))
        
        self.detect_button = ctk.CTkButton(
            controls_section,
            text="DETECTER NOMBRE DE PAGES",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#ff6600",
            hover_color="#ff8800",
            command=self._on_detect_pages_clicked
        )
        self.detect_button.pack(fill="x", padx=20, pady=(5, 5))
        
        self.import_json_button = ctk.CTkButton(
            controls_section,
            text="CHARGER JSON",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#8B4513",
            hover_color="#A0522D",
            command=self._on_import_json_clicked
        )
        self.import_json_button.pack(fill="x", padx=20, pady=(5, 5))
        
        self.export_word_button = ctk.CTkButton(
            controls_section,
            text="EXPORTER WORD",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color="#2d5a2d",
            hover_color="#3d6a3d",
            command=self._on_export_word_clicked
        )
        self.export_word_button.pack(fill="x", padx=20, pady=(5, 15))
        
        stats_section = self._create_section(left_panel, "STATISTIQUES")
        
        stats_frame = ctk.CTkFrame(stats_section, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        self.stats_labels = {}
        stats = [
            ("pages_scanned", "Pages scannees"),
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
    
    def _create_right_panel(self, parent):
        """Cree le panneau droit avec pagination."""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        right_panel.grid_rowconfigure(0, weight=2)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        highlights_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        highlights_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        highlights_section = self._create_section_frame(highlights_container, "HIGHLIGHTS EXTRAITS")
        highlights_section.pack(fill="both", expand=True)
        
        # Utiliser grid au lieu de pack pour mieux controler le layout
        highlights_section.grid_rowconfigure(0, weight=0)  # Header
        highlights_section.grid_rowconfigure(1, weight=0)  # Search
        highlights_section.grid_rowconfigure(2, weight=1)  # Grid
        highlights_section.grid_rowconfigure(3, weight=0)  # Pagination
        highlights_section.grid_columnconfigure(0, weight=1)
        
        # HEADER
        header_frame = ctk.CTkFrame(highlights_section, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        self.highlights_title = ctk.CTkLabel(
            header_frame,
            text="HIGHLIGHTS EXTRAITS (0)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary']
        )
        self.highlights_title.pack(side="left")
        
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right")
        
        self.list_view_button = ctk.CTkButton(
            controls_frame,
            text="LISTE",
            width=60,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#4a4a4a" if self.view_mode != "list" else self.colors['accent'],
            hover_color="#5a5a5a",
            command=self._set_list_view
        )
        self.list_view_button.pack(side="right", padx=(5, 0))
        
        self.grid_view_button = ctk.CTkButton(
            controls_frame,
            text="GRILLE",
            width=60,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#4a4a4a" if self.view_mode != "grid" else self.colors['accent'],
            hover_color="#5a5a5a",
            command=self._set_grid_view
        )
        self.grid_view_button.pack(side="right", padx=(5, 0))
        
        # SEARCH
        search_frame = ctk.CTkFrame(highlights_section, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Rechercher dans les highlights...",
            font=ctk.CTkFont(size=11),
            height=30
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        clear_search_btn = ctk.CTkButton(
            search_frame,
            text="X",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#444444",
            command=self._clear_search
        )
        clear_search_btn.pack(side="right")
        
        # GRILLE DE HIGHLIGHTS
        self.highlights_grid = HighlightGrid(
            highlights_section,
            columns=2,
            fg_color="transparent",
            on_edit_requested=self._on_edit_requested,
            on_highlight_selected=self._on_highlight_selected
        )
        self.highlights_grid.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 5))
        
        # BARRE DE PAGINATION - Positionnee apres la grille
        self.pagination_bar = PaginationBar(
            highlights_section,
            self.pagination_controller,
            fg_color="transparent"
        )
        self.pagination_bar.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.pagination_bar.grid_remove()  # Cachee au debut
        
        # PANNEAU D'EDITION avec reference a MainWindow
        self.edit_panel = IntegratedEditPanel(
            right_panel,
            main_window=self,  # CORRECTION: Passer la reference
            on_save=self._on_edit_saved,
            on_cancel=self._on_edit_cancelled,
            on_delete=self._on_highlight_deleted
        )
        self.edit_panel.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    def _create_section(self, parent, title: str) -> ctk.CTkFrame:
        """Cree une section avec titre."""
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
        """Cree une section frame."""
        section = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_secondary'],
            corner_radius=10
        )
        return section
    
    def _bind_viewmodel(self):
        """Lie le ViewModel."""
        self.viewmodel.on_state_changed = self._on_state_changed
        self.viewmodel.on_progress_changed = self._on_progress_changed
        self.viewmodel.on_highlight_added = self._on_highlight_added
    
    def _start_update_loop(self):
        """Demarre la boucle de mise a jour."""
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
        """Planifie une mise a jour."""
        self._update_queue.append(func)
    
    def _set_grid_view(self):
        """Active le mode grille."""
        if self.view_mode != "grid":
            self.view_mode = "grid"
            self._update_view_buttons()
            self._recreate_grid(2)
    
    def _set_list_view(self):
        """Active le mode liste."""
        if self.view_mode != "list":
            self.view_mode = "list"
            self._update_view_buttons()
            self._recreate_grid(1)
    
    def _update_view_buttons(self):
        """Met a jour les boutons de vue."""
        grid_color = self.colors['accent'] if self.view_mode == "grid" else "#4a4a4a"
        self.grid_view_button.configure(fg_color=grid_color)
        
        list_color = self.colors['accent'] if self.view_mode == "list" else "#4a4a4a"
        self.list_view_button.configure(fg_color=list_color)
    
    def _recreate_grid(self, columns):
        """Recree la grille."""
        highlights_data = self.highlights_grid.get_highlights_data()
        
        for card in self.highlights_grid.cards:
            card.destroy()
        
        self.highlights_grid.cards.clear()
        self.highlights_grid.highlights_data.clear()
        self.highlights_grid.columns = columns
        
        for i in range(columns):
            self.highlights_grid.grid_columnconfigure(i, weight=1, uniform="column")
        
        if columns < 4:
            for i in range(columns, 4):
                self.highlights_grid.grid_columnconfigure(i, weight=0, uniform="")
        
        self.highlights_grid.update_idletasks()
        self.after_idle(lambda: self._restore_highlights_data(highlights_data))
    
    def _restore_highlights_data(self, highlights_data):
        """Restaure les donnees."""
        selected_highlight = None
        if self.selected_card and self.selected_card.highlight_data:
            selected_highlight = self.selected_card.highlight_data.copy()
        
        for highlight_data in highlights_data:
            self.highlights_grid.add_highlight(highlight_data)
        
        if selected_highlight:
            self.after_idle(lambda: self._restore_selection(selected_highlight))
        
        self._update_highlights_count()
        self.highlights_grid.update_idletasks()
        self.update_idletasks()
    
    def _restore_selection(self, selected_highlight):
        """Restaure la selection."""
        for card in self.highlights_grid.cards:
            if (card.highlight_data.get('page') == selected_highlight.get('page') and
                card.highlight_data.get('text', '')[:50] == selected_highlight.get('text', '')[:50]):
                card.set_selected(True)
                self.selected_card = card
                break
    
    def _on_highlight_selected(self, highlight_data, shift_pressed=False):
        """Callback selection highlight avec support multi-selection (Shift)."""
        if hasattr(self, 'edit_panel') and self.edit_panel.current_highlight:
            self.edit_panel._save_changes()
        
        # Trouver la carte cliquee
        clicked_card = None
        for card in self.highlights_grid.cards:
            if (card.highlight_data.get('page') == highlight_data.get('page') and
                card.highlight_data.get('text', '')[:50] == highlight_data.get('text', '')[:50]):
                clicked_card = card
                break
        
        if not clicked_card:
            return
        
        if shift_pressed:
            # Mode multi-selection : ajouter/retirer de la selection
            if clicked_card in self.highlights_grid.selected_cards:
                # Deselectionner cette carte
                clicked_card.set_selected(False)
                self.highlights_grid.selected_cards.remove(clicked_card)
            else:
                # Ajouter a la selection
                clicked_card.set_selected(True)
                self.highlights_grid.selected_cards.append(clicked_card)
            
            # Afficher la derniere carte selectionnee dans le panneau d'edition
            if self.highlights_grid.selected_cards:
                self.edit_panel.show_highlight(self.highlights_grid.selected_cards[-1].highlight_data)
            else:
                self.edit_panel._show_default_message()
        else:
            # Mode selection simple : deselectionner tout sauf la carte cliquee
            for card in self.highlights_grid.selected_cards:
                if card != clicked_card:
                    try:
                        card.set_selected(False)
                    except:
                        pass
            
            self.highlights_grid.selected_cards.clear()
            clicked_card.set_selected(True)
            self.highlights_grid.selected_cards.append(clicked_card)
            
            # Afficher dans le panneau d'edition
            self.edit_panel.show_highlight(highlight_data)
        
        # Mettre a jour le texte du bouton supprimer
        self._update_delete_button_text()
    
    def _update_delete_button_text(self):
        """Met a jour le texte du bouton supprimer selon le nombre de selections."""
        count = len(self.highlights_grid.selected_cards)
        if count > 1:
            self.edit_panel.clear_btn.configure(text=f"SUPPRIMER {count} FICHES")
        else:
            self.edit_panel.clear_btn.configure(text="SUPPRIMER FICHE")
    
    def _on_edit_requested(self, highlight_data):
        """Callback edition demandee."""
        self.edit_panel.show_highlight(highlight_data)
    
    def _on_edit_saved(self, updated_data):
        """Callback sauvegarde edition."""
        try:
            self.highlights_grid.update_highlight(updated_data)
            self._save_to_extraction_file()
        except Exception as e:
            print(f"ERREUR: Erreur sauvegarde: {e}")
            self._force_refresh_all_cards()
    
    def _on_edit_cancelled(self):
        """Callback edition annulee."""
        pass
    
    def _on_highlight_deleted(self, highlight_data):
        """Callback suppression highlight."""
        if (self.selected_card and 
            self.selected_card.highlight_data.get('page') == highlight_data.get('page') and
            self.selected_card.highlight_data.get('text', '')[:50] == highlight_data.get('text', '')[:50]):
            self.selected_card = None
            self.edit_panel._show_default_message()
        
        try:
            self.highlights_grid._on_highlight_deleted(highlight_data)
            self._update_highlights_count()
            self._save_to_extraction_file()
            self._update_delete_button_text()
        except Exception as e:
            print(f"ERREUR: Erreur suppression: {e}")
    
    def _force_refresh_all_cards(self):
        """Force le rafraichissement."""
        try:
            for i, (card, data) in enumerate(zip(self.highlights_grid.cards, self.highlights_grid.highlights_data)):
                card.update_data(data)
        except Exception as e:
            print(f"ERREUR: Erreur rafraichissement: {e}")
    
    def _save_to_extraction_file(self):
        """Sauvegarde dans fichier."""
        if not self.extraction_file_path or not os.path.exists(self.extraction_file_path):
            self._find_or_create_extraction_file()
        
        if self.extraction_file_path:
            try:
                highlights_data = self.highlights_grid.get_highlights_data()
                
                content = "=== HIGHLIGHTS KINDLE EXTRAITS ===\n"
                content += f"Genere le: {datetime.now().strftime('%d/%m/%Y a %H:%M')}\n"
                content += f"Nombre total: {len(highlights_data)}\n\n"
                
                for i, highlight in enumerate(highlights_data, 1):
                    title = highlight.get('custom_name', f"Page {highlight.get('page', '?')}")
                    content += f"--- {i}. {title} ---\n"
                    content += f"Page: {highlight.get('page', '?')}\n"
                    content += f"Confiance: {highlight.get('confidence', 0):.1f}%\n"
                    
                    if highlight.get('modified'):
                        content += f"Modifie le: {highlight.get('modified_date', 'N/A')}\n"
                    
                    content += f"\nTexte:\n{highlight.get('text', '')}\n\n"
                    content += "-" * 50 + "\n\n"
                
                with open(self.extraction_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"ERREUR: Sauvegarde: {e}")
    
    def _find_or_create_extraction_file(self):
        """Trouve ou cree fichier extraction."""
        extractions_dir = "extractions"
        if os.path.exists(extractions_dir):
            txt_files = [f for f in os.listdir(extractions_dir) if f.endswith('.txt')]
            if txt_files:
                latest_file = max(txt_files, key=lambda f: os.path.getctime(os.path.join(extractions_dir, f)))
                self.extraction_file_path = os.path.join(extractions_dir, latest_file)
                return
        
        if not os.path.exists(extractions_dir):
            os.makedirs(extractions_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"highlights_extraits_{timestamp}.txt"
        self.extraction_file_path = os.path.join(extractions_dir, filename)
    
    def _on_export_word_clicked(self):
        """Exporte vers Word."""
        if not WORD_AVAILABLE:
            messagebox.showerror(
                "Export Word indisponible", 
                "La bibliotheque python-docx n'est pas installee.\n\n" +
                "Installez-la avec: poetry add python-docx\n" +
                "Puis redemarrez l'application."
            )
            return
        
        highlights_data = self.highlights_grid.get_highlights_data()
        
        if not highlights_data:
            messagebox.showwarning("Aucun highlight", "Aucun highlight a exporter.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Exporter vers Word",
            defaultextension=".docx",
            filetypes=[("Documents Word", "*.docx"), ("Tous les fichiers", "*.*")],
            initialfile=f"highlights_kindle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        )
        
        if file_path:
            try:
                doc = Document()
                
                title = doc.add_heading('Highlights Kindle - Extraits AllamBik', 0)
                title.alignment = 1
                
                info_para = doc.add_paragraph()
                info_para.add_run("Document genere le: ").bold = True
                info_para.add_run(f"{datetime.now().strftime('%d/%m/%Y a %H:%M')}\n")
                info_para.add_run("Nombre total d'extraits: ").bold = True
                info_para.add_run(f"{len(highlights_data)} highlights\n")
                
                doc.add_paragraph("=" * 60)
                
                for i, highlight in enumerate(highlights_data, 1):
                    title_text = highlight.get('custom_name', f"Extrait Page {highlight.get('page', '?')}")
                    doc.add_heading(f"{i}. {title_text}", level=2)
                    
                    meta_para = doc.add_paragraph()
                    meta_para.add_run("Page: ").bold = True
                    meta_para.add_run(f"{highlight.get('page', '?')}")
                    
                    meta_para.add_run("  |  Confiance: ").bold = True
                    meta_para.add_run(f"{highlight.get('confidence', 0):.1f}%")
                    
                    content = highlight.get('text', '').strip()
                    if content:
                        text_content = doc.add_paragraph(content)
                        text_content.style = 'Quote'
                    else:
                        doc.add_paragraph("[Aucun texte]")
                    
                    if i < len(highlights_data):
                        doc.add_paragraph("-" * 40)
                
                doc.save(file_path)
                
                messagebox.showinfo(
                    "Export Word reussi", 
                    f"Document Word cree avec succes!\n\n" +
                    f"{len(highlights_data)} highlights exportes"
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Erreur d'export Word", 
                    f"Erreur:\n{str(e)}"
                )
    
    def _on_search_changed(self, event):
        """Gere recherche."""
        search_text = self.search_entry.get().lower().strip()
        self.current_search = search_text
        
        if not search_text:
            self._show_all_cards()
        else:
            self._filter_and_highlight_cards(search_text)
        
        self._update_highlights_count()
    
    def _show_all_cards(self):
        """Affiche toutes les cartes."""
        for card in self.highlights_grid.cards:
            try:
                row = self.highlights_grid.cards.index(card) // self.highlights_grid.columns
                col = self.highlights_grid.cards.index(card) % self.highlights_grid.columns
                card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            except:
                pass
            
            card._remove_search_highlight()
    
    def _filter_and_highlight_cards(self, search_text):
        """Filtre les cartes."""
        visible_count = 0
        
        for i, card in enumerate(self.highlights_grid.cards):
            highlight_data = card.highlight_data
            
            text_match = search_text in highlight_data.get('text', '').lower()
            name_match = search_text in highlight_data.get('custom_name', '').lower()
            page_match = search_text in str(highlight_data.get('page', ''))
            
            if text_match or name_match or page_match:
                try:
                    row = visible_count // self.highlights_grid.columns
                    col = visible_count % self.highlights_grid.columns
                    card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                    visible_count += 1
                    card._add_search_highlight(search_text)
                except:
                    pass
            else:
                try:
                    card.grid_remove()
                    card._remove_search_highlight()
                except:
                    pass
    
    def _clear_search(self):
        """Efface la recherche."""
        self.search_entry.delete(0, "end")
        self.current_search = ""
        self._show_all_cards()
        self._update_highlights_count()
    
    def _update_highlights_count(self):
        """Met a jour le compteur."""
        count = self.highlights_grid.get_count()
        self.highlights_title.configure(text=f"HIGHLIGHTS EXTRAITS ({count})")
    
    def _on_zone_selected(self, zone: Tuple[int, int, int, int]):
        """Callback zone selectionnee."""
        if hasattr(self.viewmodel, 'custom_scan_zone'):
            self.viewmodel.custom_scan_zone = zone
        else:
            self.viewmodel.custom_scan_zone = zone
        
        x, y, w, h = zone
        print(f"INFO: Zone: {w}x{h} a ({x},{y})")
    
    def _on_start_clicked(self):
        """Gere clic demarrer."""
        if hasattr(self.viewmodel, 'detected_pages') and self.viewmodel.detected_pages:
            total_pages = self.viewmodel.detected_pages
            
            if self.async_loop:
                asyncio.run_coroutine_threadsafe(
                    self.viewmodel.start_extraction_command(total_pages),
                    self.async_loop
                )
            return
        
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
        """Gere clic arreter."""
        if self.async_loop:
            asyncio.run_coroutine_threadsafe(
                self.viewmodel.stop_extraction_command(),
                self.async_loop
            )
    
    def _on_detect_pages_clicked(self):
        """Lance detection pages."""
        if not hasattr(self.viewmodel, 'page_detector') or self.viewmodel.page_detector is None:
            messagebox.showinfo(
                "Detection non disponible",
                "La detection automatique n'est pas encore configuree."
            )
            return
        
        if messagebox.askyesno("Detection des pages", "Lancer la detection automatique?"):
            self.detect_button.configure(state="disabled", text="DETECTION EN COURS...")
            
            if hasattr(self.viewmodel, 'detect_pages_command') and self.async_loop:
                import asyncio
                
                def on_complete(future):
                    self.detect_button.configure(state="normal")
                    try:
                        result = future.result()
                        if self.viewmodel.detected_pages:
                            self.detect_button.configure(
                                text=f"{self.viewmodel.detected_pages} PAGES",
                                fg_color="#00aa00"
                            )
                    except Exception as e:
                        self.detect_button.configure(text="DETECTER NOMBRE DE PAGES")
                
                future = asyncio.run_coroutine_threadsafe(
                    self.viewmodel.detect_pages_command(),
                    self.async_loop
                )
                future.add_done_callback(lambda f: self.after(0, lambda: on_complete(f)))
    
    def _on_import_json_clicked(self):
        """Charge un fichier JSON avec pagination automatique."""
        from tkinter import filedialog, messagebox
        import json
        import os
        
        print("INFO: Import JSON demande")
        
        try:
            file_path = filedialog.askopenfilename(
                title="Selectionner un fichier JSON d'extraction",
                initialdir=os.path.abspath("extractions") if os.path.exists("extractions") else os.getcwd(),
                filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
            )
            
            if not file_path:
                print("Selection annulee")
                return
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dialogue:\n{str(e)}")
            return
        
        try:
            print(f"Chargement de: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            highlights = []
            if isinstance(data, list):
                highlights = data
            elif isinstance(data, dict):
                highlights = data.get('highlights', data.get('results', []))
            
            formatted_highlights = []
            for i, h in enumerate(highlights):
                if isinstance(h, dict):
                    highlight_data = {
                        'page': h.get('page', h.get('page_number', i // 3 + 1)),
                        'text': h.get('text', h.get('extracted_text', '')),
                        'confidence': h.get('confidence', h.get('confidence_score', 85)),
                        'timestamp': h.get('timestamp', "2024-01-01T00:00:00"),
                        'source_image': h.get('source_image', None),
                        'coordinates': h.get('coordinates', None),
                        'validated': h.get('validated', False),
                        'modified': h.get('modified', False)
                    }
                    formatted_highlights.append(highlight_data)
            
            print(f"[OK] {len(formatted_highlights)} highlights charges")
            
            # Stocker toutes les donnees dans all_highlights_data
            self.all_highlights_data = formatted_highlights
            
            # Configurer la pagination
            self.pagination_controller.set_data(formatted_highlights)
            self.pagination_controller.on_page_changed = self._on_page_changed
            
            # Afficher la premiere page
            self._display_current_page()
            
            # Afficher la barre de pagination
            self.pagination_bar.grid()
            self.pagination_bar.refresh()
            
            messagebox.showinfo(
                "Import reussi",
                f"{len(formatted_highlights)} highlights charges\n"
                f"Affichage par pages de {self.pagination_controller.items_per_page}"
            )
            
        except Exception as e:
            print(f"Erreur import JSON: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Impossible de charger:\n{str(e)}")
    
    def _on_page_changed(self, page_data, page_number):
        """Callback changement de page."""
        self._display_current_page()
    
    def _display_current_page(self):
        """Affiche la page actuelle."""
        current_page_data = self.pagination_controller.get_current_page_data()
        
        self.highlights_grid.set_paginated_data(current_page_data)
        
        total = self.pagination_controller.total_items
        start = self.pagination_controller.start_index + 1
        end = self.pagination_controller.end_index
        self.highlights_title.configure(
            text=f"HIGHLIGHTS EXTRAITS ({start}-{end} sur {total})"
        )
        
        print(f"INFO: Page {self.pagination_controller.current_page}/{self.pagination_controller.total_pages}")
    
    def _on_state_changed(self, state: ViewState):
        """Met a jour selon etat."""
        def update():
            self.start_button.configure(
                state="normal" if self.viewmodel.can_start else "disabled"
            )
            self.stop_button.configure(
                state="normal" if self.viewmodel.can_stop else "disabled"
            )
            
            has_highlights = self.highlights_grid.get_count() > 0
            self.export_word_button.configure(
                state="normal" if has_highlights else "disabled"
            )
            
            if state == ViewState.ERROR:
                self.progress_circle.configure(fg_color=self.colors['error'])
        
        self._schedule_update(update)
    
    def _on_progress_changed(self):
        """Met a jour progression."""
        def update():
            self.progress_circle.update_progress(
                current=self.viewmodel.current_progress,
                phase1=self.viewmodel.phase1_progress,
                phase2=self.viewmodel.phase2_progress
            )
            self.progress_label.configure(text=self.viewmodel.progress_message)
            
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
        """Ajoute un highlight."""
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
            self._save_to_extraction_file()
        
        self._schedule_update(update)