"""
Composant Highlight Card - Version avec support pagination et selection multiple
"""
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
import tkinter as tk
from tkinter import messagebox


class HighlightCard(ctk.CTkFrame):
    """
    Carte pour afficher un highlight extrait - Version avec support multi-selection.
    """
    
    def __init__(
        self,
        parent,
        highlight_data: Dict[str, Any],
        on_click: Optional[Callable] = None,
        on_update: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_edit_requested: Optional[Callable] = None,
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
        self.highlight_data = highlight_data.copy()
        self.on_click = on_click
        self.on_update = on_update
        self.on_delete = on_delete
        self.on_edit_requested = on_edit_requested
        
        # Variables d'état
        self.is_hovered = False
        self.is_selected = False
        self.search_highlighted = False
        
        # CORRECTION BUG MODIF: Variable pour gérer l'indicateur
        self.modified_indicator = None
        
        # Créer le contenu
        self._create_content()
        self._bind_events()
    
    def _update_modification_indicator(self):
        """CORRECTION BUG MODIF: Gère l'indicateur de modification de manière sûre."""
        # Vérifier si ce highlight spécifique a été modifié
        is_modified = self.highlight_data.get('modified', False)
        
        if is_modified and self.modified_indicator is None:
            # Créer l'indicateur seulement s'il n'existe pas et qu'on en a besoin
            self.modified_indicator = ctk.CTkLabel(
                self.header_frame,
                text="MODIF",
                font=ctk.CTkFont(size=8, weight="bold"),
                text_color="#00aaff"
            )
            self.modified_indicator.pack(side="right", padx=(0, 5))
            print(f"DEBUG: Indicateur MODIF créé pour Page {self.highlight_data.get('page')}")
            
        elif not is_modified and self.modified_indicator is not None:
            # Supprimer l'indicateur s'il existe mais qu'on n'en a plus besoin
            self.modified_indicator.destroy()
            self.modified_indicator = None
            print(f"DEBUG: Indicateur MODIF supprimé pour Page {self.highlight_data.get('page')}")
    
    def _create_content(self):
        """Crée le contenu de la carte."""
        # Header avec numéro de page OU nom personnalisé
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        # CORRECTION: Affichage du nom personnalisé en titre
        display_name = self.highlight_data.get('custom_name')
        if display_name:
            # Si nom personnalisé, l'afficher en titre
            title_text = display_name
            subtitle_text = f"Page {self.highlight_data.get('page', '?')}"
        else:
            # Sinon, afficher "Page X"
            title_text = f"Page {self.highlight_data.get('page', '?')}"
            subtitle_text = None
        
        # Titre principal
        self.page_label = ctk.CTkLabel(
            self.header_frame,
            text=title_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ffffff"  # Plus visible si c'est un nom personnalisé
        )
        self.page_label.pack(side="left", anchor="w")
        
        # Sous-titre si nom personnalisé (affiche la page)
        if subtitle_text:
            self.page_subtitle = ctk.CTkLabel(
                self.header_frame,
                text=subtitle_text,
                font=ctk.CTkFont(size=9),
                text_color="#b0b0b0"
            )
            self.page_subtitle.pack(side="left", anchor="w", padx=(5, 0))
        else:
            self.page_subtitle = None
        
        # Confidence indicator
        confidence = self.highlight_data.get('confidence', 0)
        self.confidence_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=self._get_confidence_color(),
            width=8,
            height=8,
            corner_radius=4
        )
        self.confidence_frame.pack(side="right", padx=(5, 0))
        self.confidence_frame.pack_propagate(False)
        
        # CORRECTION BUG MODIF: Créer l'indicateur de manière contrôlée
        self._update_modification_indicator()
        
        # Texte du highlight
        text_content = self._truncate_text(self.highlight_data.get('text', ''), 150)
        self.text_label = ctk.CTkLabel(
            self,
            text=text_content,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            justify="left",
            anchor="nw",
            wraplength=250
        )
        self.text_label.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Footer avec confidence
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=20)
        self.footer_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.footer_frame.pack_propagate(False)
        
        self.confidence_label = ctk.CTkLabel(
            self.footer_frame,
            text=f"{confidence:.0f}% confiance",
            font=ctk.CTkFont(size=9),
            text_color="#808080"
        )
        self.confidence_label.pack(side="left")
    
    def _bind_events(self):
        """Lie les événements aux widgets."""
        # Double-clic pour édition intégrée
        self.bind("<Double-Button-1>", self._on_double_click)
        
        # Clic simple pour sélection (avec support Shift)
        self.bind("<Button-1>", self._on_card_clicked)
        
        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Bind events pour tous les enfants
        for child in self.winfo_children():
            child.bind("<Double-Button-1>", self._on_double_click)
            child.bind("<Button-1>", self._on_card_clicked)
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)
            
            # Bind récursif pour les sous-enfants
            for subchild in child.winfo_children():
                subchild.bind("<Double-Button-1>", self._on_double_click)
                subchild.bind("<Button-1>", self._on_card_clicked)
                subchild.bind("<Enter>", self._on_enter)
                subchild.bind("<Leave>", self._on_leave)
    
    def _on_card_clicked(self, event):
        """Gère le clic sur la carte avec support Shift pour multi-selection."""
        # Vérifier si Shift est enfoncé
        shift_pressed = event.state & 0x0001  # Shift key mask
        
        if self.on_click:
            self.on_click(self.highlight_data, shift_pressed)
    
    def _on_double_click(self, event):
        """Gère le double-clic pour ouvrir l'édition intégrée."""
        if self.on_edit_requested:
            self.on_edit_requested(self.highlight_data)
    
    def _on_enter(self, event):
        """Gère l'entrée de la souris."""
        if not self.is_hovered:
            self.is_hovered = True
            self.update_visual_state()
    
    def _on_leave(self, event):
        """Gère la sortie de la souris."""
        # Vérifier si on est vraiment sorti de la carte
        x, y = event.x_root, event.y_root
        widget_x = self.winfo_rootx()
        widget_y = self.winfo_rooty()
        widget_width = self.winfo_width()
        widget_height = self.winfo_height()
        
        if not (widget_x <= x <= widget_x + widget_width and 
                widget_y <= y <= widget_y + widget_height):
            self.is_hovered = False
            self.update_visual_state()
    
    def set_selected(self, selected: bool):
        """Définit l'état de sélection de la carte."""
        self.is_selected = selected
        self.update_visual_state()
    
    def update_hover(self, hovering: bool):
        """Met à jour l'apparence au survol."""
        self.is_hovered = hovering
        self.update_visual_state()
    
    def update_visual_state(self):
        """Met à jour l'apparence selon l'état (sélectionné, survolé, normal)."""
        if self.is_selected:
            # Fiche sélectionnée - surbrillance persistante
            self.configure(fg_color="#4a5a4a", border_color="#00ff88", border_width=2)
        elif self.search_highlighted:
            # Résultat de recherche - surbrillance jaune
            self.configure(fg_color="#5a5a3a", border_color="#ffaa00", border_width=2)
        elif self.is_hovered:
            # Survol temporaire
            self.configure(fg_color="#454545", border_color="#00aaff", border_width=1)
        else:
            # État normal
            self.configure(fg_color="#3a3a3a", border_color="#505050", border_width=1)
    
    def _add_search_highlight(self, search_text):
        """Ajoute le surlignage de recherche."""
        self.search_highlighted = True
        self.update_visual_state()
    
    def _remove_search_highlight(self):
        """Supprime le surlignage de recherche."""
        self.search_highlighted = False
        self.update_visual_state()
    
    def _refresh_display(self):
        """Actualise l'affichage de la carte."""
        # CORRECTION: Mettre à jour le titre selon le nom personnalisé
        display_name = self.highlight_data.get('custom_name')
        if display_name:
            # Nom personnalisé en titre
            self.page_label.configure(text=display_name, text_color="#ffffff")
            
            # Ajouter sous-titre avec page si pas déjà présent
            if not self.page_subtitle:
                self.page_subtitle = ctk.CTkLabel(
                    self.header_frame,
                    text=f"Page {self.highlight_data.get('page', '?')}",
                    font=ctk.CTkFont(size=9),
                    text_color="#b0b0b0"
                )
                self.page_subtitle.pack(side="left", anchor="w", padx=(5, 0), after=self.page_label)
            else:
                self.page_subtitle.configure(text=f"Page {self.highlight_data.get('page', '?')}")
        else:
            # Pas de nom personnalisé, afficher juste la page
            self.page_label.configure(text=f"Page {self.highlight_data.get('page', '?')}", text_color="#b0b0b0")
            
            # Supprimer le sous-titre si présent
            if self.page_subtitle:
                self.page_subtitle.destroy()
                self.page_subtitle = None
        
        # Mettre à jour le texte
        text_content = self._truncate_text(self.highlight_data.get('text', ''), 150)
        self.text_label.configure(text=text_content)
        
        # CORRECTION BUG MODIF: Utiliser la méthode contrôlée
        self._update_modification_indicator()
    
    def _get_confidence_color(self) -> str:
        """Retourne la couleur selon le niveau de confiance."""
        confidence = self.highlight_data.get('confidence', 0)
        if confidence >= 90:
            return "#00ff88"  # Vert
        elif confidence >= 75:
            return "#ffaa00"  # Jaune
        else:
            return "#ff4444"  # Rouge
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Tronque le texte si nécessaire."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def update_data(self, new_data: Dict[str, Any]):
        """Met à jour les données du highlight."""
        self.highlight_data = new_data.copy()
        self._refresh_display()


class HighlightGrid(ctk.CTkScrollableFrame):
    """
    Grille scrollable pour afficher les highlights - Version avec pagination et multi-selection.
    """
    
    def __init__(self, parent, columns: int = 2, on_edit_requested: Optional[Callable] = None, 
                 on_highlight_selected: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns
        self.cards = []
        self.highlights_data = []
        self.on_edit_requested = on_edit_requested
        self.on_highlight_selected = on_highlight_selected
        self.configure(fg_color="transparent")
        
        # NOUVEAU : Liste des cartes selectionnees (multi-selection)
        self.selected_cards = []
        
        # NOUVEAU : Limiter la hauteur pour eviter le scroll avec pagination
        self.configure(height=600)  # Hauteur fixe pour ~50 elements
        
        # Configuration de la grille
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1, uniform="column")
    
    def add_highlight(self, highlight_data: Dict[str, Any]):
        """Ajoute un highlight à la grille."""
        # Stocker les données
        self.highlights_data.append(highlight_data)
        
        # Créer la carte
        card = HighlightCard(
            self,
            highlight_data=highlight_data,
            on_click=self.on_highlight_selected,
            on_update=self._on_highlight_updated,
            on_delete=self._on_highlight_deleted,
            on_edit_requested=self.on_edit_requested
        )
        
        # Calculer la position dans la grille
        row = len(self.cards) // self.columns
        col = len(self.cards) % self.columns
        
        card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        self.cards.append(card)
        
        # Effet d'apparition
        card.configure(fg_color="#2a2a2a")
        self.after(50, lambda: card.configure(fg_color="#3a3a3a"))
    
    def set_paginated_data(self, highlights_data: List[Dict[str, Any]]):
        """
        Remplace toutes les donnees affichees par une nouvelle page.
        Utilise pour la pagination.
        
        Args:
            highlights_data: Liste des highlights a afficher pour cette page
        """
        # Supprimer toutes les cartes existantes
        for card in self.cards:
            card.destroy()
        
        self.cards.clear()
        self.highlights_data.clear()
        self.selected_cards.clear()  # Vider aussi les selections
        
        # Ajouter les nouvelles donnees
        for highlight_data in highlights_data:
            self.add_highlight(highlight_data)
        
        # Forcer la mise a jour de l'affichage
        self.update_idletasks()
        
        print(f"INFO: Affichage de {len(highlights_data)} highlights (page paginee)")
    
    def clear_all_selections(self):
        """Deselectionne toutes les cartes."""
        for card in self.selected_cards:
            try:
                card.set_selected(False)
            except:
                pass
        self.selected_cards.clear()
    
    def get_selected_cards(self) -> List:
        """Retourne la liste des cartes selectionnees."""
        return self.selected_cards.copy()
    
    def delete_selected_cards(self):
        """Supprime toutes les cartes selectionnees."""
        if not self.selected_cards:
            return 0
        
        # Copier la liste pour eviter les modifications pendant l'iteration
        cards_to_delete = self.selected_cards.copy()
        data_to_delete = [card.highlight_data for card in cards_to_delete]
        count = len(cards_to_delete)
        
        # Supprimer les cartes de l'affichage
        for card in cards_to_delete:
            try:
                card.destroy()
                self.cards.remove(card)
            except:
                pass
        
        # Supprimer les donnees correspondantes
        for data in data_to_delete:
            for stored_data in self.highlights_data[:]:  # Copie pour iteration
                if (stored_data.get('page') == data.get('page') and
                    stored_data.get('text', '')[:50] == data.get('text', '')[:50]):
                    self.highlights_data.remove(stored_data)
                    break
        
        # Vider la selection
        self.selected_cards.clear()
        
        # Reorganiser la grille
        self._reorganize_grid()
        
        return count
    
    def update_highlight(self, updated_data: Dict[str, Any]):
        """Met à jour un highlight existant - CORRECTION BUG ÉDITION."""
        # CORRECTION: Utiliser un identifiant plus robuste pour trouver le highlight
        target_index = None
        
        print(f"DEBUG: Recherche highlight à mettre à jour: Page {updated_data.get('page')}, Nom: {updated_data.get('custom_name', 'Sans nom')}")
        
        # Essayer de correspondre par plusieurs critères
        for i, data in enumerate(self.highlights_data):
            # Critère 1: Même page ET début du texte identique (30 caractères)
            if (data.get('page') == updated_data.get('page') and 
                data.get('text', '')[:30] == updated_data.get('text', '')[:30]):
                target_index = i
                print(f"SUCCESS: Trouvé par critère 1 (page + texte) à l'index {i}")
                break
            
            # Critère 2: Si pas de match exact, chercher par texte complet identique
            if target_index is None and data.get('text', '') == updated_data.get('text', ''):
                target_index = i
                print(f"SUCCESS: Trouvé par critère 2 (texte complet) à l'index {i}")
                break
        
        # Critère 3: Correspondance par timestamp si disponible
        if target_index is None:
            for i, data in enumerate(self.highlights_data):
                if (data.get('timestamp') and updated_data.get('timestamp') and
                    data.get('timestamp') == updated_data.get('timestamp')):
                    target_index = i
                    print(f"SUCCESS: Trouvé par critère 3 (timestamp) à l'index {i}")
                    break
        
        # Si toujours pas trouvé, utiliser un fallback avec la page uniquement
        if target_index is None:
            for i, data in enumerate(self.highlights_data):
                if data.get('page') == updated_data.get('page'):
                    target_index = i
                    print(f"WARNING: Fallback par page uniquement à l'index {i}")
                    break
        
        if target_index is not None:
            # Mettre à jour les données
            old_data = self.highlights_data[target_index].copy()
            self.highlights_data[target_index] = updated_data.copy()
            
            # Mettre à jour la carte correspondante
            if target_index < len(self.cards):
                self.cards[target_index].update_data(updated_data)
                print(f"SUCCESS: Highlight {target_index} mis à jour: '{old_data.get('custom_name', 'Sans nom')}' → '{updated_data.get('custom_name', 'Sans nom')}'")
            else:
                print(f"ERREUR: Index {target_index} hors limite pour les cartes ({len(self.cards)} cartes)")
        else:
            print(f"ERREUR: Highlight non trouvé pour mise à jour: Page {updated_data.get('page')}")
            print(f"INFO: Highlights disponibles:")
            for i, data in enumerate(self.highlights_data):
                print(f"  {i}: Page {data.get('page')}, Texte: '{data.get('text', '')[:30]}...'")
    
    def _on_highlight_updated(self, updated_data):
        """Callback quand un highlight est mis à jour."""
        self.update_highlight(updated_data)
    
    def _on_highlight_deleted(self, deleted_data):
        """Callback quand un highlight est supprimé."""
        # Trouver la carte correspondante
        card_to_remove = None
        data_to_remove = None
        
        for i, (card, data) in enumerate(zip(self.cards, self.highlights_data)):
            if (data.get('page') == deleted_data.get('page') and 
                data.get('text', '')[:50] == deleted_data.get('text', '')[:50]):
                card_to_remove = card
                data_to_remove = data
                break
        
        if card_to_remove:
            # Retirer de la liste des selections si presente
            if card_to_remove in self.selected_cards:
                self.selected_cards.remove(card_to_remove)
            
            # Supprimer la carte et les données
            card_to_remove.destroy()
            self.cards.remove(card_to_remove)
            self.highlights_data.remove(data_to_remove)
            
            # Réorganiser la grille
            self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Réorganise la grille après suppression."""
        for i, card in enumerate(self.cards):
            row = i // self.columns
            col = i % self.columns
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
    
    def clear(self):
        """Supprime tous les highlights."""
        for card in self.cards:
            card.destroy()
        self.cards.clear()
        self.highlights_data.clear()
        self.selected_cards.clear()
    
    def get_count(self) -> int:
        """Retourne le nombre de highlights."""
        return len(self.cards)
    
    def get_highlights_data(self) -> List[Dict[str, Any]]:
        """Retourne toutes les données des highlights."""
        return self.highlights_data.copy()