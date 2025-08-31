"""
Composant de liste virtuelle pour afficher efficacement de grandes listes
"""
import customtkinter as ctk
import tkinter as tk

class VirtualScrollFrame(ctk.CTkScrollableFrame):
    """Frame scrollable avec virtualisation pour performances."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configuration virtualisation
        self.visible_items = 50  # Nombre d'éléments visibles
        self.item_height = 120  # Hauteur estimée par élément
        self.total_items = 0
        self.items_data = []
        self.rendered_widgets = {}
        self.current_top_index = 0
        
        # Bind scroll events
        self._parent_canvas.bind("<MouseWheel>", self._on_scroll)
        
    def set_items(self, items):
        """Définit les éléments à afficher."""
        self.items_data = items
        self.total_items = len(items)
        
        # Nettoyer l'affichage actuel
        for widget in self.rendered_widgets.values():
            widget.destroy()
        self.rendered_widgets.clear()
        
        # Afficher les premiers éléments
        self._render_visible_items()
        
        print(f"VirtualScrollFrame: {self.total_items} éléments, {self.visible_items} visibles")
        
    def _render_visible_items(self):
        """Rend seulement les éléments visibles."""
        if not self.items_data:
            return
            
        # Calculer les indices visibles
        start_idx = self.current_top_index
        end_idx = min(start_idx + self.visible_items, self.total_items)
        
        # Supprimer les widgets hors vue
        for idx in list(self.rendered_widgets.keys()):
            if idx < start_idx or idx >= end_idx:
                self.rendered_widgets[idx].destroy()
                del self.rendered_widgets[idx]
        
        # Créer les widgets visibles
        for idx in range(start_idx, end_idx):
            if idx not in self.rendered_widgets:
                item = self.items_data[idx]
                widget = self._create_item_widget(item, idx)
                widget.pack(fill="x", padx=5, pady=2)
                self.rendered_widgets[idx] = widget
                
    def _create_item_widget(self, item, index):
        """Crée un widget pour un élément."""
        frame = ctk.CTkFrame(self, height=100)
        
        # Numéro et texte
        text = item.extracted_text if hasattr(item, 'extracted_text') else str(item)
        display_text = f"#{index + 1}: {text[:100]}..." if len(text) > 100 else f"#{index + 1}: {text}"
        
        label = ctk.CTkLabel(
            frame,
            text=display_text,
            anchor="w",
            justify="left"
        )
        label.pack(fill="both", expand=True, padx=10, pady=5)
        
        return frame
        
    def _on_scroll(self, event):
        """Gère le scroll pour la virtualisation."""
        # Calculer le nouveau top index basé sur le scroll
        scroll_units = -1 * (event.delta / 120)
        new_top = max(0, min(self.current_top_index + int(scroll_units * 3), 
                             self.total_items - self.visible_items))
        
        if new_top != self.current_top_index:
            self.current_top_index = new_top
            self._render_visible_items()
