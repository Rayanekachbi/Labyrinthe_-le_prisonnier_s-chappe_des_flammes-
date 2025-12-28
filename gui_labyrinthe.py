import tkinter as tk
from tkinter import messagebox
import heapq
import sys
import os
from typing import List, Tuple, Optional

# --- CLASSE DE SIMULATION (Ta logique, adaptée) ---
class LabyrinthSimulation:
    def __init__(self, n_rows: int, m_cols: int, grid: List[List[str]]):
        self.rows = n_rows
        self.cols = m_cols
        self.original_grid = [row[:] for row in grid] # Pour le reset
        self.grid = [row[:] for row in grid]
        self.prisoner_pos = self.find_positions()[0]
        self.path_to_draw = []

    def reset(self):
        self.grid = [row[:] for row in self.original_grid]
        self.prisoner_pos = self.find_positions()[0]
        self.path_to_draw = []

    def find_positions(self) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        p, s = None, None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'D': p = (r, c)
                elif self.grid[r][c] == 'S': s = (r, c)
        return p, s

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # --- A* STATIQUE (Feu = Mur) ---
    def solve_astar_static(self) -> Optional[List[Tuple[int, int]]]:
        start = self.prisoner_pos
        _, goal = self.find_positions()
        if not goal: return None

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            r, c = current
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    # Le feu statique (F) est un obstacle comme un mur (#)
                    if self.grid[nr][nc] in ['#', 'F']: continue
                    
                    tentative_g = g_score[current] + 1
                    neighbor = (nr, nc)
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + self.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f, neighbor))
        return None

    # --- LOGIQUE DYNAMIQUE (Simulation tour par tour) ---
    def burn_around(self, r, c):
        touch_player_or_exit = False
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                cell = self.grid[nr][nc]
                if cell == '.': self.grid[nr][nc] = 'A' # Futur feu
                elif cell in ['D', 'S']: touch_player_or_exit = True
        return touch_player_or_exit

    def update_fire_state(self) -> bool:
        # 1. Transformer les futurs feux (A) en feux actuels (F)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'A': self.grid[r][c] = 'F'
        
        # 2. Propager les feux actuels
        game_over = False
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    if self.burn_around(r, c): game_over = True
        return game_over

    def move_prisoner_naive(self) -> bool:
        r, c = self.prisoner_pos
        _, s_pos = self.find_positions()
        if not s_pos: return False
        er, ec = s_pos

        # Victoire immédiate ?
        if abs(r-er) + abs(c-ec) == 1: return True 

        # Mouvement Glouton (le plus proche de la sortie)
        best_move = None
        min_dist = float('inf')
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] in ['.', 'S']: # On peut aller sur du sol ou la sortie
                    d = abs(nr-er) + abs(nc-ec)
                    if d < min_dist:
                        min_dist = d
                        best_move = (nr, nc)
        
        if best_move:
            self.grid[r][c] = '.' # On laisse du vide derrière
            self.grid[best_move[0]][best_move[1]] = 'D'
            self.prisoner_pos = best_move
        return False

# --- CONSTANTES DE STYLE (Mode Sombre Moderne) ---
BG_COLOR = "#1E1E2E"        # Fond principal (Gris foncé bleuté)
PANEL_COLOR = "#2A2A3C"     # Fond des panneaux (Un peu plus clair)
TEXT_COLOR = "#CDD6F4"      # Blanc cassé pour le texte
ACCENT_COLOR = "#89B4FA"    # Bleu clair pour les boutons/titres
BUTTON_BG = "#45475A"       # Fond des boutons
BUTTON_ACTIVE = "#585B70"   # Fond bouton survolé
GRID_BG = "#313244"         # Fond de la grille
GRID_LINE = "#45475A"       # Lignes de la grille
PATH_COLOR = "#F9E2AF"      # Jaune pâle pour le chemin A*

FONT_TITLE = ("Helvetica Neue", 24, "bold")
FONT_TEXT = ("Helvetica Neue", 12)
FONT_BUTTON = ("Helvetica Neue", 14, "bold")

# --- L'INTERFACE GRAPHIQUE ---
class LabyrinthGUI:
    def __init__(self, root, raw_instances):
        self.root = root
        self.root.title("Labyrinthe d'Ayutthaya - Simulateur")
        self.root.configure(bg=BG_COLOR)
        self.raw_instances = raw_instances
        self.current_level_idx = 0
        self.sim = None
        self.running = False
        self.animation_speed = 400 # Vitesse en ms
        self.timer_seconds = 0
        self.timer_job = None

        # Charger les images
        self.images = self.load_images()

        # --- TITRE ---
        tk.Label(root, text="LABYRINTHE D'AYUTTHAYA", font=FONT_TITLE, bg=BG_COLOR, fg=ACCENT_COLOR, pady=20).pack()

        # --- CONTENEUR PRINCIPAL ---
        main_container = tk.Frame(root, bg=BG_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

        # --- GAUCHE : LA GRILLE ---
        grid_frame = tk.Frame(main_container, bg=PANEL_COLOR, bd=2, relief=tk.RIDGE)
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(grid_frame, bg=GRID_BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Redessiner quand la fenêtre change de taille
        self.canvas.bind("<Configure>", lambda event: self.draw_grid())

        # --- DROITE : PANNEAU DE CONTRÔLE ---
        control_panel = tk.Frame(main_container, bg=PANEL_COLOR, width=300, padx=20, pady=20, bd=2, relief=tk.RIDGE)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        control_panel.pack_propagate(False) # Fixe la largeur

        # Boutons d'action
        self.btn_start = tk.Button(control_panel, text="DÉMARRER", command=self.toggle_run, bg=ACCENT_COLOR, fg=BG_COLOR, font=FONT_BUTTON, relief=tk.FLAT, activebackground=BUTTON_ACTIVE, cursor="hand2")
        self.btn_start.pack(fill=tk.X, pady=10)

        tk.Button(control_panel, text="RÉINITIALISER", command=self.reset_level, bg=BUTTON_BG, fg=TEXT_COLOR, font=FONT_BUTTON, relief=tk.FLAT, activebackground=BUTTON_ACTIVE, cursor="hand2").pack(fill=tk.X, pady=10)

        tk.Button(control_panel, text="NIVEAU SUIVANT", command=self.next_level, bg=BUTTON_BG, fg=TEXT_COLOR, font=FONT_BUTTON, relief=tk.FLAT, activebackground=BUTTON_ACTIVE, cursor="hand2").pack(fill=tk.X, pady=10)

        # Choix du mode
        tk.Label(control_panel, text="MODE :", bg=PANEL_COLOR, fg=ACCENT_COLOR, font=FONT_BUTTON).pack(anchor="w", pady=(30, 5))        
        self.mode_var = tk.StringVar(value="static")
        rb_style = {"bg": PANEL_COLOR, "fg": TEXT_COLOR, "font": FONT_TEXT, "selectcolor": PANEL_COLOR, "activebackground": PANEL_COLOR}
        tk.Radiobutton(control_panel, text="Statique (A*)", variable=self.mode_var, value="static", command=self.reset_level, **rb_style).pack(anchor="w")
        tk.Radiobutton(control_panel, text="Dynamique (Simu)", variable=self.mode_var, value="dynamic", command=self.reset_level, **rb_style).pack(anchor="w")

        # Panneau d'infos (Timer/Statut)
        info_box = tk.Frame(control_panel, bg=BUTTON_BG, padx=15, pady=15, bd=1, relief=tk.SOLID)
        info_box.pack(fill=tk.X, pady=(40, 0), side=tk.BOTTOM)
        
        self.time_label = tk.Label(info_box, text="TEMPS: 00:00", bg=BUTTON_BG, fg=TEXT_COLOR, font=FONT_TEXT)
        self.time_label.pack(anchor="w")
        
        self.status_label = tk.Label(info_box, text="STATUT: PRÊT", bg=BUTTON_BG, fg=TEXT_COLOR, font=FONT_TEXT)
        self.status_label.pack(anchor="w", pady=(5,0))

        # Charger le premier niveau
        self.load_current_level()

    def load_images(self):
        """ Charge et redimensionne les images (nécessite PIL/Pillow pour le redimensionnement propre, 
            ici on utilise une astuce Tkinter de base qui est moins jolie mais sans dépendance) """
        imgs = {}
        try:
            # On charge les images en mémoire. Le redimensionnement se fera dans draw_grid.
            imgs['D'] = tk.PhotoImage(file="icons/player.png")
            imgs['F'] = tk.PhotoImage(file="icons/FEU.png")
            imgs['A'] = tk.PhotoImage(file="icons/fire.png")
            imgs['#'] = tk.PhotoImage(file="icons/wall.png")
            imgs['S'] = tk.PhotoImage(file="icons/exit.png")
        except Exception as e:
            print(f"Erreur de chargement d'image: {e}")
            messagebox.showwarning("Images manquantes", "Assurez-vous que player.png, fire.png, wall.png et exit.png sont dans le dossier.")
        return imgs

    def load_current_level(self):
        if not self.raw_instances: return
        n, m, grid_data = self.raw_instances[self.current_level_idx]
        self.sim = LabyrinthSimulation(n, m, grid_data)
        self.reset_gui_state()

    def reset_level(self):
        if self.sim: self.sim.reset()
        self.reset_gui_state()

    def reset_gui_state(self):
        self.running = False
        if self.timer_job: self.root.after_cancel(self.timer_job)
        self.timer_seconds = 0
        self.update_timer_display()
        self.btn_start.config(text="DÉMARRER", bg=ACCENT_COLOR)
        self.status_label.config(text="STATUT: PRÊT", fg=TEXT_COLOR)
        self.draw_grid()

    def next_level(self):
        self.current_level_idx = (self.current_level_idx + 1) % len(self.raw_instances)
        self.load_current_level()

    def update_timer(self):
        if self.running and self.mode_var.get() == "dynamic":
            self.timer_seconds += 1
            self.update_timer_display()
            self.timer_job = self.root.after(1000, self.update_timer)

    def update_timer_display(self):
        mins, secs = divmod(self.timer_seconds, 60)
        self.time_label.config(text=f"TEMPS: {mins:02d}:{secs:02d}")

    def toggle_run(self):
        if not self.running:
            self.running = True
            self.btn_start.config(text="PAUSE", bg="#EBA0AC") # Rouge clair
            self.status_label.config(text="STATUT: EN COURS", fg=ACCENT_COLOR)
            
            if self.mode_var.get() == "static":
                self.run_static()
            else:
                self.timer_job = self.root.after(1000, self.update_timer)
                self.run_dynamic_step()
        else:
            self.running = False
            if self.timer_job: self.root.after_cancel(self.timer_job)
            self.btn_start.config(text="REPRENDRE", bg=ACCENT_COLOR)
            self.status_label.config(text="STATUT: PAUSE", fg="#F9E2AF") # Jaune

    def run_static(self):
        path = self.sim.solve_astar_static()
        if path:
            self.sim.path_to_draw = path
            self.status_label.config(text="STATUT: CHEMIN TROUVÉ", fg="#A6E3A1") # Vert
        else:
            self.status_label.config(text="STATUT: IMPOSSIBLE", fg="#F38BA8") # Rouge
        self.draw_grid()
        self.running = False
        self.btn_start.config(text="DÉMARRER", bg=ACCENT_COLOR)

    def run_dynamic_step(self):
        if not self.running: return

        # 1. Feu
        game_over = self.sim.update_fire_state()
        if game_over:
            self.end_game("STATUT: ÉCHEC (BRÛLÉ)", "#F38BA8")
            return

        # 2. Prisonnier
        victoire = self.sim.move_prisoner_naive()
        if victoire:
            self.end_game("STATUT: SUCCÈS (ÉCHAPPÉ)", "#A6E3A1")
            return

        self.draw_grid()
        self.root.after(self.animation_speed, self.run_dynamic_step)

    def end_game(self, text, color):
        self.running = False
        if self.timer_job: self.root.after_cancel(self.timer_job)
        self.status_label.config(text=text, fg=color)
        self.btn_start.config(text="DÉMARRER", bg=ACCENT_COLOR)
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        self.keep_images = []
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        if c_width < 50: return

        cell_w = c_width / self.sim.cols
        cell_h = c_height / self.sim.rows
        # On garde des cellules carrées pour que les images ne soient pas déformées
        cell_size = min(cell_w, cell_h)
        
        # Centrer la grille
        start_x = (c_width - (cell_size * self.sim.cols)) / 2
        start_y = (c_height - (cell_size * self.sim.rows)) / 2

        # Dessiner les lignes de la grille
        for r in range(self.sim.rows + 1):
            y = start_y + r * cell_size
            self.canvas.create_line(start_x, y, start_x + self.sim.cols * cell_size, y, fill=GRID_LINE)
        for c in range(self.sim.cols + 1):
            x = start_x + c * cell_size
            self.canvas.create_line(x, start_y, x, self.sim.rows * cell_size, fill=GRID_LINE)

        # Dessiner le contenu
        for r in range(self.sim.rows):
            for c in range(self.sim.cols):
                char = self.sim.grid[r][c]
                x1 = start_x + c * cell_size
                y1 = start_y + r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                center_x, center_y = (x1+x2)/2, (y1+y2)/2

                # Chemin A* (Mode statique)
                if self.mode_var.get() == "static" and (r, c) in self.sim.path_to_draw and char == '.':
                     self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill=PATH_COLOR, outline="")

                # Images (si disponibles)
                img_key = char if char in self.images else None
                if char == 'A': img_key = 'F' # A et F utilisent la même image de feu

                if img_key:
                    # Astuce de redimensionnement Tkinter (subsample)
                    # Ce n'est pas parfait mais ça évite d'utiliser la librairie Pillow
                    original_img = self.images[img_key]
                    # Calcul du facteur de réduction (Tkinter ne sait faire que des entiers)
                    scale_factor = int(original_img.width() / (cell_size * 0.8))
                    if scale_factor < 1: scale_factor = 1
                    
                    try:
                        resized_img = original_img.subsample(scale_factor, scale_factor)
                        
                        # --- SAUVEGARDE LA RÉFÉRENCE ---
                        self.keep_images.append(resized_img) 
                        # -------------------------------
                        
                        self.canvas.create_image(center_x, center_y, image=resized_img)
                    except Exception:
                        # Si l'image est trop petite ou bug, on met du texte
                        pass
                
                # Fallback texte si pas d'image (pour S, ou si erreur de chargement)
                elif char == 'S' and 'S' not in self.images:
                     self.canvas.create_text(center_x, center_y, text="EXIT", fill=ACCENT_COLOR, font=("Arial", int(cell_size/4), "bold"))


# --- PARSER DE FICHIER ---
def parse_file(filename):
    instances = []
    try:
        with open(filename, 'r') as f: content = f.read().split()
        iterator = iter(content)
        num_instances = int(next(iterator))
        for _ in range(num_instances):
            r, c = int(next(iterator)), int(next(iterator))
            grid = [list(next(iterator)) for _ in range(r)]
            instances.append((r, c, grid))
    except Exception as e:
        print(f"Erreur lecture: {e}. Utilisation de données de test.")
        return []
    return instances

# --- MAIN ---
if __name__ == "__main__":
    # Tente de charger 'test.txt', sinon utilise des données par défaut
    data = parse_file("test3.txt")
    if not data:
        data = [(5, 5, [list("....."), list("F.D.S"), list("....."), list("....."), list(".....")]),
                (5, 5, [list(".#S.."), list("D#..."), list(".#..."), list(".#..."), list(".....")])]

    root = tk.Tk()
    root.geometry("1000x700") # Taille initiale
    app = LabyrinthGUI(root, data)
    root.mainloop()