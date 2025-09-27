"""
main_with_pagination.py - AllamBik avec pagination intégrée
Utilise des dictionnaires pour compatibilité avec HighlightCard
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("ALLAMBIK AVEC PAGINATION")
print("="*60)

from pagination_with_dict import PaginatedCardDisplay
import src.presentation.gui.views.main_window as main_window

# Sauvegarder la méthode originale
original_on_highlights_changed = getattr(main_window.MainWindow, '_on_highlights_changed', None)

def patched_on_highlights_changed(self, highlights):
    """Version avec pagination pour grandes listes."""
    
    # Stocker TOUS les highlights (objets) pour l'export
    self.all_highlights = list(highlights) if highlights else []
    
    print(f"\n📊 {len(highlights)} highlights reçus")
    
    # Seuil de pagination
    PAGINATION_THRESHOLD = 100
    
    if len(highlights) > PAGINATION_THRESHOLD:
        print(f"⚡ Pagination activée ({len(highlights)} > {PAGINATION_THRESHOLD})")
        
        # Trouver le conteneur
        container = None
        for attr in ['highlight_list_scroll', 'highlight_scroll', 'highlight_list']:
            if hasattr(self, attr):
                container = getattr(self, attr)
                if container:
                    break
        
        if container:
            # Nettoyer
            for widget in container.winfo_children():
                widget.destroy()
            
            # Convertir les objets Highlight en dictionnaires
            highlight_dicts = []
            for i, h in enumerate(highlights):
                # Conversion objet -> dictionnaire
                h_dict = {
                    'page': getattr(h, 'page_number', getattr(h, 'page', 0)),
                    'extracted_text': getattr(h, 'text', getattr(h, 'extracted_text', '')),
                    'confidence': getattr(h, 'confidence', 0),
                    'custom_name': getattr(h, 'custom_name', f'Highlight {i+1}'),
                    # Garder une référence à l'objet original pour l'export
                    '_original': h
                }
                highlight_dicts.append(h_dict)
            
            # Créer le display paginé
            if not hasattr(self, 'paginated_display'):
                self.paginated_display = PaginatedCardDisplay(container, items_per_page=100)
            
            # Callback pour la sélection
            def on_click(h_dict):
                # Utiliser l'objet original si disponible
                original = h_dict.get('_original', h_dict)
                if hasattr(self, '_on_highlight_selected'):
                    self._on_highlight_selected(original)
            
            # Charger avec pagination
            self.paginated_display.load_highlights(highlight_dicts, on_click)
            
            # Mettre à jour le titre
            if hasattr(self, 'highlight_list_title'):
                self.highlight_list_title.configure(
                    text=f"HIGHLIGHTS EXTRAITS ({len(highlights)})"
                )
            
            print(f"✓ {self.paginated_display.total_pages} pages créées")
            
        else:
            print("⚠ Conteneur non trouvé, utilisation standard")
            if original_on_highlights_changed:
                original_on_highlights_changed(self, highlights)
    else:
        # Peu d'éléments, utiliser la méthode normale
        print(f"📝 Affichage standard ({len(highlights)} highlights)")
        if original_on_highlights_changed:
            original_on_highlights_changed(self, highlights)

# Appliquer le patch
if original_on_highlights_changed:
    main_window.MainWindow._on_highlights_changed = patched_on_highlights_changed
    print("✓ Patch de pagination appliqué")

# Aussi patcher l'export pour utiliser all_highlights
original_export = getattr(main_window.MainWindow, '_on_export_word_clicked', None)

def patched_export(self):
    """Export qui utilise all_highlights."""
    # Utiliser les highlights complets stockés
    highlights_to_export = getattr(self, 'all_highlights', self.viewmodel.highlights)
    
    if highlights_to_export:
        print(f"Export de {len(highlights_to_export)} highlights (complet)")
        
        # Appeler l'export original avec tous les highlights
        self.viewmodel.highlights = highlights_to_export
        if original_export:
            original_export(self)
    else:
        print("Aucun highlight à exporter")

if original_export:
    main_window.MainWindow._on_export_word_clicked = patched_export
    print("✓ Export patché pour utiliser tous les highlights")

print("\n" + "="*60)
print("Configuration:")
print(f"  • Seuil de pagination: {100} highlights")
print(f"  • Éléments par page: 100")
print("  • Export complet préservé (tous les highlights)")
print("="*60 + "\n")

# Lancer l'application
from src.presentation.gui.app import main
main()
