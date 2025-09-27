"""
main_pagination_fixed.py - Version corrigée avec pagination stricte
LIMITE ABSOLUE de 100 éléments affichés
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("ALLAMBIK - PAGINATION STRICTE (100 MAX)")
print("="*60)

import src.presentation.gui.views.main_window as main_window

# Intercepter TOUTE création de widgets
original_on_highlights_changed = getattr(main_window.MainWindow, '_on_highlights_changed', None)

# Variable globale pour stocker les highlights complets
ALL_HIGHLIGHTS = []

def strict_paginated_display(self, highlights):
    """Affichage strictement limité à 100 éléments."""
    global ALL_HIGHLIGHTS
    
    # Stocker TOUS pour l'export
    ALL_HIGHLIGHTS = list(highlights) if highlights else []
    self.all_highlights = ALL_HIGHLIGHTS
    
    print(f"\n⚡ PAGINATION STRICTE: {len(highlights)} highlights")
    print(f"   Affichage limité à 100 éléments MAX")
    
    # LIMITE ABSOLUE
    MAX_DISPLAY = 100
    
    # Trouver le conteneur
    container = None
    for attr in ['highlight_list_scroll', 'highlight_scroll', 'highlight_list']:
        if hasattr(self, attr):
            container = getattr(self, attr)
            if container:
                break
    
    if not container:
        print("✗ Pas de conteneur trouvé")
        return
    
    # NETTOYER COMPLÈTEMENT
    for widget in container.winfo_children():
        widget.destroy()
    
    # Afficher SEULEMENT les premiers 100
    display_items = highlights[:MAX_DISPLAY]
    
    # Créer les widgets (100 maximum)
    from src.presentation.gui.components.highlight_card import HighlightCard
    
    for i, h in enumerate(display_items):
        try:
            # Convertir en dict
            h_dict = {
                'page': getattr(h, 'page_number', getattr(h, 'page', 0)),
                'extracted_text': getattr(h, 'text', getattr(h, 'extracted_text', '')),
                'confidence': getattr(h, 'confidence', 0),
                'custom_name': f'Highlight {i+1}'
            }
            
            card = HighlightCard(
                container,
                h_dict,
                on_click=lambda h=h: self._on_highlight_selected(h) if hasattr(self, '_on_highlight_selected') else None
            )
            card.pack(fill="x", padx=10, pady=5)
            
        except Exception as e:
            print(f"Erreur carte {i}: {e}")
            break
    
    # Message d'avertissement
    if len(highlights) > MAX_DISPLAY:
        import customtkinter as ctk
        warning = ctk.CTkFrame(container, fg_color="orange", height=60)
        warning.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkLabel(
            warning,
            text=f"⚠️ AFFICHAGE LIMITÉ: {MAX_DISPLAY}/{len(highlights)} highlights\n"
                 f"Utilisez l'export Word pour obtenir tous les highlights",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(pady=10)
    
    # Mettre à jour le titre
    if hasattr(self, 'highlight_list_title'):
        self.highlight_list_title.configure(
            text=f"HIGHLIGHTS EXTRAITS ({len(highlights)}) - Affichage: {len(display_items)}"
        )
    
    print(f"✓ {len(display_items)} widgets créés (sur {len(highlights)} total)")

# Remplacer TOUTES les méthodes qui créent des widgets
main_window.MainWindow._on_highlights_changed = strict_paginated_display

# Intercepter aussi les changements de mode d'affichage
original_toggle = getattr(main_window.MainWindow, '_toggle_display_mode', None)
if original_toggle:
    def safe_toggle(self):
        """Toggle sans recréer tous les widgets."""
        print("Toggle intercepté - utilisation de la vue paginée")
        # Réafficher avec la limite
        if hasattr(self, 'all_highlights'):
            strict_paginated_display(self, self.all_highlights[:100])
    
    main_window.MainWindow._toggle_display_mode = safe_toggle

# Patch pour l'export
original_export = getattr(main_window.MainWindow, '_on_export_word_clicked', None)
def export_all(self):
    """Export TOUS les highlights."""
    all_h = getattr(self, 'all_highlights', [])
    print(f"EXPORT: {len(all_h)} highlights (COMPLET)")
    
    if all_h and original_export:
        # Temporairement mettre tous les highlights
        old = self.viewmodel.highlights
        self.viewmodel.highlights = all_h
        original_export(self)
        self.viewmodel.highlights = old

if original_export:
    main_window.MainWindow._on_export_word_clicked = export_all

print("\n✅ PATCHES APPLIQUÉS:")
print("  • Limite stricte: 100 widgets MAX")
print("  • Export: TOUS les highlights")
print("  • Toggle mode: limité aussi")
print("="*60)

# Lancer
from src.presentation.gui.app import main
main()
