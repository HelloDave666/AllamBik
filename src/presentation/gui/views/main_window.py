"""
Fenêtre principale - Vue principale de l'application
"""
import customtkinter as ctk
import asyncio
from typing import Optional, Tuple
import threading

from src.presentation.gui.viewmodels.main_viewmodel import MainViewModel, ViewState, HighlightViewModel
from src.presentation.gui.components.progress_circle import ProgressCircle
from src.presentation.gui.components.highlight_card import HighlightGrid
from src.presentation.gui.components.zone_picker import ZonePickerButton


class MainWindow(ctk.CTk):
    """
    Fenêtre principale de l'application Alambik v3.
    Suit le pattern MVVM avec binding au ViewModel.
    """
    
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        
        self.viewmodel = viewmodel
        self.async_loop = None  # Sera défini par l'app
        self._setup_window()
        self._create_ui()
        self._bind_viewmodel()
        
        # Pour gérer les mises à jour depuis les threads async
        self._update_queue = []
        self._start_update_loop()
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
        self.title("Alambik v3.0 - Extracteur de Highlights Kindle")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Couleurs personnalisées
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
        
        # Panneau gauche
        self._create_left_panel(main_container)
        
        # Panneau droit
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
        
        # Frame pour les boutons Valider/Arrêter
        button_frame = ctk.CTkFrame(controls_section, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(5, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        self.validate_button = ctk.CTkButton(
            button_frame,
            text="VALIDER",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color=self.colors['success'],
            hover_color="#00cc66",
            state="disabled",
            command=self._on_validate_clicked
        )
        self.validate_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="ARRÊTER",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color=self.colors['bg_tertiary'],
            hover_color=self.colors['error'],
            state="disabled",
            command=self._on_stop_clicked
        )
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
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
        """Crée le panneau droit avec highlights et logs."""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configuration de la grille
        right_panel.grid_rowconfigure(0, weight=3)  # Highlights
        right_panel.grid_rowconfigure(1, weight=1)  # Logs
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Section Highlights
        highlights_section = self._create_section_frame(right_panel, "HIGHLIGHTS EXTRAITS")
        highlights_section.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.highlights_grid = HighlightGrid(
            highlights_section,
            columns=2,
            fg_color="transparent"
        )
        self.highlights_grid.pack(fill="both", expand=True, padx=15, pady=(10, 15))
        
        # Section Logs
        logs_section = self._create_section_frame(right_panel, "ACTIVITÉ")
        logs_section.grid(row=1, column=0, sticky="nsew")
        
        self.logs_textbox = ctk.CTkTextbox(
            logs_section,
            fg_color=self.colors['bg_primary'],
            text_color=self.colors['text_secondary'],
            font=ctk.CTkFont(size=10),
            wrap="word"
        )
        self.logs_textbox.pack(fill="both", expand=True, padx=15, pady=(10, 15))
    
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
        
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.pack(pady=(15, 5))
        
        return section
    
    def _bind_viewmodel(self):
        """Lie le ViewModel à la vue."""
        self.viewmodel.on_state_changed = self._on_state_changed
        self.viewmodel.on_progress_changed = self._on_progress_changed
        self.viewmodel.on_highlight_added = self._on_highlight_added
        self.viewmodel.on_log_added = self._on_log_added
    
    def _start_update_loop(self):
        """Démarre la boucle de mise à jour UI."""
        def update_ui():
            try:
                # Traiter les mises à jour en attente
                for update_func in self._update_queue[:]:
                    update_func()
                    self._update_queue.remove(update_func)
            except:
                pass
            
            # Replanifier
            self.after(100, update_ui)
        
        self.after(100, update_ui)
    
    def _schedule_update(self, func):
        """Planifie une mise à jour UI thread-safe."""
        self._update_queue.append(func)
    
    # Handlers d'événements UI
    
    def _on_zone_selected(self, zone: Tuple[int, int, int, int]):
        """Callback quand une zone est sélectionnée."""
        # Stocker la zone pour l'extraction
        if hasattr(self.viewmodel, 'custom_scan_zone'):
            self.viewmodel.custom_scan_zone = zone
        else:
            self.viewmodel.custom_scan_zone = zone
        
        # Log
        x, y, w, h = zone
        self.viewmodel.add_log(f"Zone de scan définie: {w}x{h} pixels à la position ({x},{y})")
    
    def _on_start_clicked(self):
        """Gère le clic sur Démarrer."""
        # Demander le nombre de pages
        dialog = ctk.CTkInputDialog(
            text="Nombre total de pages du livre:",
            title="Configuration"
        )
        pages_str = dialog.get_input()
        
        if pages_str:
            try:
                total_pages = int(pages_str)
                if total_pages > 0:
                    # Lancer dans la boucle asyncio du thread dédié
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
    
    def _on_validate_clicked(self):
        """Gère le clic sur Valider."""
        if self.async_loop:
            asyncio.run_coroutine_threadsafe(
                self.viewmodel.validate_phase1_command(),
                self.async_loop
            )
    
    # Callbacks du ViewModel
    
    def _on_state_changed(self, state: ViewState):
        """Met à jour l'UI selon l'état."""
        def update():
            # Mettre à jour les boutons
            self.start_button.configure(
                state="normal" if self.viewmodel.can_start else "disabled"
            )
            self.stop_button.configure(
                state="normal" if self.viewmodel.can_stop else "disabled"
            )
            self.validate_button.configure(
                state="normal" if self.viewmodel.can_validate else "disabled"
            )
            
            # Mettre à jour les couleurs selon l'état
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
            self.highlights_grid.add_highlight(
                page=highlight.page,
                text=highlight.text,
                confidence=highlight.confidence
            )
        
        self._schedule_update(update)
    
    def _on_log_added(self, log_entry: str):
        """Ajoute une entrée de log."""
        def update():
            self.logs_textbox.insert("end", log_entry + "\n")
            self.logs_textbox.see("end")
        
        self._schedule_update(update)