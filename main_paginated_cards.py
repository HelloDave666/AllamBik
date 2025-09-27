"""
main_paginated_cards.py - AllamBik avec pagination ET apparence originale
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("ALLAMBIK - PAGINATION AVEC APPARENCE ORIGINALE")
print("="*60)

# Importer la pagination avec cards
from pagination_with_cards import PaginatedCardDisplay

# Patcher main_window
import src.presentation.gui.views.main_window as main_window

original_on_highlights_changed = getattr(main_window.MainWindow, '_on_highlights_changed', None)

def patched_on_highlights_changed(self, highlights):
    """Utilise la pagination avec les vrais HighlightCard."""
    
    # Stocker pour l'export
    self.all_highlights = list(highlights) if highlights else []
    
    print(f"\n📊 {len(highlights)} highlights reçus")
    
    # Si plus de 100 highlights, utiliser pagination
    if len(highlights) > 100:
        print(f"⚡ Activation pagination (>100 éléments)")
        
        # Trouver le conteneur
        container = None
        for attr in ['highlight_list_scroll', 'highlight_scroll', 'highlight_list']:
            container = getattr(self, attr, None)
            if container:
                break
        
        if container:
            # Nettoyer
            for widget in container.winfo_children():
                widget.destroy()
            
            # Créer le display paginé avec vrais cards
            self.paginated = PaginatedCardDisplay(container, items_per_page=100)
            self.paginated.load_highlights(
                highlights,
                on_click_callback=lambda h: self._on_highlight_selected(h) if hasattr(self, '_on_highlight_selected') else None
            )
            
            # Mettre à jour le titre si existe
            if hasattr(self, 'highlight_list_title'):
                self.highlight_list_title.configure(
                    text=f"HIGHLIGHTS EXTRAITS ({len(highlights)})"
                )
        else:
            print("⚠ Conteneur non trouvé")
    else:
        # Peu d'éléments, méthode normale
        if original_on_highlights_changed:
            original_on_highlights_changed(self, highlights)

# Appliquer le patch
if original_on_highlights_changed:
    main_window.MainWindow._on_highlights_changed = patched_on_highlights_changed

print("✅ Pagination activée avec apparence originale")
print("  • Seuil: >100 highlights")
print("  • Utilise les vrais HighlightCard")
print("  • Export complet préservé")

# Lancer
from src.presentation.gui.app import main
main()
