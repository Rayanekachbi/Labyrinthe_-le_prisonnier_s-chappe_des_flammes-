import tkinter as tk
from tkinter import messagebox
import sys
import os
from typing import List, Tuple

# On importe ta classe de simulation originale
try:
    from simulation import LabyrinthSimulation
except ImportError:
    print("Erreur : simulation.py introuvable.")
    sys.exit(1)

# --- CONFIGURATION VISUELLE ---
BG_COLOR = "#1E1E2E"
PANEL_COLOR = "#2A2A3C"
TEXT_COLOR = "#CDD6F4"
ACCENT_COLOR = "#89B4FA"
BUTTON_BG = "#45475A"
GRID_BG = "#313244"
GRID_LINE = "#45475A"
PATH_COLOR = "#F9E2AF"      # Jaune pour le chemin
SUCCESS_COLOR = "#A6E3A1"   # Vert
FAIL_COLOR = "#F38BA8"      # Rouge

FONT_TITLE = ("Helvetica Neue", 20, "bold")
FONT_BOLD = ("Helvetica Neue", 11, "bold")

# --- EXTENSION DE LA SIMULATION ---
class ExtendedSimulation(LabyrinthSimulation):
    def __init__(self, n_rows, m_cols, grid):
        super().__init__(n_rows, m_cols, grid)
        # On garde une copie profonde de la grille originale pour le Reset
        self.original_grid_copy = [row[:] for row in grid]
        self.fire_mode_static = False 

    def reset_grid(self):
        """ Remet la grille à zéro proprement """
        self.grid = [row[:] for row in self.original_grid_copy]
        self.prisoner_pos = self.find_positions()[0]

    def compute_fire_spread(self) -> List[List[int]]:
        """ Si mode statique, on empêche le feu de 'prévoir' l'avenir pour A* """
        if self.fire_mode_static:
            times = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid[r][c] == 'F':
                        times[r][c] = 0
                    elif self.grid[r][c] == '#':
                        times[r][c] = -1
            return times
        else:
            return super().compute_fire_spread()

# --- INTERFACE GRAPHIQUE ---
class LabyrinthGUI:
    def __init__(self, root, raw_instances):
        self.root = root
        self.root.title("Simulateur Labyrinthe - Mode Manuel & Auto")
        self.root.geometry("1100x800")
        self.root.configure(bg=BG_COLOR)
        
        self.raw_instances = raw_instances
        self.current_level_idx = 0
        self.sim = None
        
        # Variables d'état
        self.running = False
        self.game_over = False
        self.move_count = 0
        self.animation_speed = 300 # ms
        
        # Pour A*
        self.astar_path_visual = [] # Pour dessiner la ligne jaune (reste fixe)
        self.astar_path_moves = []  # Pour faire bouger le bonhomme (se vide)
        
        self.images = self.load_images()
        self.setup_ui()
        self.load_level(0)

    def load_images(self):
        imgs = {}
        path = "icons/" # Assure-toi que le dossier icons est au même endroit
        try:
            imgs['D'] = tk.PhotoImage(file=os.path.join(path, "player.png"))
            imgs['F'] = tk.PhotoImage(file=os.path.join(path, "fire.png"))
            imgs['#'] = tk.PhotoImage(file=os.path.join(path, "wall.png"))
            imgs['S'] = tk.PhotoImage(file=os.path.join(path, "exit.png"))
        except Exception:
            pass # On utilisera des couleurs si pas d'images
        return imgs

    def setup_ui(self):
        # Titre
        tk.Label(self.root, text="SIMULATION LABYRINTHE", font=FONT_TITLE, bg=BG_COLOR, fg=ACCENT_COLOR, pady=10).pack(fill=tk.X)

        # Main Container
        main = tk.Frame(self.root, bg=BG_COLOR)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # GAUCHE : Canvas
        self.canvas = tk.Canvas(main, bg=GRID_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        self.canvas.bind("<Configure>", lambda e: self.draw_grid())

        # DROITE : Panneau de contrôle
        controls = tk.Frame(main, bg=PANEL_COLOR, width=300, padx=15, pady=15)
        controls.pack(side=tk.RIGHT, fill=tk.Y)
        controls.pack_propagate(False)

        # 1. Navigation Niveaux
        nav = tk.Frame(controls, bg=PANEL_COLOR)
        nav.pack(fill=tk.X, pady=(0, 20))
        self.lbl_level = tk.Label(nav, text="NIVEAU 1", font=FONT_TITLE, bg=PANEL_COLOR, fg=TEXT_COLOR)
        self.lbl_level.pack()
        
        btn_box = tk.Frame(nav, bg=PANEL_COLOR)
        btn_box.pack(fill=tk.X, pady=5)
        tk.Button(btn_box, text="< PRÉCÉDENT", command=self.prev_level, bg=BUTTON_BG, fg=TEXT_COLOR, relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_box, text="SUIVANT >", command=self.next_level, bg=BUTTON_BG, fg=TEXT_COLOR, relief=tk.FLAT).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        # 2. Stats
        self.lbl_moves = tk.Label(controls, text="Déplacements : 0", bg=BUTTON_BG, fg=ACCENT_COLOR, font=FONT_BOLD, pady=5)
        self.lbl_moves.pack(fill=tk.X, pady=5)
        self.lbl_status = tk.Label(controls, text="PRÊT", bg=BUTTON_BG, fg=TEXT_COLOR, pady=5)
        self.lbl_status.pack(fill=tk.X)

        # 3. Paramètres
        tk.Label(controls, text="PARAMÈTRES", bg=PANEL_COLOR, fg=ACCENT_COLOR, font=FONT_BOLD).pack(anchor="w", pady=(20, 5))
        
        # Algo
        self.algo_var = tk.StringVar(value="astar")
        tk.Radiobutton(controls, text="Algo : A* (Optimal)", variable=self.algo_var, value="astar", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")
        tk.Radiobutton(controls, text="Algo : Naïf (Vue directe)", variable=self.algo_var, value="simple", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")

        # Feu
        self.fire_var = tk.StringVar(value="dynamic")
        tk.Label(controls, text="Feu :", bg=PANEL_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(10, 0))
        tk.Radiobutton(controls, text="Dynamique (Se propage)", variable=self.fire_var, value="dynamic", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")
        tk.Radiobutton(controls, text="Statique (Fixe)", variable=self.fire_var, value="static", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")

        # Mode Lecture (Auto / Manuel)
        self.play_mode = tk.StringVar(value="auto")
        tk.Label(controls, text="Lecture :", bg=PANEL_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(10, 0))
        tk.Radiobutton(controls, text="Automatique", variable=self.play_mode, value="auto", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR).pack(anchor="w")
        tk.Radiobutton(controls, text="Manuel (Pas à pas)", variable=self.play_mode, value="manual", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR).pack(anchor="w")

        # 4. Actions Principales
        tk.Label(controls, text="ACTIONS", bg=PANEL_COLOR, fg=ACCENT_COLOR, font=FONT_BOLD).pack(anchor="w", pady=(20, 5))
        
        # Bouton Démarrer / Étape
        self.btn_action = tk.Button(controls, text="DÉMARRER", command=self.on_action_click, bg=ACCENT_COLOR, fg=BG_COLOR, font=("Arial", 14, "bold"), relief=tk.FLAT, pady=10)
        self.btn_action.pack(fill=tk.X, pady=5)
        
        # Bouton Reset
        tk.Button(controls, text="RÉINITIALISER", command=self.reset_level, bg="#E78284", fg=BG_COLOR, font=FONT_BOLD, relief=tk.FLAT, pady=5).pack(fill=tk.X, pady=5)

    # --- LOGIQUE ---
    def load_level(self, idx):
        if not self.raw_instances: return
        self.current_level_idx = idx % len(self.raw_instances)
        n, m, grid = self.raw_instances[self.current_level_idx]
        self.sim = ExtendedSimulation(n, m, grid)
        self.lbl_level.config(text=f"NIVEAU {self.current_level_idx + 1}")
        self.reset_level()

    def prev_level(self): self.load_level(self.current_level_idx - 1)
    def next_level(self): self.load_level(self.current_level_idx + 1)

    def reset_level(self):
        """ Réinitialise tout pour recommencer proprement """
        self.running = False
        self.game_over = False
        self.move_count = 0
        if self.sim: self.sim.reset_grid()
        
        self.astar_path_visual = []
        self.astar_path_moves = []
        
        self.lbl_status.config(text="PRÊT", fg=TEXT_COLOR)
        self.lbl_moves.config(text="Déplacements : 0")
        self.btn_action.config(text="DÉMARRER", bg=ACCENT_COLOR, state=tk.NORMAL)
        self.draw_grid()

    def on_action_click(self):
        """ Gère le clique sur le gros bouton d'action """
        mode = self.play_mode.get()
        
        # Si la partie est finie, le bouton ne fait rien (il faut reset)
        if self.game_over:
            return

        # 1. Initialisation (Premier clic)
        if self.move_count == 0 and not self.running and not self.astar_path_moves:
            # Configurer la simulation
            self.sim.fire_mode_static = (self.fire_var.get() == "static")
            
            # Pré-calculer A* si sélectionné
            if self.algo_var.get() == "astar":
                path = self.sim.solve_astar_dynamique()
                if path:
                    self.astar_path_visual = list(path) # Copie pour dessin
                    self.astar_path_moves = list(path)  # Copie pour mouvement
                    self.lbl_status.config(text="CHEMIN CALCULÉ", fg=PATH_COLOR)
                else:
                    self.lbl_status.config(text="IMPOSSIBLE (A*)", fg=FAIL_COLOR)
                    # On continue quand même pour voir le blocage
            
            self.running = True
        
        # 2. Exécution
        if mode == "auto":
            if self.btn_action['text'] == "PAUSE":
                # Mettre en pause
                self.running = False
                self.btn_action.config(text="REPRENDRE")
            else:
                # Lancer l'auto
                self.running = True
                self.btn_action.config(text="PAUSE", bg=PATH_COLOR)
                self.run_step_auto()
                
        elif mode == "manual":
            self.btn_action.config(text="ÉTAPE SUIVANTE", bg=PATH_COLOR)
            self.run_single_step()

    def run_step_auto(self):
        """ Boucle automatique """
        if not self.running or self.game_over: return
        
        self.run_single_step()
        
        if not self.game_over:
            self.root.after(self.animation_speed, self.run_step_auto)

    def run_single_step(self):
        """ Exécute UN SEUL mouvement (Logique centrale) """
        if self.game_over: return

        # 1. Propagation du feu (si dynamique)
        if self.fire_var.get() == "dynamic":
            if self.sim.update_fire_state():
                self.end_game(False, "BRÛLÉ PAR LE FEU !")
                return

        # 2. Mouvement du joueur
        moved = False
        algo = self.algo_var.get()

        if algo == "astar":
            if self.astar_path_moves:
                next_pos = self.astar_path_moves.pop(0)
                
                # Vérif sécurité (mur ou feu apparu ?)
                cell = self.sim.grid[next_pos[0]][next_pos[1]]
                if cell == 'F' or cell == '#':
                    self.end_game(False, "CHEMIN BLOQUÉ !")
                    return
                
                # Déplacement manuel dans la grille
                cr, cc = self.sim.prisoner_pos
                self.sim.grid[cr][cc] = '.'
                self.sim.grid[next_pos[0]][next_pos[1]] = 'D'
                self.sim.prisoner_pos = next_pos
                moved = True
                
                # Victoire A* (si liste vide et pas mort)
                if not self.astar_path_moves:
                    self.end_game(True, "SORTIE ATTEINTE (A*) !")
                    
            elif not self.astar_path_moves and self.move_count == 0:
                # Pas de chemin trouvé dès le début
                pass 

        elif algo == "simple":
            # Algorithme naïf
            if self.sim.move_prisoner():
                self.end_game(True, "SORTIE ATTEINTE !")
                moved = True # Le dernier move est compté
            else:
                # Vérif si bloqué
                if self.sim.count_possible_moves(*self.sim.prisoner_pos) > 0:
                    moved = True
                else:
                    # Bloqué sans victoire
                    pass

        if moved:
            self.move_count += 1
            self.lbl_moves.config(text=f"Déplacements : {self.move_count}")
        
        self.draw_grid()

    def end_game(self, victory, msg):
        self.game_over = True
        self.running = False
        color = SUCCESS_COLOR if victory else FAIL_COLOR
        self.lbl_status.config(text=msg, fg=color)
        self.btn_action.config(text="TERMINÉ (RESET ?)", bg=BUTTON_BG, state=tk.DISABLED)
        self.draw_grid()

    # --- DESSIN ---
    def draw_grid(self):
        self.canvas.delete("all")
        if not self.sim: return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        rows, cols = self.sim.rows, self.sim.cols
        cell_size = min(w // cols, h // rows) if rows > 0 else 20
        if cell_size < 5: cell_size = 5
        
        ox = (w - cols * cell_size) // 2
        oy = (h - rows * cell_size) // 2

        # 1. Chemin jaune (sous les entités)
        if self.astar_path_visual and self.algo_var.get() == "astar":
            coords = []
            # On dessine tout le chemin prévu
            full = [self.sim.prisoner_pos] + self.astar_path_visual # Visuel approximatif du reste
            # Pour faire plus propre : on dessine tout le chemin calculé initialement
            # Mais comme self.astar_path_visual est statique dans ma modif, ça va.
            # Correction : self.astar_path_visual contient tout le chemin depuis le début.
            
            for r, c in self.astar_path_visual:
                x = ox + c * cell_size + cell_size // 2
                y = oy + r * cell_size + cell_size // 2
                coords.extend([x, y])
            
            # On ajoute le joueur actuel au début du tracé pour relier visuellement
            pr, pc = self.sim.prisoner_pos
            px, py = ox + pc * cell_size + cell_size // 2, oy + pr * cell_size + cell_size // 2
            coords = [px, py] + coords
            
            if len(coords) >= 4:
                self.canvas.create_line(coords, fill=PATH_COLOR, width=3, capstyle=tk.ROUND)

        # 2. Entités
        self.keep_imgs = []
        for r in range(rows):
            for c in range(cols):
                char = self.sim.grid[r][c]
                x = ox + c * cell_size
                y = oy + r * cell_size
                
                img = None
                if char == 'D' and 'D' in self.images: img = self.images['D']
                elif char in ['F', 'A'] and 'F' in self.images: img = self.images['F']
                elif char == '#' and '#' in self.images: img = self.images['#']
                elif char == 'S' and 'S' in self.images: img = self.images['S']

                if img:
                    ratio = int(img.width() / cell_size)
                    if ratio < 1: ratio = 1
                    try:
                        final = img.subsample(ratio)
                        self.keep_imgs.append(final)
                        self.canvas.create_image(x + cell_size//2, y + cell_size//2, image=final)
                    except: pass
                else:
                    # Mode sans image (couleurs)
                    col = None
                    if char == '#': col = "#444"
                    elif char == 'F': col = "#E78284"
                    elif char == 'D': col = "#89DCEB"
                    elif char == 'S': col = "#A6E3A1"
                    if col:
                        self.canvas.create_rectangle(x, y, x+cell_size, y+cell_size, fill=col, outline="")

        # Grille
        for i in range(rows + 1):
            py = oy + i * cell_size
            self.canvas.create_line(ox, py, ox + cols * cell_size, py, fill=GRID_LINE)
        for i in range(cols + 1):
            px = ox + i * cell_size
            self.canvas.create_line(px, oy, px, rows * cell_size, fill=GRID_LINE)

# --- PARSEUR ---
def parse_file(filename):
    insts = []
    try:
        with open(filename, 'r') as f: content = f.read().split()
        if not content: return []
        it = iter(content)
        try:
            num = int(next(it))
            for _ in range(num):
                r, c = int(next(it)), int(next(it))
                g = [list(next(it)) for _ in range(r)]
                insts.append((r, c, g))
        except StopIteration: pass
    except Exception as e:
        print(f"Erreur: {e}")
    return insts

if __name__ == "__main__":
    file_to_load = sys.argv[1] if len(sys.argv) > 1 else "test3.txt"
    if not os.path.exists(file_to_load):
        # Données de secours
        data = [(5, 5, [list("....."), list(".D.S."), list("..F.."), list("....."), list(".....")])]
    else:
        data = parse_file(file_to_load)

    root = tk.Tk()
    app = LabyrinthGUI(root, data)
    root.mainloop()