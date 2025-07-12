"""
Composant Highlight Card - Carte pour afficher un highlight
"""
import customtkinter as ctk
from typing import Optional, Callable


class HighlightCard(ctk.CTkFrame):
    """
    Carte pour afficher un highlight extrait.
    Design inspiré du style Alambik original.
    """
    
    def __init__(
        self,
        parent,
        page: int,
        text: str,
        confidence: float,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.configure(
            fg_color="#3a3a3a",
            border_width=1,
            border_color="#505050",
            height=120
        )
        
        # Données
        self.page = page
        self.text = text
        self.confidence = confidence
        self.on_click = on_click
        
        # Créer le contenu
        self._create_content()
        
        # Bind click event
        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click())
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: self.on_click())
    
    def _create_content(self):
        """Crée le contenu de la carte."""
        # Header avec numéro de page
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        # Page number
        page_label = ctk.CTkLabel(
            header_frame,
            text=f"Page {self.page}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#b0b0b0"
        )
        page_label.pack(side="left")
        
        # Confidence indicator
        confidence_frame = ctk.CTkFrame(
            header_frame,
            fg_color=self._get_confidence_color(),
            width=8,
            height=8,
            corner_radius=4
        )
        confidence_frame.pack(side="right", padx=(5, 0))
        confidence_frame.pack_propagate(False)
        
        # Trois points (menu)
        dots_label = ctk.CTkLabel(
            header_frame,
            text="⋯",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#606060"
        )
        dots_label.pack(side="right", padx=(0, 10))
        
        # Texte du highlight
        text_content = self._truncate_text(self.text, 150)
        text_label = ctk.CTkLabel(
            self,
            text=text_content,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            justify="left",
            anchor="nw",
            wraplength=250
        )
        text_label.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Footer avec confidence
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=20)
        footer_frame.pack(fill="x", padx=15, pady=(0, 10))
        footer_frame.pack_propagate(False)
        
        confidence_label = ctk.CTkLabel(
            footer_frame,
            text=f"{self.confidence:.0f}% confiance",
            font=ctk.CTkFont(size=9),
            text_color="#808080"
        )
        confidence_label.pack(side="left")
    
    def _get_confidence_color(self) -> str:
        """Retourne la couleur selon le niveau de confiance."""
        if self.confidence >= 90:
            return "#00ff88"  # Vert
        elif self.confidence >= 75:
            return "#ffaa00"  # Jaune
        else:
            return "#ff4444"  # Rouge
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Tronque le texte si nécessaire."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def update_hover(self, hovering: bool):
        """Met à jour l'apparence au survol."""
        if hovering:
            self.configure(fg_color="#454545", border_color="#00aaff")
        else:
            self.configure(fg_color="#3a3a3a", border_color="#505050")


class HighlightGrid(ctk.CTkScrollableFrame):
    """
    Grille scrollable pour afficher les highlights.
    """
    
    def __init__(self, parent, columns: int = 2, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns
        self.cards = []
        self.configure(fg_color="transparent")
        
        # Configuration de la grille
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1, uniform="column")
    
    def add_highlight(self, page: int, text: str, confidence: float):
        """Ajoute un highlight à la grille."""
        card = HighlightCard(
            self,
            page=page,
            text=text,
            confidence=confidence
        )
        
        # Calculer la position dans la grille
        row = len(self.cards) // self.columns
        col = len(self.cards) % self.columns
        
        card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        self.cards.append(card)
        
        # Effet d'apparition
        card.configure(fg_color="#2a2a2a")
        self.after(50, lambda: card.configure(fg_color="#3a3a3a"))
    
    def clear(self):
        """Supprime tous les highlights."""
        for card in self.cards:
            card.destroy()
        self.cards.clear()
    
    def get_count(self) -> int:
        """Retourne le nombre de highlights."""
        return len(self.cards)