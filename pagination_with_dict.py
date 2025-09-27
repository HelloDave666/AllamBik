"""
pagination_with_dict.py - Test avec conversion en dictionnaire
"""
import customtkinter as ctk
import time
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from src.presentation.gui.components.highlight_card import HighlightCard
from src.domain.entities.highlight import Highlight

class PaginatedCardDisplay:
    """Pagination qui utilise les vrais HighlightCard."""
    
    def __init__(self, parent_frame, items_per_page: int = 100):
        self.parent = parent_frame
        self.items_per_page = items_per_page
        self.current_page = 0
        self.all_highlights = []
        self.card_widgets = []
        self.on_card_click = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface qui ressemble exactement à l'originale."""
        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent",
            height=500
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.nav_frame = ctk.CTkFrame(self.container, height=50, fg_color="transparent")
        
        button_style = {
            "height": 35,
            "font": ("Arial", 12),
            "fg_color": "#FF6B35",
            "hover_color": "#FF8C42"
        }
        
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Page précédente",
            command=self._prev_page,
            width=140,
            **button_style
        )
        self.prev_btn.pack(side="left", padx=5, pady=5)
        
        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="",
            font=("Arial", 12),
            text_color="gray"
        )
        self.page_label.pack(side="left", expand=True)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Page suivante ▶",
            command=self._next_page,
            width=140,
            **button_style
        )
        self.next_btn.pack(side="right", padx=5, pady=5)
    
    def load_highlights(self, highlights, on_click_callback=None):
        """Charge les highlights avec leur callback."""
        self.all_highlights = highlights
        self.on_card_click = on_click_callback
        self.current_page = 0
        
        self.total_pages = max(1, (len(highlights) + self.items_per_page - 1) // self.items_per_page)
        
        if self.total_pages > 1:
            self.nav_frame.pack(fill="x", pady=(5, 0))
        else:
            self.nav_frame.pack_forget()
        
        self._display_page()
        
        print(f"✓ {len(highlights)} highlights chargés, {self.total_pages} pages")
    
    def _display_page(self):
        """Affiche une page avec les vrais HighlightCard."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.card_widgets.clear()
        
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.all_highlights))
        
        for highlight in self.all_highlights[start:end]:
            # Convertir l'objet Highlight en dictionnaire si nécessaire
            if hasattr(highlight, '__dict__'):
                # C'est un objet, le convertir en dict
                highlight_dict = {
                    'page': getattr(highlight, 'page_number', 0),
                    'extracted_text': getattr(highlight, 'text', ''),
                    'confidence': getattr(highlight, 'confidence', 0),
                    'custom_name': getattr(highlight, 'custom_name', f'Highlight {getattr(highlight, "highlight_number", "")}')
                }
            else:
                # C'est déjà un dict
                highlight_dict = highlight
            
            card = HighlightCard(
                self.scroll_frame,
                highlight_dict,  # Passer le dictionnaire
                on_click=lambda h=highlight: self._on_card_clicked(h)
            )
            card.pack(fill="x", padx=10, pady=5)
            self.card_widgets.append(card)
        
        self._update_nav()
    
    def _on_card_clicked(self, highlight):
        if self.on_card_click:
            self.on_card_click(highlight)
    
    def _update_nav(self):
        start = self.current_page * self.items_per_page + 1
        end = min((self.current_page + 1) * self.items_per_page, len(self.all_highlights))
        total = len(self.all_highlights)
        
        self.page_label.configure(
            text=f"Page {self.current_page + 1}/{self.total_pages} | "
                 f"Affichage {start}-{end} sur {total}"
        )
        
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
    
    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._display_page()
    
    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._display_page()
    
    def get_all_highlights(self):
        return self.all_highlights


# Test avec des dictionnaires
if __name__ == "__main__":
    print("TEST PAGINATION AVEC DICTIONNAIRES")
    print("="*60)
    
    root = ctk.CTk()
    root.title("AllamBik - Test Pagination")
    root.geometry("1200x800")
    
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    title = ctk.CTkLabel(
        main_frame,
        text="HIGHLIGHTS EXTRAITS",
        font=("Arial", 18, "bold")
    )
    title.pack(pady=10)
    
    # Créer des highlights de test comme DICTIONNAIRES
    test_highlights = []
    
    for i in range(500):  # 500 highlights de test
        h = {
            'page': i // 3 + 1,
            'extracted_text': f"Texte extrait #{i+1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                            f"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                            f"Ut enim ad minim veniam, quis nostrud exercitation.",
            'confidence': 85 + (i % 15),
            'custom_name': f'Highlight {i+1}'
        }
        test_highlights.append(h)
    
    # Créer le display paginé
    display = PaginatedCardDisplay(main_frame, items_per_page=50)
    
    # Callback pour les clics
    def on_highlight_click(highlight):
        if isinstance(highlight, dict):
            print(f"Clic sur {highlight.get('custom_name', 'Highlight')}")
        else:
            print(f"Clic sur highlight page {getattr(highlight, 'page_number', '?')}")
    
    # Charger
    display.load_highlights(test_highlights, on_highlight_click)
    
    # Bouton export
    export_frame = ctk.CTkFrame(root, fg_color="transparent")
    export_frame.pack(pady=10)
    
    export_btn = ctk.CTkButton(
        export_frame,
        text=f"EXPORTER WORD ({len(test_highlights)} highlights)",
        width=200,
        height=40,
        fg_color="#4CAF50",
        hover_color="#45a049",
        command=lambda: print(f"Export de {len(display.get_all_highlights())} highlights")
    )
    export_btn.pack()
    
    root.mainloop()
