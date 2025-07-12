"""
Composant Progress Circle - Affichage des 3 cercles de progression
"""
import customtkinter as ctk
from tkinter import Canvas
import math
from typing import Dict


class ProgressCircle(ctk.CTkFrame):
    """
    Widget personnalisé affichant 3 cercles de progression imbriqués.
    Inspiré de votre design original Alambik.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.configure(fg_color="transparent")
        
        # Valeurs de progression
        self.percentages = {
            'current': 0,    # Cercle intérieur (bleu)
            'phase1': 0,     # Cercle moyen (jaune)
            'phase2': 0      # Cercle extérieur (rouge)
        }
        
        # Canvas pour dessiner
        self.canvas = Canvas(
            self,
            width=250,
            height=250,
            bg="#2a2a2a",
            highlightthickness=0
        )
        self.canvas.pack(padx=20, pady=20)
        
        # Centre et rayons
        self.center_x = 125
        self.center_y = 125
        self.radius_outer = 100    # Rouge - Phase 2
        self.radius_middle = 75    # Jaune - Phase 1
        self.radius_inner = 50     # Bleu - Progression courante
        self.line_width = 8
        
        # Couleurs
        self.colors = {
            'background': '#404040',
            'current': '#00aaff',    # Bleu
            'phase1': '#ffaa00',     # Jaune
            'phase2': '#ff4444'      # Rouge
        }
        
        # Label central
        self.percentage_label = ctk.CTkLabel(
            self,
            text="0%",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        self.percentage_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Dessiner les cercles de fond
        self._draw_background_circles()
        
        # Arcs de progression
        self.progress_arcs = {}
    
    def _draw_background_circles(self):
        """Dessine les cercles de fond."""
        # Cercle extérieur (Phase 2)
        self._create_circle(self.radius_outer, self.colors['background'])
        
        # Cercle moyen (Phase 1)
        self._create_circle(self.radius_middle, self.colors['background'])
        
        # Cercle intérieur (Progression courante)
        self._create_circle(self.radius_inner, self.colors['background'])
    
    def _create_circle(self, radius: int, color: str):
        """Crée un cercle de fond."""
        x1 = self.center_x - radius
        y1 = self.center_y - radius
        x2 = self.center_x + radius
        y2 = self.center_y + radius
        
        self.canvas.create_oval(
            x1, y1, x2, y2,
            outline=color,
            width=self.line_width,
            fill=""
        )
    
    def _create_arc(self, radius: int, percentage: float, color: str, tag: str):
        """Crée un arc de progression."""
        if percentage <= 0:
            return
        
        x1 = self.center_x - radius
        y1 = self.center_y - radius
        x2 = self.center_x + radius
        y2 = self.center_y + radius
        
        # Calculer l'angle (commence en haut)
        start_angle = 90
        extent_angle = -(percentage * 360 / 100)
        
        # Supprimer l'ancien arc s'il existe
        self.canvas.delete(tag)
        
        # Créer le nouvel arc
        self.canvas.create_arc(
            x1, y1, x2, y2,
            start=start_angle,
            extent=extent_angle,
            outline=color,
            width=self.line_width,
            style='arc',
            tags=tag
        )
    
    def update_progress(self, current: float = None, phase1: float = None, phase2: float = None):
        """
        Met à jour les pourcentages de progression.
        
        Args:
            current: Progression courante (0-100)
            phase1: Progression phase 1 (0-100)
            phase2: Progression phase 2 (0-100)
        """
        # Mettre à jour les valeurs
        if current is not None:
            self.percentages['current'] = max(0, min(100, current))
        if phase1 is not None:
            self.percentages['phase1'] = max(0, min(100, phase1))
        if phase2 is not None:
            self.percentages['phase2'] = max(0, min(100, phase2))
        
        # Redessiner les arcs
        self._create_arc(
            self.radius_inner,
            self.percentages['current'],
            self.colors['current'],
            'arc_current'
        )
        
        self._create_arc(
            self.radius_middle,
            self.percentages['phase1'],
            self.colors['phase1'],
            'arc_phase1'
        )
        
        self._create_arc(
            self.radius_outer,
            self.percentages['phase2'],
            self.colors['phase2'],
            'arc_phase2'
        )
        
        # Mettre à jour le label central
        # Afficher la progression globale
        if self.percentages['phase2'] > 0:
            display_percentage = (self.percentages['phase1'] + self.percentages['phase2']) / 2
        else:
            display_percentage = self.percentages['phase1']
        
        self.percentage_label.configure(text=f"{int(display_percentage)}%")
    
    def reset(self):
        """Réinitialise tous les cercles."""
        self.update_progress(current=0, phase1=0, phase2=0)
        self.canvas.delete("arc_current")
        self.canvas.delete("arc_phase1")
        self.canvas.delete("arc_phase2")