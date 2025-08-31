"""
Fenêtre principale - Version corrigée sans bugs d'ascenseur
"""
import customtkinter as ctk
from src.presentation.gui.components.highlight_card import HighlightCard
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
    print("ATTENTION: python-docx non disponible. Export Word désactivé.")

from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel, ViewState, HighlightViewModel
from src.presentation.gui.components.progress_circle import ProgressCircle
from src.presentation.gui.components.highlight_card import HighlightGrid
from src.presentation.gui.components.zone_picker import ZonePickerButton


class IntegratedEditPanel(ctk.CTkFrame):
    """Panneau d'édition intégré en bas de l'interface."""
    
    def __init__(self, parent, on_save=None, on_cancel=None, on_delete=None):
        super().__init__(parent)
        self.configure(fg_color="#2a2a2a", corner_radius=10)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.on_delete = on_delete
        self.current_highlight = None
        
        # CORRECTION BUG MODIF: Variables pour l'état initial
        self.initial_text = ""
        self.initial_name = ""
        
        self._create_content()
        # Le placement est géré par le parent avec grid()
        
        # Variables pour l'historique d'annulation
        self._text_history = []
        self._name_history = []
        self._max_history = 50
    
    def _on_key_press_name(self, event):
        """Sauvegarde dans l'historique avant modification du nom."""
        # CORRECTION CTRL+Z: Sauvegarder seulement pour les vraies modifications
        if event.keysym not in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 
                               'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab']:
            current_value = self.name_entry.get()
            if not self._name_history or (self._name_history and self._name_history[-1] != current_value):
                if len(self._name_history) >= self._max_history:
                    self._name_history.pop(0)
                self._name_history.append(current_value)
                print(f"DEBUG: Historique nom sauvegardé: '{current_value}' (touche: {event.keysym})")
    
    def _on_key_press_text(self, event):
        """Sauvegarde dans l'historique avant modification du texte."""
        # CORRECTION CTRL+Z: Sauvegarder seulement pour les vraies modifications
        if event.keysym not in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R',
                               'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab', 'Prior', 'Next']:
            current_value = self.text_editor.get("1.0", "end-1c")
            if not self._text_history or (self._text_history and self._text_history[-1] != current_value):
                if len(self._text_history) >= self._max_history:
                    self._text_history.pop(0)
                self._text_history.append(current_value)
                print(f"DEBUG: Historique texte sauvegardé: '{current_value[:30]}...' (touche: {event.keysym})")
    
    def _on_focus_out(self, event):
        """Sauvegarde automatique quand on perd le focus (clic ailleurs)."""
        self._save_changes()
    
    def _on_enter_pressed(self, event):
        """Sauvegarde automatique quand on appuie sur Entrée."""
        self._save_changes()
        return "break"  # Empêche le comportement par défaut
    
    def _on_undo_pressed(self, event):
        """Gère l'annulation (Ctrl+Z) - VERSION CORRIGÉE RENFORCÉE."""
        widget = event.widget
        print(f"DEBUG: Ctrl+Z pressé sur widget: {type(widget)}")
        
        # CORRECTION RENFORCÉE: Multiples tentatives d'accès aux widgets natifs
        try:
            # Méthode 1: Accès direct aux widgets sous-jacents CustomTkinter
            if hasattr(widget, '_entry'):
                tk_widget = widget._entry
                print(f"DEBUG: Widget Entry trouvé: {type(tk_widget)}")
                if hasattr(tk_widget, 'edit_undo'):
                    try:
                        tk_widget.edit_undo()
                        print("SUCCESS: Undo natif CTkEntry exécuté")
                        return "break"
                    except tk.TclError as e:
                        print(f"DEBUG: Undo natif Entry échoué: {e}")
            
            elif hasattr(widget, '_textbox'):
                tk_widget = widget._textbox
                print(f"DEBUG: Widget Textbox trouvé: {type(tk_widget)}")
                if hasattr(tk_widget, 'edit_undo'):
                    try:
                        tk_widget.edit_undo()
                        print("SUCCESS: Undo natif CTkTextbox exécuté")
                        return "break"
                    except tk.TclError as e:
                        print(f"DEBUG: Undo natif Textbox échoué: {e}")
            
            # Méthode 2: Si c'est directement un widget Tkinter
            elif hasattr(widget, 'edit_undo'):
                try:
                    widget.edit_undo()
                    print("SUCCESS: Undo natif direct exécuté")
                    return "break"
                except tk.TclError as e:
                    print(f"DEBUG: Undo natif direct échoué: {e}")
        
        except Exception as e:
            print(f"DEBUG: Erreur accès widgets natifs: {e}")
        
        # MÉTHODE 3: Forcer l'activation de l'undo sur les widgets natifs
        try:
            if hasattr(widget, '_entry'):
                tk_widget = widget._entry
                # Forcer l'activation de l'undo si pas déjà fait
                try:
                    tk_widget.configure(undo=True, maxundo=20)
                    tk_widget.edit_undo()
                    print("SUCCESS: Undo forcé CTkEntry exécuté")
                    return "break"
                except:
                    pass
            
            elif hasattr(widget, '_textbox'):
                tk_widget = widget._textbox
                # Forcer l'activation de l'undo si pas déjà fait
                try:
                    tk_widget.configure(undo=True, maxundo=20)
                    tk_widget.edit_undo()
                    print("SUCCESS: Undo forcé CTkTextbox exécuté")
                    return "break"
                except:
                    pass
        
        except Exception as e:
            print(f"DEBUG: Undo forcé échoué: {e}")
        
        # FALLBACK: Système d'undo manuel amélioré
        print("DEBUG: Utilisation du système d'undo manuel")
        try:
            # Identifier le widget parent CustomTkinter
            if hasattr(widget, 'master') and hasattr(widget.master, 'master'):
                parent_widget = widget.master.master
                if parent_widget == self.name_entry:
                    print("DEBUG: Undo manuel pour champ nom")
                    if self._name_history and len(self._name_history) >= 1:
                        if len(self._name_history) >= 2:
                            previous_value = self._name_history[-2]
                            self._name_history.pop()
                        else:
                            previous_value = ""
                        
                        self.name_entry.delete(0, 'end')
                        if previous_value:
                            self.name_entry.insert(0, previous_value)
                        print(f"SUCCESS: Undo manuel nom: → '{previous_value}'")
                        return "break"
                
                elif parent_widget == self.text_editor:
                    print("DEBUG: Undo manuel pour champ texte")
                    if self._text_history and len(self._text_history) >= 1:
                        if len(self._text_history) >= 2:
                            previous_value = self._text_history[-2]
                            self._text_history.pop()
                        else:
                            previous_value = ""
                        
                        self.text_editor.delete("1.0", "end")
                        if previous_value:
                            self.text_editor.insert("1.0", previous_value)
                        print(f"SUCCESS: Undo manuel texte: → '{previous_value[:30]}...'")
                        return "break"
            
            # Si l'identification par parent ne marche pas, essayer par comparaison directe
            if widget == self.name_entry or str(widget).find('entry') != -1:
                print("DEBUG: Undo manuel pour nom (identification directe)")
                if self._name_history:
                    if len(self._name_history) >= 2:
                        previous_value = self._name_history[-2]
                        self._name_history.pop()
                    else:
                        previous_value = ""
                    
                    self.name_entry.delete(0, 'end')
                    if previous_value:
                        self.name_entry.insert(0, previous_value)
                    print(f"SUCCESS: Undo manuel nom direct: → '{previous_value}'")
                    return "break"
            
            elif widget == self.text_editor or str(widget).find('text') != -1:
                print("DEBUG: Undo manuel pour texte (identification directe)")
                if self._text_history:
                    if len(self._text_history) >= 2:
                        previous_value = self._text_history[-2]
                        self._text_history.pop()
                    else:
                        previous_value = ""
                    
                    self.text_editor.delete("1.0", "end")
                    if previous_value:
                        self.text_editor.insert("1.0", previous_value)
                    print(f"SUCCESS: Undo manuel texte direct: → '{previous_value[:30]}...'")
                    return "break"
        
        except Exception as e:
            print(f"ERREUR: Undo manuel échoué: {e}")
        
        print("WARNING: Aucune méthode d'undo n'a fonctionné")
        return "break"
    
    def _save_text_to_history(self):
        """Sauvegarde l'état actuel dans l'historique."""
        if self.current_highlight:
            try:
                # Sauvegarder l'état du nom
                current_name = self.name_entry.get()
                if not self._name_history or (self._name_history and self._name_history[-1] != current_name):
                    if len(self._name_history) >= self._max_history:
                        self._name_history.pop(0)
                    self._name_history.append(current_name)
                    print(f"DEBUG: Nom sauvegardé dans historique: '{current_name}'")
                
                # Sauvegarder l'état du texte
                current_text = self.text_editor.get("1.0", "end-1c")
                if not self._text_history or (self._text_history and self._text_history[-1] != current_text):
                    if len(self._text_history) >= self._max_history:
                        self._text_history.pop(0)
                    self._text_history.append(current_text)
                    print(f"DEBUG: Texte sauvegardé dans historique: '{current_text[:30]}...'")
            
            except Exception as e:
                print(f"ERREUR: Sauvegarde historique échouée: {e}")
    
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
        
        # Bindings pour sauvegarde automatique et undo
        self.name_entry.bind("<Return>", self._on_enter_pressed)
        self.name_entry.bind("<Control-z>", self._on_undo_pressed)
        self.name_entry.bind("<FocusOut>", self._on_focus_out)
        self.name_entry.bind("<KeyPress>", self._on_key_press_name)
        
        # CORRECTION CTRL+Z: Forcer l'activation de l'undo sur le widget natif
        try:
            if hasattr(self.name_entry, '_entry'):
                self.name_entry._entry.configure(undo=True, maxundo=20)
                print("DEBUG: Undo activé sur name_entry")
        except Exception as e:
            print(f"DEBUG: Erreur activation undo name_entry: {e}")
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="SUPPRIMER FICHE",
            command=self._delete_highlight,
            fg_color="#cc4444",
            hover_color="#dd5555",
            height=35
        )
        clear_btn.pack(fill="x")
        
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
        
        # Bindings pour sauvegarde automatique et undo
        self.text_editor.bind("<Return>", self._on_enter_pressed)
        self.text_editor.bind("<Control-z>", self._on_undo_pressed)
        self.text_editor.bind("<FocusOut>", self._on_focus_out)
        self.text_editor.bind("<KeyPress>", self._on_key_press_text)
        
        # CORRECTION CTRL+Z: Forcer l'activation de l'undo sur le widget natif
        try:
            if hasattr(self.text_editor, '_textbox'):
                self.text_editor._textbox.configure(undo=True, maxundo=20)
                print("DEBUG: Undo activé sur text_editor")
        except Exception as e:
            print(f"DEBUG: Erreur activation undo text_editor: {e}")
        
        # Afficher un message par défaut
        self._show_default_message()
    
    def _show_default_message(self):
        """Affiche un message par défaut quand aucun highlight n'est sélectionné."""
        self.page_label.configure(text="Page: -")
        self.confidence_label.configure(text="Confiance: -")
        self.name_entry.delete(0, 'end')
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "Sélectionnez un highlight ci-dessus pour l'afficher ici...")
        self.current_highlight = None
        
        # CORRECTION BUG MODIF: Réinitialiser l'état initial
        self.initial_text = ""
        self.initial_name = ""
    
    def show_highlight(self, highlight_data):
        """Affiche un highlight pour édition."""
        # Sauvegarder l'état actuel avant de changer
        self._save_text_to_history()
        
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
        
        # CORRECTION BUG MODIF: Stocker l'état initial pour comparaison future
        self.initial_name = custom_name
        self.initial_text = text
        print(f"DEBUG: État initial sauvegardé - Nom: '{self.initial_name}', Texte: '{self.initial_text[:30]}...'")
        
        # Réinitialiser l'historique pour le nouveau highlight
        self._text_history.clear()
        self._name_history.clear()
    
    def _save_changes(self):
        """Sauvegarde les modifications."""
        if not self.current_highlight:
            return
        
        # Récupérer les nouvelles valeurs
        new_text = self.text_editor.get("1.0", "end-1c")
        new_name = self.name_entry.get().strip()
        
        # CORRECTION BUG MODIF: Vérifier s'il y a vraiment eu des modifications
        has_changes = False
        
        # Comparer le texte
        if new_text != self.initial_text:
            has_changes = True
            print(f"DEBUG: Changement texte détecté: '{self.initial_text[:30]}...' → '{new_text[:30]}...'")
        
        # Comparer le nom
        if new_name != self.initial_name:
            has_changes = True
            print(f"DEBUG: Changement nom détecté: '{self.initial_name}' → '{new_name}'")
        
        # Mettre à jour les données
        self.current_highlight['text'] = new_text
        if new_name:
            self.current_highlight['custom_name'] = new_name
        elif 'custom_name' in self.current_highlight:
            del self.current_highlight['custom_name']
        
        # CORRECTION BUG MODIF: Marquer comme modifié SEULEMENT s'il y a vraiment eu des changements
        if has_changes:
            self.current_highlight['modified'] = True
            self.current_highlight['modified_date'] = datetime.now().isoformat()
            print("DEBUG: Highlight marqué comme modifié")
        else:
            print("DEBUG: Aucun changement détecté, pas de modification marquée")
        
        # Callback de sauvegarde
        if self.on_save:
            self.on_save(self.current_highlight)
    
    def _delete_highlight(self):
        """Supprime la fiche highlight actuellement sélectionnée."""
        if not self.current_highlight:
            messagebox.showwarning("Aucune sélection", "Aucun highlight sélectionné à supprimer.")
            return
        
        # Obtenir le nom de la fiche pour la confirmation
        page = self.current_highlight.get('page', '?')
        name = self.current_highlight.get('custom_name', f"Page {page}")
        
        # Demander confirmation
        if messagebox.askyesno(
            "Supprimer le highlight",
            f"Êtes-vous sûr de vouloir supprimer définitivement :\n\n'{name}'\n\nCette action est irréversible."
        ):
            # Notifier le parent pour supprimer la fiche
            if self.on_delete:
                self.on_delete(self.current_highlight)
            
            # Revenir à l'état par défaut
            self._show_default_message()


class MainWindow(ctk.CTk):
    """
    Fenêtre principale de l'application AllamBik v3 - Version corrigée.
    """
    
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        
        self.viewmodel = viewmodel
        self.async_loop = None
        
        # Variables d'état (AVANT _create_ui())
        self.view_mode = "grid"  # "grid" (2 col) ou "list" (1 col)
        self.current_search = ""
        self.extraction_file_path = None  # Chemin vers le fichier d'extraction
        self.selected_card = None  # Fiche actuellement sélectionnée
        
        # Pour gérer les mises à jour
        self._update_queue = []
        
        self._setup_window()
        self._create_ui()
        self._bind_viewmodel()
        self._start_update_loop()
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
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
            text="ALLAMBIK v3.0",
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
        
        # Bouton Arrêter
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
        self.stop_button.pack(fill="x", padx=20, pady=(5, 5))
        
        # Bouton Détection automatique du nombre de pages
        self.detect_button = ctk.CTkButton(
            controls_section,
            text="DETECTER NOMBRE DE PAGES",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="#ff6600",  # Orange
            hover_color="#ff8800",
            command=self._on_detect_pages_clicked
        )
        self.detect_button.pack(fill="x", padx=20, pady=(5, 5))

        
        # BOUTON EXPORT WORD - DIRECTEMENT SOUS ARRÊTER
        self.export_word_button = ctk.CTkButton(
            controls_section,
            text="EXPORTER WORD",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color="#2d5a2d",  # Vert foncé pour le distinguer
            hover_color="#3d6a3d",
            command=self._on_export_word_clicked
        )
        self.export_word_button.pack(fill="x", padx=20, pady=(5, 15))
        
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
    
    def _create_right_panel(self, parent):
        """Crée le panneau droit avec highlights et panneau d'édition."""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configuration - highlights en haut, édition en bas
        right_panel.grid_rowconfigure(0, weight=2)  # Highlights prennent plus d'espace
        right_panel.grid_rowconfigure(1, weight=1)  # Panneau d'édition en bas
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Container pour highlights
        highlights_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        highlights_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
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
            text="LISTE",
            width=60,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#4a4a4a" if self.view_mode != "list" else self.colors['accent'],
            hover_color="#5a5a5a",
            command=self._set_list_view
        )
        self.list_view_button.pack(side="right", padx=(5, 0))
        
        # Bouton mode grille (2 colonnes)
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
        
        # Zone de recherche
        search_frame = ctk.CTkFrame(highlights_section, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Rechercher dans les highlights...",
            font=ctk.CTkFont(size=11),
            height=30
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # Bouton effacer recherche
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
        
        # Grille de highlights
        self.highlights_grid = HighlightGrid(
            highlights_section,
            columns=2,  # Démarre en mode grille
            fg_color="transparent",
            on_edit_requested=self._on_edit_requested,
            on_highlight_selected=self._on_highlight_selected  # NOUVEAU: sélection simple
        )
        self.highlights_grid.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Panneau d'édition intégré (TOUJOURS VISIBLE)
        self.edit_panel = IntegratedEditPanel(
            right_panel,
            on_save=self._on_edit_saved,
            on_cancel=self._on_edit_cancelled,
            on_delete=self._on_highlight_deleted
        )
        self.edit_panel.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
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
        """Recrée la grille avec le nombre de colonnes spécifié - CORRECTION BUG ASCENSEUR."""
        
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
        if columns < 4:
            for i in range(columns, 4):
                self.highlights_grid.grid_columnconfigure(i, weight=0, uniform="")
        
        # Forcer la mise à jour du scrollable frame
        self.highlights_grid.update_idletasks()
        
        # Attendre un cycle d'événements puis restaurer les données
        self.after_idle(lambda: self._restore_highlights_data(highlights_data))
    
    def _restore_highlights_data(self, highlights_data):
        """Restaure les données des highlights dans la grille modifiée."""
        # Sauvegarder la fiche actuellement sélectionnée
        selected_highlight = None
        if self.selected_card and self.selected_card.highlight_data:
            selected_highlight = self.selected_card.highlight_data.copy()
        
        # Restaurer toutes les données
        for highlight_data in highlights_data:
            self.highlights_grid.add_highlight(highlight_data)
        
        # Restaurer la sélection si possible
        if selected_highlight:
            self.after_idle(lambda: self._restore_selection(selected_highlight))
        
        self._update_highlights_count()
        
        # Forcer la mise à jour complète de l'affichage
        self.highlights_grid.update_idletasks()
        self.update_idletasks()
    
    def _restore_selection(self, selected_highlight):
        """Restaure la sélection après changement de mode."""
        for card in self.highlights_grid.cards:
            if (card.highlight_data.get('page') == selected_highlight.get('page') and
                card.highlight_data.get('text', '')[:50] == selected_highlight.get('text', '')[:50]):
                card.set_selected(True)
                self.selected_card = card
                print(f"DEBUG: Sélection restaurée - Page {selected_highlight.get('page')}")
                break
    
    # Gestion de l'édition intégrée
    
    def _on_highlight_selected(self, highlight_data):
        """NOUVEAU: Callback quand un highlight est sélectionné (simple clic)."""
        # CORRECTION 1: Sauvegarder avant de changer de fiche
        if hasattr(self, 'edit_panel') and self.edit_panel.current_highlight:
            self.edit_panel._save_changes()
        
        # CORRECTION 2: Désélectionner la fiche précédente de manière robuste
        if self.selected_card:
            try:
                self.selected_card.set_selected(False)
            except:
                pass  # La carte peut avoir été détruite
        
        # CORRECTION 3: Trouver et sélectionner la nouvelle fiche de manière robuste
        self.selected_card = None
        for card in self.highlights_grid.cards:
            # Critères multiples pour identifier la bonne carte
            if (card.highlight_data.get('page') == highlight_data.get('page') and
                card.highlight_data.get('text', '')[:50] == highlight_data.get('text', '')[:50]):
                try:
                    card.set_selected(True)
                    self.selected_card = card
                    print(f"DEBUG: Fiche sélectionnée - Page {highlight_data.get('page')}")
                    break
                except:
                    print(f"ERREUR: Impossible de sélectionner la carte Page {highlight_data.get('page')}")
        
        # Afficher dans le panneau d'édition
        self.edit_panel.show_highlight(highlight_data)
    
    def _on_edit_requested(self, highlight_data):
        """Callback quand l'édition d'un highlight est demandée (double-clic)."""
        self.edit_panel.show_highlight(highlight_data)
    
    def _on_edit_saved(self, updated_data):
        """Callback quand un highlight est sauvegardé après édition."""
        print(f"DEBUG: Sauvegarde highlight: Page {updated_data.get('page')}, Nom: {updated_data.get('custom_name', 'Sans nom')}")
        
        try:
            self.highlights_grid.update_highlight(updated_data)
            self._save_to_extraction_file()
            print(f"SUCCESS: Highlight sauvegardé: {updated_data.get('custom_name', 'Sans nom')}")
            
        except Exception as e:
            print(f"ERREUR: Erreur sauvegarde highlight: {e}")
            self._force_refresh_all_cards()
    
    def _on_edit_cancelled(self):
        """Callback quand l'édition est annulée."""
        print("INFO: Édition annulée")
    
    def _on_highlight_deleted(self, highlight_data):
        """Callback quand un highlight est supprimé depuis le panneau d'édition."""
        print(f"DEBUG: Suppression highlight: Page {highlight_data.get('page')}, Nom: {highlight_data.get('custom_name', 'Sans nom')}")
        
        # CORRECTION: Nettoyer la sélection si c'est la fiche sélectionnée qui est supprimée
        if (self.selected_card and 
            self.selected_card.highlight_data.get('page') == highlight_data.get('page') and
            self.selected_card.highlight_data.get('text', '')[:50] == highlight_data.get('text', '')[:50]):
            self.selected_card = None
            self.edit_panel._show_default_message()
        
        try:
            # Supprimer de la grille
            self.highlights_grid._on_highlight_deleted(highlight_data)
            self._update_highlights_count()
            self._save_to_extraction_file()
            print(f"SUCCESS: Highlight supprimé: {highlight_data.get('custom_name', 'Sans nom')}")
            
        except Exception as e:
            print(f"ERREUR: Erreur suppression highlight: {e}")
    
    def _force_refresh_all_cards(self):
        """Force le rafraîchissement de toutes les cartes."""
        try:
            for i, (card, data) in enumerate(zip(self.highlights_grid.cards, self.highlights_grid.highlights_data)):
                card.update_data(data)
            print("INFO: Toutes les cartes ont été rafraîchies")
        except Exception as e:
            print(f"ERREUR: Erreur rafraîchissement: {e}")
    
    # Gestion des fichiers
    
    def _save_to_extraction_file(self):
        """Sauvegarde les modifications dans le fichier d'extraction."""
        if not self.extraction_file_path or not os.path.exists(self.extraction_file_path):
            self._find_or_create_extraction_file()
        
        if self.extraction_file_path:
            try:
                highlights_data = self.highlights_grid.get_highlights_data()
                
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
                
                with open(self.extraction_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"INFO: Fichier d'extraction mis à jour: {self.extraction_file_path}")
                
            except Exception as e:
                print(f"ERREUR: Erreur lors de la sauvegarde: {e}")
    
    def _find_or_create_extraction_file(self):
        """Trouve ou crée le fichier d'extraction."""
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
    
    # Export Word - VERSION CORRIGÉE SANS EMOJIS
    
        def _on_export_word_clicked(self):
        """Export Word avec tous les highlights."""
        from tkinter import filedialog, messagebox
        from datetime import datetime
        import os
        
        # Utiliser ALL highlights stockés
        highlights_to_export = getattr(self, 'all_highlights', self.viewmodel.highlights)
        
        if not highlights_to_export:
            messagebox.showwarning("Export", "Aucun highlight à exporter")
            return
        
        print(f"Export de {len(highlights_to_export)} highlights...")
        
        try:
            # Nom par défaut
            default_name = f"highlights_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
            
            # Dialogue sauvegarde
            file_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Word", "*.docx"), ("All", "*.*")],
                initialfile=default_name,
                title="Exporter les highlights"
            )
            
            if file_path:
                # Export
                from src.infrastructure.export.word_exporter import WordExporter
                exporter = WordExporter()
                exporter.export_to_word(highlights_to_export, file_path)
                
                # Confirmation
                messagebox.showinfo(
                    "Export réussi",
                    f"{len(highlights_to_export)} highlights exportés vers:
{os.path.basename(file_path)}"
                )
                print(f"✓ Export terminé: {file_path}")
                
        except Exception as e:
            print(f"Erreur export: {e}")
            messagebox.showerror("Erreur", f"Export impossible:
{str(e)}")
    
    def _on_search_changed(self, event):
        """Gère les changements de recherche avec filtrage et surbrillance."""
        search_text = self.search_entry.get().lower().strip()
        self.current_search = search_text
        
        if not search_text:
            # Afficher toutes les fiches si recherche vide
            self._show_all_cards()
        else:
            # Filtrer et surligner les fiches correspondantes
            self._filter_and_highlight_cards(search_text)
        
        self._update_highlights_count()
    
    def _show_all_cards(self):
        """Affiche toutes les fiches sans filtrage."""
        for card in self.highlights_grid.cards:
            try:
                card.pack_info()  # Vérifier si la carte est affichée
                card.pack(fill="x", padx=5, pady=5)
            except:
                # Si pas en mode pack, utiliser grid
                try:
                    row = self.highlights_grid.cards.index(card) // self.highlights_grid.columns
                    col = self.highlights_grid.cards.index(card) % self.highlights_grid.columns
                    card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                except:
                    pass
            
            # Retirer le surlignage de recherche
            card._remove_search_highlight()
    
    def _filter_and_highlight_cards(self, search_text):
        """Filtre et surligne les fiches selon la recherche."""
        visible_count = 0
        
        for i, card in enumerate(self.highlights_grid.cards):
            highlight_data = card.highlight_data
            
            # Vérifier si la recherche correspond
            text_match = search_text in highlight_data.get('text', '').lower()
            name_match = search_text in highlight_data.get('custom_name', '').lower()
            page_match = search_text in str(highlight_data.get('page', ''))
            
            if text_match or name_match or page_match:
                # Afficher la carte
                try:
                    row = visible_count // self.highlights_grid.columns
                    col = visible_count % self.highlights_grid.columns
                    card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                    visible_count += 1
                    
                    # Ajouter surlignage
                    card._add_search_highlight(search_text)
                    
                except Exception as e:
                    print(f"ERREUR: Affichage carte {i}: {e}")
            else:
                # Cacher la carte
                try:
                    card.grid_remove()
                    card._remove_search_highlight()
                except:
                    pass
    
    def _clear_search(self):
        """Efface la recherche et affiche toutes les fiches."""
        self.search_entry.delete(0, "end")
        self.current_search = ""
        self._show_all_cards()
        self._update_highlights_count()
    
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
        print(f"INFO: Zone de scan définie: {w}x{h} pixels à la position ({x},{y})")
    
    def _on_start_clicked(self):
        """Gère le clic sur Démarrer."""
        # Utiliser les pages détectées si disponibles
        if hasattr(self.viewmodel, 'detected_pages') and self.viewmodel.detected_pages:
            total_pages = self.viewmodel.detected_pages
            print(f"INFO: Utilisation automatique de {total_pages} pages détectées")
            
            if self.async_loop:
                asyncio.run_coroutine_threadsafe(
                    self.viewmodel.start_extraction_command(total_pages),
                    self.async_loop
                )
            return
        
        # Sinon demander manuellement
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
    
    def _on_highlights_changed(self, highlights):
        """Affiche les highlights avec limite pour performance."""
        # Stocker TOUS les highlights pour export
        self.all_highlights = list(highlights) if highlights else []
        
        # Trouver le conteneur scrollable
        scroll_container = getattr(self, 'highlight_list_scroll', None)
        if not scroll_container:
            print("ERREUR: Conteneur scrollable non trouvé")
            return
        
        # Nettoyer
        for widget in scroll_container.winfo_children():
            widget.destroy()
        
        # Limites
        DISPLAY_LIMIT = 200
        total = len(self.all_highlights)
        
        print(f"Affichage: {min(total, DISPLAY_LIMIT)}/{total} highlights")
        
        # Import
        from src.presentation.gui.components.highlight_card import HighlightCard
        import customtkinter as ctk
        
        # Créer les cartes (limitées)
        display_items = self.all_highlights[:DISPLAY_LIMIT]
        
        for i, highlight in enumerate(display_items):
            try:
                card = HighlightCard(
                    scroll_container,
                    highlight,
                    on_click=lambda h=highlight: self._on_highlight_selected(h)
                )
                card.pack(fill="x", padx=10, pady=5)
                
                # Update périodique
                if i % 25 == 0:
                    self.window.update_idletasks()
                    
            except Exception as e:
                print(f"Erreur création carte {i}: {e}")
                break
        
        # Titre
        if hasattr(self, 'highlight_list_title'):
            self.highlight_list_title.configure(
                text=f"HIGHLIGHTS EXTRAITS ({total})"
            )
        
        # Info si limité
        if total > DISPLAY_LIMIT:
            info = ctk.CTkLabel(
                scroll_container,
                text=f"⚠️ Performance: {DISPLAY_LIMIT}/{total} affichés
Utilisez Export Word pour tout obtenir",
                text_color="orange",
                font=("Arial", 12, "bold")
            )
            info.pack(pady=20)
        
        print(f"✓ {len(display_items)} cartes créées")
    

    def _on_detect_pages_clicked(self):
        """Lance la détection automatique du nombre de pages."""
        print("INFO: Detection automatique demandee")
        
        from tkinter import messagebox
        
        # Vérifier si le détecteur existe
        if not hasattr(self.viewmodel, 'page_detector') or self.viewmodel.page_detector is None:
            print("INFO: Detecteur non configure")
            messagebox.showinfo(
                "Détection non disponible",
                "La détection automatique n'est pas encore configurée.\n\n" +
                "Vous pouvez entrer le nombre de pages manuellement."
            )
            return
        
        # Demander confirmation
        if messagebox.askyesno("Détection des pages", "Lancer la détection automatique du nombre de pages?"):
            print("INFO: Detection acceptee par l'utilisateur")
            self.detect_button.configure(state="disabled", text="DETECTION EN COURS...")
            
            # Si detect_pages_command existe
            if hasattr(self.viewmodel, 'detect_pages_command') and self.async_loop:
                import asyncio
                
                def on_complete(future):
                    self.detect_button.configure(state="normal")
                    try:
                        result = future.result()
                        if self.viewmodel.detected_pages:
                            self.detect_button.configure(
                                text=f"✓ {self.viewmodel.detected_pages} PAGES",
                                fg_color="#00aa00"
                            )
                            print(f"SUCCESS: {self.viewmodel.detected_pages} pages detectees")
                    except Exception as e:
                        print(f"ERREUR: {e}")
                        self.detect_button.configure(text="DETECTER NOMBRE DE PAGES")
                
                future = asyncio.run_coroutine_threadsafe(
                    self.viewmodel.detect_pages_command(),
                    self.async_loop
                )
                future.add_done_callback(lambda f: self.after(0, lambda: on_complete(f)))
            else:
                # Fallback: simulation simple
                print("INFO: Mode test - simulation de detection")
                messagebox.showinfo("Test", "Le détecteur sera bientôt fonctionnel!")
                self.detect_button.configure(state="normal", text="DETECTER NOMBRE DE PAGES")


    def _on_state_changed(self, state: ViewState):
        """Met à jour l'UI selon l'état."""
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
        """Met à jour la progression."""
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
    
    def _update_highlight_display_batch(self, highlights):
        """Met à jour l'affichage par batch pour performances."""
        self.all_highlights = highlights
        total = len(highlights)
        
        # Si trop d'éléments, afficher par batch
        if total > self.max_display_items:
            # Afficher seulement les premiers éléments
            display_items = highlights[:self.max_display_items]
            
            # Ajouter un indicateur
            print(f"INFO: Affichage de {self.max_display_items}/{total} highlights")
            self._display_highlights_subset(display_items, total)
        else:
            # Afficher tout normalement
            self._display_highlights_subset(highlights, total)
    
    def _display_highlights_subset(self, items, total):
        """Affiche un sous-ensemble des highlights."""
        # Code d'affichage ici
        # Mettre à jour le titre avec le compte total
        if hasattr(self, 'highlight_list_title'):
            self.highlight_list_title.configure(
                text=f"HIGHLIGHTS EXTRAITS ({total})"
            )

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
            self._save_to_extraction_file()
        
        self._schedule_update(update)