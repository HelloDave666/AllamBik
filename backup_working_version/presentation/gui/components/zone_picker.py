"""
Zone Picker - Sélecteur de zone pour le scan OCR
"""
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import io
from typing import Optional, Tuple, Callable


class ZonePicker(ctk.CTkToplevel):
    """
    Fenêtre overlay pour sélectionner une zone de scan.
    """
    
    def __init__(self, parent, screenshot: bytes = None, on_zone_selected: Optional[Callable] = None):
        super().__init__(parent)
        
        self.on_zone_selected = on_zone_selected
        self.screenshot_bytes = screenshot
        
        # Variables pour la sélection
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.selection = None
        
        self._setup_window()
        self._create_ui()
        
        # Si pas de screenshot fourni, capturer l'écran
        if not self.screenshot_bytes:
            self._capture_screen()
    
    def _setup_window(self):
        """Configure la fenêtre overlay."""
        # Plein écran sans bordure
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)  # Légèrement transparent
        
        # Titre et configuration
        self.title("Sélectionner la zone de scan")
        self.configure(fg_color="#1a1a1a")
        
        # Bind escape pour fermer
        self.bind('<Escape>', lambda e: self.cancel())
    
    def _create_ui(self):
        """Crée l'interface de sélection."""
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Instructions en haut
        instruction_frame = ctk.CTkFrame(main_frame, fg_color="#2a2a2a", height=60)
        instruction_frame.pack(fill="x", pady=(0, 10))
        instruction_frame.pack_propagate(False)
        
        instruction_label = ctk.CTkLabel(
            instruction_frame,
            text="Cliquez et glissez pour sélectionner la zone où se trouvent les surlignements Kindle",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        instruction_label.pack(expand=True)
        
        # Canvas pour l'image et la sélection
        self.canvas = tk.Canvas(
            main_frame,
            highlightthickness=0,
            bg="#1a1a1a"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Boutons en bas
        button_frame = ctk.CTkFrame(main_frame, fg_color="#2a2a2a", height=80)
        button_frame.pack(fill="x", pady=(10, 0))
        button_frame.pack_propagate(False)
        
        # Container centré pour les boutons
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Bouton Valider
        self.validate_button = ctk.CTkButton(
            button_container,
            text="VALIDER LA ZONE",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200,
            height=45,
            fg_color="#00ff88",
            hover_color="#00cc66",
            text_color="#000000",
            state="disabled",
            command=self.validate
        )
        self.validate_button.pack(side="left", padx=10)
        
        # Bouton Annuler
        cancel_button = ctk.CTkButton(
            button_container,
            text="ANNULER",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200,
            height=45,
            fg_color="#3a3a3a",
            hover_color="#ff4444",
            command=self.cancel
        )
        cancel_button.pack(side="left", padx=10)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
    
    def _capture_screen(self):
        """Capture l'écran actuel."""
        screenshot = ImageGrab.grab()
        
        # Convertir en bytes
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        buffer.seek(0)
        self.screenshot_bytes = buffer.read()
        
        # Afficher l'image
        self._display_screenshot()
    
    def _display_screenshot(self):
        """Affiche le screenshot dans le canvas."""
        if not self.screenshot_bytes:
            return
        
        # Charger l'image
        image = Image.open(io.BytesIO(self.screenshot_bytes))
        
        # Redimensionner si nécessaire
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Garder un peu de marge
        max_width = screen_width - 40
        max_height = screen_height - 200
        
        # Calculer le ratio
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height
        ratio = min(width_ratio, height_ratio, 1.0)
        
        if ratio < 1.0:
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Stocker le ratio pour convertir les coordonnées
        self.scale_ratio = ratio
        self.original_width = image.width / ratio
        self.original_height = image.height / ratio
        
        # Convertir en PhotoImage
        self.photo = ImageTk.PhotoImage(image)
        
        # Afficher dans le canvas
        self.canvas.config(width=image.width, height=image.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
    
    def _on_mouse_down(self, event):
        """Début de la sélection."""
        self.start_x = event.x
        self.start_y = event.y
        
        # Supprimer l'ancienne sélection
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def _on_mouse_drag(self, event):
        """Mise à jour de la sélection."""
        if self.start_x is None:
            return
        
        # Supprimer le rectangle précédent
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # Dessiner le nouveau rectangle
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="#00ff88",
            width=3,
            dash=(5, 5)
        )
        
        # Ajouter un fond semi-transparent
        self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            fill="#00ff88",
            stipple="gray25",
            outline="",
            tags="selection"
        )
    
    def _on_mouse_up(self, event):
        """Fin de la sélection."""
        if self.start_x is None:
            return
        
        # Calculer la zone sélectionnée
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        # Vérifier que la zone est valide
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            # Convertir aux coordonnées originales
            self.selection = (
                int(x1 / self.scale_ratio),
                int(y1 / self.scale_ratio),
                int((x2 - x1) / self.scale_ratio),
                int((y2 - y1) / self.scale_ratio)
            )
            
            # Activer le bouton valider
            self.validate_button.configure(state="normal")
            
            # Afficher les coordonnées
            self._show_coordinates()
    
    def _show_coordinates(self):
        """Affiche les coordonnées sélectionnées."""
        if self.selection:
            x, y, w, h = self.selection
            coord_text = f"Zone sélectionnée: X={x}, Y={y}, Largeur={w}, Hauteur={h}"
            
            # Afficher sur le canvas
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                20,
                text=coord_text,
                font=("Arial", 14, "bold"),
                fill="#00ff88",
                tags="coords"
            )
    
    def validate(self):
        """Valide la sélection."""
        if self.selection and self.on_zone_selected:
            self.on_zone_selected(self.selection)
        
        self.destroy()
    
    def cancel(self):
        """Annule la sélection."""
        self.destroy()


class ZonePickerButton(ctk.CTkButton):
    """
    Bouton pour lancer le zone picker.
    """
    
    def __init__(self, parent, on_zone_selected: Optional[Callable] = None, **kwargs):
        # Configuration par défaut
        kwargs.setdefault("text", "📐 DÉFINIR ZONE DE SCAN")
        kwargs.setdefault("font", ctk.CTkFont(size=12, weight="bold"))
        kwargs.setdefault("height", 40)
        kwargs.setdefault("fg_color", "#ffaa00")
        kwargs.setdefault("hover_color", "#ff8800")
        
        super().__init__(parent, command=self._open_picker, **kwargs)
        
        self.on_zone_selected = on_zone_selected
        self.selected_zone = None
    
    def _open_picker(self):
        """Ouvre le sélecteur de zone."""
        picker = ZonePicker(
            self.winfo_toplevel(),
            on_zone_selected=self._on_zone_selected
        )
        picker.wait_window()  # Attendre la fermeture
    
    def _on_zone_selected(self, zone: Tuple[int, int, int, int]):
        """Callback quand une zone est sélectionnée."""
        self.selected_zone = zone
        
        # Mettre à jour le texte du bouton
        x, y, w, h = zone
        self.configure(text=f"📐 Zone: {w}x{h} à ({x},{y})")
        
        # Appeler le callback externe
        if self.on_zone_selected:
            self.on_zone_selected(zone)