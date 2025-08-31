"""
Test de performance UI - Version standalone
Aucune dépendance au projet AllamBik
"""
import customtkinter as ctk
import time
import tkinter as tk

print("Lancement du test de performance UI...")

class PerformanceTestApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Test Performance AllamBik - 2000 éléments")
        self.window.geometry("1400x800")
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()
        self.test_data = []
        
    def setup_ui(self):
        """Configure l'interface de test."""
        # Frame principale
        main = ctk.CTkFrame(self.window)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main, height=100)
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header, 
            text="TEST PERFORMANCE: Interface avec 2000 highlights",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=20)
        
        # Contrôles
        controls = ctk.CTkFrame(main)
        controls.pack(fill="x", pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            controls,
            text="Prêt pour le test",
            font=("Arial", 14)
        )
        self.status_label.pack(side="left", padx=20)
        
        # Boutons de test
        btn_frame = ctk.CTkFrame(controls)
        btn_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Test 100 éléments",
            command=lambda: self.test_loading(100),
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Test 500 éléments",
            command=lambda: self.test_loading(500),
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Test 2000 éléments",
            command=lambda: self.test_loading(2000),
            width=150,
            fg_color="orange"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Nettoyer",
            command=self.clear_display,
            width=100,
            fg_color="red"
        ).pack(side="left", padx=5)
        
        # Zone d'affichage
        display_frame = ctk.CTkFrame(main)
        display_frame.pack(fill="both", expand=True)
        
        # Info performance
        self.perf_label = ctk.CTkLabel(
            display_frame,
            text="",
            font=("Arial", 12),
            text_color="yellow"
        )
        self.perf_label.pack(pady=5)
        
        # Scrollable frame pour les éléments
        self.scroll = ctk.CTkScrollableFrame(display_frame)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
    def test_loading(self, count):
        """Teste le chargement de N éléments."""
        print(f"\nTest avec {count} éléments...")
        start_time = time.time()
        
        # Nettoyer
        self.clear_display()
        
        # Mise à jour status
        self.status_label.configure(text=f"Chargement de {count} éléments...")
        self.window.update()
        
        # Limiter l'affichage pour performance
        max_display = 100
        actual_display = min(count, max_display)
        
        # Créer les widgets
        for i in range(actual_display):
            # Frame container
            item_frame = ctk.CTkFrame(self.scroll, height=80)
            item_frame.pack(fill="x", padx=5, pady=3)
            
            # Contenu
            header_frame = ctk.CTkFrame(item_frame)
            header_frame.pack(fill="x", padx=10, pady=(5, 0))
            
            # Numéro et page
            ctk.CTkLabel(
                header_frame,
                text=f"#{i+1}/{count}",
                font=("Arial", 10, "bold"),
                text_color="cyan"
            ).pack(side="left")
            
            ctk.CTkLabel(
                header_frame,
                text=f"Page {i//3 + 1}",
                font=("Arial", 10),
                text_color="gray"
            ).pack(side="right")
            
            # Texte
            text_label = ctk.CTkLabel(
                item_frame,
                text=f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Test highlight numéro {i+1}.",
                anchor="w",
                justify="left",
                wraplength=800
            )
            text_label.pack(fill="x", padx=10, pady=5)
            
            # Mise à jour périodique
            if i % 10 == 0:
                self.window.update()
        
        # Temps écoulé
        elapsed = time.time() - start_time
        
        # Afficher les stats
        if count > max_display:
            warning_label = ctk.CTkLabel(
                self.scroll,
                text=f"⚠️ Performance: Seulement {max_display} éléments affichés sur {count} total",
                font=("Arial", 14, "bold"),
                text_color="orange"
            )
            warning_label.pack(pady=20)
        
        # Mise à jour status
        self.status_label.configure(
            text=f"✓ {actual_display}/{count} éléments chargés"
        )
        
        self.perf_label.configure(
            text=f"Temps de rendu: {elapsed:.2f}s | {actual_display/elapsed:.0f} éléments/sec"
        )
        
        print(f"✓ Test terminé: {actual_display} éléments en {elapsed:.2f}s")
        
    def clear_display(self):
        """Nettoie l'affichage."""
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.status_label.configure(text="Affichage nettoyé")
        self.perf_label.configure(text="")
        
    def run(self):
        """Lance l'application de test."""
        print("Interface de test prête")
        print("-" * 60)
        print("Cliquez sur les boutons pour tester différentes charges")
        print("Le bouton orange teste 2000 éléments (cas réel)")
        self.window.mainloop()

# Lancer le test
if __name__ == "__main__":
    app = PerformanceTestApp()
    app.run()
