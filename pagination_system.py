"""
pagination_system.py - Système de pagination pour AllamBik
Module indépendant qui peut être testé sans toucher au code principal
"""
import customtkinter as ctk
import time
from typing import List, Any, Callable

class PaginatedHighlightDisplay:
    """Système de pagination pour gérer efficacement 2000+ highlights."""
    
    def __init__(self, parent_frame, items_per_page: int = 100):
        self.parent = parent_frame
        self.items_per_page = items_per_page
        self.current_page = 0
        self.all_items = []
        self.display_widgets = []
        self.on_item_click = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Crée l'interface de pagination."""
        # Frame principale
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header avec info
        self.info_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.info_frame.pack(fill="x", pady=(0, 10))
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Aucun highlight chargé",
            font=("Arial", 14, "bold")
        )
        self.info_label.pack(pady=10)
        
        # Frame scrollable pour les éléments
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            height=400
        )
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Frame de navigation (cachée initialement)
        self.nav_frame = ctk.CTkFrame(self.main_frame, height=60)
        
        # Boutons de navigation
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Page précédente",
            command=self._prev_page,
            width=150
        )
        self.prev_btn.pack(side="left", padx=10, pady=10)
        
        self.page_info = ctk.CTkLabel(
            self.nav_frame,
            text="",
            font=("Arial", 12)
        )
        self.page_info.pack(side="left", expand=True)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Page suivante ▶",
            command=self._next_page,
            width=150
        )
        self.next_btn.pack(side="right", padx=10, pady=10)
        
        # Jump to page
        self.jump_frame = ctk.CTkFrame(self.nav_frame)
        self.jump_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(self.jump_frame, text="Aller à:").pack(side="left", padx=5)
        self.page_entry = ctk.CTkEntry(self.jump_frame, width=50)
        self.page_entry.pack(side="left", padx=5)
        ctk.CTkButton(
            self.jump_frame,
            text="Go",
            command=self._jump_to_page,
            width=40
        ).pack(side="left")
    
    def load_items(self, items: List[Any], create_widget_func: Callable = None):
        """Charge les éléments et affiche la première page."""
        start_time = time.time()
        
        self.all_items = items
        self.current_page = 0
        self.create_widget_func = create_widget_func or self._default_create_widget
        
        # Calculer le nombre de pages
        self.total_pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
        
        # Afficher ou cacher la navigation
        if self.total_pages > 1:
            self.nav_frame.pack(fill="x", pady=(10, 0))
        else:
            self.nav_frame.pack_forget()
        
        # Afficher la première page
        self._display_current_page()
        
        elapsed = time.time() - start_time
        print(f"✓ {len(items)} éléments chargés en {elapsed:.3f}s")
        print(f"  Pages: {self.total_pages}, Par page: {self.items_per_page}")
    
    def _display_current_page(self):
        """Affiche uniquement les éléments de la page courante."""
        # Nettoyer l'affichage
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.display_widgets.clear()
        
        # Calculer les indices
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.all_items))
        
        # Créer les widgets pour cette page seulement
        page_items = self.all_items[start_idx:end_idx]
        
        for i, item in enumerate(page_items, start=start_idx):
            widget = self.create_widget_func(self.scroll_frame, item, i)
            widget.pack(fill="x", padx=5, pady=3)
            self.display_widgets.append(widget)
        
        # Mettre à jour les infos
        self._update_navigation()
    
    def _default_create_widget(self, parent, item, index):
        """Créateur de widget par défaut."""
        frame = ctk.CTkFrame(parent, height=60)
        
        # Header avec numéro et info
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(
            header,
            text=f"#{index + 1}",
            font=("Arial", 10, "bold"),
            text_color="cyan"
        ).pack(side="left")
        
        # Contenu
        text = str(item)[:200] + "..." if len(str(item)) > 200 else str(item)
        ctk.CTkLabel(
            frame,
            text=text,
            anchor="w",
            justify="left"
        ).pack(fill="x", padx=10, pady=5)
        
        return frame
    
    def _update_navigation(self):
        """Met à jour les contrôles de navigation."""
        # Info principale
        total = len(self.all_items)
        start = self.current_page * self.items_per_page + 1
        end = min((self.current_page + 1) * self.items_per_page, total)
        
        self.info_label.configure(
            text=f"Affichage {start}-{end} sur {total} highlights"
        )
        
        # Info de page
        self.page_info.configure(
            text=f"Page {self.current_page + 1} / {self.total_pages}"
        )
        
        # États des boutons
        self.prev_btn.configure(
            state="normal" if self.current_page > 0 else "disabled"
        )
        self.next_btn.configure(
            state="normal" if self.current_page < self.total_pages - 1 else "disabled"
        )
    
    def _prev_page(self):
        """Page précédente."""
        if self.current_page > 0:
            self.current_page -= 1
            self._display_current_page()
    
    def _next_page(self):
        """Page suivante."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._display_current_page()
    
    def _jump_to_page(self):
        """Sauter à une page spécifique."""
        try:
            page_num = int(self.page_entry.get()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self._display_current_page()
        except ValueError:
            pass
    
    def get_all_items(self):
        """Retourne tous les éléments (pour export)."""
        return self.all_items


# Test standalone
if __name__ == "__main__":
    print("TEST DU SYSTÈME DE PAGINATION")
    print("="*60)
    
    root = ctk.CTk()
    root.title("Test Pagination AllamBik")
    root.geometry("1000x700")
    
    # Créer des données de test
    test_data = []
    for i in range(2000):
        test_data.append({
            'page': i // 3 + 1,
            'text': f'Highlight #{i+1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
                   f'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
            'confidence': 85 + (i % 15)
        })
    
    # Fonction de création de widget personnalisée
    def create_highlight_widget(parent, item, index):
        frame = ctk.CTkFrame(parent, height=80)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(
            header,
            text=f"#{index + 1} - Page {item['page']}",
            font=("Arial", 11, "bold"),
            text_color="#FF6B35"
        ).pack(side="left")
        
        ctk.CTkLabel(
            header,
            text=f"Confiance: {item['confidence']}%",
            font=("Arial", 10),
            text_color="gray"
        ).pack(side="right")
        
        # Texte
        ctk.CTkLabel(
            frame,
            text=item['text'][:150] + "...",
            anchor="w",
            justify="left",
            wraplength=800
        ).pack(fill="x", padx=10, pady=(5, 10))
        
        return frame
    
    # Créer le système paginé
    paginated = PaginatedHighlightDisplay(root, items_per_page=50)
    
    # Charger les données
    print(f"Chargement de {len(test_data)} éléments...")
    paginated.load_items(test_data, create_highlight_widget)
    
    # Bouton d'export pour test
    export_btn = ctk.CTkButton(
        root,
        text=f"Export All ({len(test_data)} items)",
        command=lambda: print(f"Export de {len(paginated.get_all_items())} éléments")
    )
    export_btn.pack(pady=10)
    
    root.mainloop()
