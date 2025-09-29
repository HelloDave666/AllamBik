"""
Controleur de pagination pour gerer l'affichage de grandes listes
"""
from typing import List, Callable, Optional, Any
import customtkinter as ctk


class PaginationController:
    """Gere la pagination pour afficher de grandes listes par pages."""
    
    def __init__(self, items_per_page: int = 50):
        """
        Initialise le controleur de pagination.
        
        Args:
            items_per_page: Nombre d'elements a afficher par page
        """
        self.items_per_page = items_per_page
        self.current_page = 1
        self.total_items = 0
        self.all_data = []
        self.on_page_changed: Optional[Callable[[List[Any], int], None]] = None
    
    @property
    def total_pages(self) -> int:
        """Calcule le nombre total de pages."""
        if self.total_items == 0:
            return 1
        return (self.total_items + self.items_per_page - 1) // self.items_per_page
    
    @property
    def has_next_page(self) -> bool:
        """Verifie s'il y a une page suivante."""
        return self.current_page < self.total_pages
    
    @property
    def has_previous_page(self) -> bool:
        """Verifie s'il y a une page precedente."""
        return self.current_page > 1
    
    @property
    def start_index(self) -> int:
        """Index de debut pour la page actuelle."""
        return (self.current_page - 1) * self.items_per_page
    
    @property
    def end_index(self) -> int:
        """Index de fin pour la page actuelle."""
        return min(self.start_index + self.items_per_page, self.total_items)
    
    def set_data(self, data: List[Any]) -> None:
        """
        Definit les donnees a paginer.
        
        Args:
            data: Liste complete des donnees
        """
        self.all_data = data
        self.total_items = len(data)
        self.current_page = 1
        self._notify_page_changed()
    
    def get_current_page_data(self) -> List[Any]:
        """Retourne les donnees de la page actuelle."""
        return self.all_data[self.start_index:self.end_index]
    
    def next_page(self) -> bool:
        """
        Passe a la page suivante.
        
        Returns:
            True si la page a change, False sinon
        """
        if self.has_next_page:
            self.current_page += 1
            self._notify_page_changed()
            return True
        return False
    
    def previous_page(self) -> bool:
        """
        Passe a la page precedente.
        
        Returns:
            True si la page a change, False sinon
        """
        if self.has_previous_page:
            self.current_page -= 1
            self._notify_page_changed()
            return True
        return False
    
    def first_page(self) -> bool:
        """
        Retourne a la premiere page.
        
        Returns:
            True si la page a change, False sinon
        """
        if self.current_page != 1:
            self.current_page = 1
            self._notify_page_changed()
            return True
        return False
    
    def last_page(self) -> bool:
        """
        Va a la derniere page.
        
        Returns:
            True si la page a change, False sinon
        """
        last_page = self.total_pages
        if self.current_page != last_page:
            self.current_page = last_page
            self._notify_page_changed()
            return True
        return False
    
    def go_to_page(self, page: int) -> bool:
        """
        Va a une page specifique.
        
        Args:
            page: Numero de la page (1-indexed)
            
        Returns:
            True si la page a change, False sinon
        """
        if 1 <= page <= self.total_pages and page != self.current_page:
            self.current_page = page
            self._notify_page_changed()
            return True
        return False
    
    def _notify_page_changed(self) -> None:
        """Notifie le callback qu'une page a change."""
        if self.on_page_changed:
            current_data = self.get_current_page_data()
            self.on_page_changed(current_data, self.current_page)
    
    def get_page_info(self) -> str:
        """Retourne une chaine d'information sur la page actuelle."""
        if self.total_items == 0:
            return "Aucun element"
        
        start = self.start_index + 1
        end = self.end_index
        return f"Elements {start}-{end} sur {self.total_items} | Page {self.current_page}/{self.total_pages}"


class PaginationBar(ctk.CTkFrame):
    """Widget de controles de pagination."""
    
    def __init__(self, parent, controller: PaginationController, **kwargs):
        """
        Initialise la barre de pagination.
        
        Args:
            parent: Widget parent
            controller: Controleur de pagination
        """
        super().__init__(parent, **kwargs)
        
        self.controller = controller
        self.configure(fg_color="transparent")
        
        self._create_widgets()
        self._update_buttons()
    
    def _create_widgets(self):
        """Cree les widgets de la barre de pagination."""
        # Container principal
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Bouton premiere page
        self.first_button = ctk.CTkButton(
            controls_frame,
            text="<<",
            width=40,
            height=30,
            command=self._on_first_clicked,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a"
        )
        self.first_button.pack(side="left", padx=2)
        
        # Bouton page precedente
        self.prev_button = ctk.CTkButton(
            controls_frame,
            text="<",
            width=40,
            height=30,
            command=self._on_previous_clicked,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a"
        )
        self.prev_button.pack(side="left", padx=2)
        
        # Label info page
        self.info_label = ctk.CTkLabel(
            controls_frame,
            text="Page 1/1",
            font=ctk.CTkFont(size=12),
            width=300
        )
        self.info_label.pack(side="left", padx=10, expand=True)
        
        # Bouton page suivante
        self.next_button = ctk.CTkButton(
            controls_frame,
            text=">",
            width=40,
            height=30,
            command=self._on_next_clicked,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a"
        )
        self.next_button.pack(side="right", padx=2)
        
        # Bouton derniere page
        self.last_button = ctk.CTkButton(
            controls_frame,
            text=">>",
            width=40,
            height=30,
            command=self._on_last_clicked,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a"
        )
        self.last_button.pack(side="right", padx=2)
    
    def _on_first_clicked(self):
        """Gere le clic sur premiere page."""
        if self.controller.first_page():
            self._update_buttons()
    
    def _on_previous_clicked(self):
        """Gere le clic sur page precedente."""
        if self.controller.previous_page():
            self._update_buttons()
    
    def _on_next_clicked(self):
        """Gere le clic sur page suivante."""
        if self.controller.next_page():
            self._update_buttons()
    
    def _on_last_clicked(self):
        """Gere le clic sur derniere page."""
        if self.controller.last_page():
            self._update_buttons()
    
    def _update_buttons(self):
        """Met a jour l'etat des boutons."""
        # Activer/desactiver les boutons selon la position
        self.first_button.configure(
            state="normal" if self.controller.has_previous_page else "disabled"
        )
        self.prev_button.configure(
            state="normal" if self.controller.has_previous_page else "disabled"
        )
        self.next_button.configure(
            state="normal" if self.controller.has_next_page else "disabled"
        )
        self.last_button.configure(
            state="normal" if self.controller.has_next_page else "disabled"
        )
        
        # Mettre a jour le label d'information
        self.info_label.configure(text=self.controller.get_page_info())
    
    def refresh(self):
        """Rafraichit l'affichage de la barre de pagination."""
        self._update_buttons()