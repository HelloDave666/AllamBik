"""
main_paginated.py - Version d'AllamBik avec pagination
Point d'entrée de test qui utilise la pagination sans modifier main.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("ALLAMBIK - VERSION PAGINÉE (TEST)")
print("="*60)

# Importer le module de pagination
from pagination_system import PaginatedHighlightDisplay

# Monkey-patch pour intercepter l'affichage des highlights
import src.presentation.gui.views.main_window as main_window

# Sauvegarder la méthode originale
original_init = main_window.MainWindow.__init__
original_on_highlights_changed = getattr(main_window.MainWindow, '_on_highlights_changed', None)

def patched_init(self, *args, **kwargs):
    """Init modifié pour ajouter la pagination."""
    # Appeler l'init original
    original_init(self, *args, **kwargs)
    
    # Ajouter le système de pagination
    print("✓ Ajout du système de pagination...")
    self.paginated_display = None
    self.pagination_enabled = True

def patched_on_highlights_changed(self, highlights):
    """Version avec pagination."""
    print(f"\n📊 Réception de {len(highlights)} highlights")
    
    # Stocker tous les highlights pour l'export
    self.all_highlights = list(highlights) if highlights else []
    
    # Si pagination activée et beaucoup d'éléments
    if len(highlights) > 200:
        print(f"⚡ Activation de la pagination ({len(highlights)} > 200)")
        
        # Créer le système paginé si pas encore fait
        if not hasattr(self, 'paginated_display'):
            from pagination_system import PaginatedHighlightDisplay
            
            # Trouver le conteneur approprié
            container = getattr(self, 'highlight_list_scroll', None) or \
                       getattr(self, 'highlight_list', None) or \
                       getattr(self, 'highlight_frame', None)
            
            if container:
                # Nettoyer le conteneur
                for widget in container.winfo_children():
                    widget.destroy()
                
                # Créer le display paginé
                self.paginated_display = PaginatedHighlightDisplay(
                    container,
                    items_per_page=100
                )
                
                # Fonction pour créer les widgets
                from src.presentation.gui.components.highlight_card import HighlightCard
                
                def create_card(parent, highlight, index):
                    card = HighlightCard(
                        parent,
                        highlight,
                        on_click=lambda h=highlight: self._on_highlight_selected(h)
                    )
                    return card
                
                # Charger avec pagination
                self.paginated_display.load_items(highlights, create_card)
                
                print(f"✓ Pagination activée: {self.paginated_display.total_pages} pages")
            else:
                print("⚠ Conteneur non trouvé, utilisation méthode standard")
                if original_on_highlights_changed:
                    original_on_highlights_changed(self, highlights[:200])
    else:
        # Peu d'éléments, utiliser la méthode normale
        print(f"📝 Affichage standard ({len(highlights)} éléments)")
        if original_on_highlights_changed:
            original_on_highlights_changed(self, highlights)

# Appliquer les patchs
main_window.MainWindow.__init__ = patched_init
if original_on_highlights_changed:
    main_window.MainWindow._on_highlights_changed = patched_on_highlights_changed

print("\n✅ Patches appliqués:")
print("  • Pagination automatique pour >200 éléments")
print("  • 100 éléments par page")
print("  • Export complet préservé")
print("\n" + "="*60)

# Lancer l'application
from src.presentation.gui.app import main
main()
