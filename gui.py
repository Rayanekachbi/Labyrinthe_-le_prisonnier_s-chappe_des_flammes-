import tkinter as tk
import sys
import os
import math
from typing import List, Tuple
from simulation import LabyrinthSimulation

# couleurs de l'interface
BG_COLOR = "#1E1E2E"
PANEL_COLOR = "#2A2A3C"
TEXT_COLOR = "#CDD6F4"
ACCENT_COLOR = "#89B4FA"
BUTTON_BG = "#45475A"
GRID_BG = "#313244"
GRID_LINE = "#45475A"
PATH_COLOR = "#F9E2AF"
SUCCESS_COLOR = "#A6E3A1"
FAIL_COLOR = "#F38BA8"

# polices d'ecriture
FONT_TITLE = ("Helvetica Neue", 18, "bold")
FONT_BOLD = ("Helvetica Neue", 11, "bold")
FONT_STATUS = ("Helvetica Neue", 11, "bold")

class ExtendedSimulation(LabyrinthSimulation):
    # initialise la simulation etendue et garde une copie de la grille pour le reset
    def __init__(self, n_rows, m_cols, grid):
        super().__init__(n_rows, m_cols, grid)
        self.original_grid_copy = [row[:] for row in grid]
        self.fire_mode_static = False 

    # remet la grille a son etat initial
    def reset_grid(self):
        self.grid = [row[:] for row in self.original_grid_copy]
        self.prisoner_pos = self.find_positions()[0]

    # modifie le calcul du feu pour permettre le mode statique dans a*
    def compute_fire_spread(self) -> List[List[int]]:
        if self.fire_mode_static:
            # si le feu est statique, on dit qu'il ne bougera pas (temps infini partout ailleurs)
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

class LabyrinthGUI:
    # initialise l'interface graphique et charge le premier niveau
    def __init__(self, root, raw_instances):
        self.root = root
        self.root.title("Simulateur Labyrinthe")
        self.root.geometry("1100x700") 
        self.root.configure(bg=BG_COLOR)
        
        self.raw_instances = raw_instances
        self.current_level_idx = 0
        self.sim = None
        
        self.running = False
        self.game_over = False
        self.move_count = 0
        self.animation_speed = 300 
        self.astar_path_moves = []
        
        self.images = self.load_images()
        self.setup_ui()
        self.load_level(0)

    # charge les images des elements du jeu
    def load_images(self):
        imgs = {}
        path = "icons/" 
        try:
            imgs['D'] = tk.PhotoImage(file=os.path.join(path, "player.png"))
            imgs['F'] = tk.PhotoImage(file=os.path.join(path, "fire.png"))
            imgs['#'] = tk.PhotoImage(file=os.path.join(path, "wall.png"))
            imgs['S'] = tk.PhotoImage(file=os.path.join(path, "exit.png"))
        except Exception:
            pass 
        return imgs

    # cree et place tous les elements visuels de la fenetre
    def setup_ui(self):
        tk.Label(self.root, text="SIMULATION LABYRINTHE", font=FONT_TITLE, bg=BG_COLOR, fg=ACCENT_COLOR, pady=5).pack(fill=tk.X)

        main = tk.Frame(self.root, bg=BG_COLOR)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # zone de dessin a gauche
        self.canvas = tk.Canvas(main, bg=GRID_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.canvas.bind("<Configure>", lambda e: self.draw_grid())

        # panneau de controle a droite
        controls = tk.Frame(main, bg=PANEL_COLOR, padx=10, pady=10)
        controls.pack(side=tk.RIGHT, fill=tk.Y)
        
        # astuce pour forcer la largeur du panneau
        tk.Frame(controls, bg=PANEL_COLOR, width=250, height=1).pack(side=tk.TOP)

        action_frame = tk.Frame(controls, bg=PANEL_COLOR)
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        tk.Button(action_frame, text="RÉINITIALISER", command=self.reset_level, bg="#E78284", fg=BG_COLOR, font=FONT_BOLD, relief=tk.FLAT, pady=5).pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(action_frame, bg=PANEL_COLOR, height=5).pack(side=tk.BOTTOM)
        self.btn_action = tk.Button(action_frame, text="DÉMARRER", command=self.on_action_click, bg=ACCENT_COLOR, fg=BG_COLOR, font=("Arial", 12, "bold"), relief=tk.FLAT, pady=8)
        self.btn_action.pack(side=tk.BOTTOM, fill=tk.X)

        top_controls = tk.Frame(controls, bg=PANEL_COLOR)
        top_controls.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # navigation entre les niveaux
        nav = tk.Frame(top_controls, bg=PANEL_COLOR)
        nav.pack(fill=tk.X, pady=(0, 10))
        self.lbl_level = tk.Label(nav, text="NIVEAU 1", font=FONT_TITLE, bg=PANEL_COLOR, fg=TEXT_COLOR)
        self.lbl_level.pack()
        
        btn_box = tk.Frame(nav, bg=PANEL_COLOR)
        btn_box.pack(fill=tk.X, pady=2)
        tk.Button(btn_box, text="< PRÉC.", command=self.prev_level, bg=BUTTON_BG, fg=TEXT_COLOR, relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_box, text="SUIV. >", command=self.next_level, bg=BUTTON_BG, fg=TEXT_COLOR, relief=tk.FLAT).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        # affichage du statut et des infos
        self.status_frame = tk.Frame(top_controls, bg=BUTTON_BG, padx=5, pady=5)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.lbl_status = tk.Label(self.status_frame, text="PRÊT", bg=BUTTON_BG, fg=TEXT_COLOR, font=FONT_STATUS, wraplength=280, justify="center")
        self.lbl_status.pack(fill=tk.X)
        
        self.lbl_moves = tk.Label(top_controls, text="Déplacements : 0", bg=PANEL_COLOR, fg=ACCENT_COLOR, font=FONT_BOLD)
        self.lbl_moves.pack(anchor="w", pady=(5, 10))

        # options de simulation
        tk.Label(top_controls, text="PARAMÈTRES", bg=PANEL_COLOR, fg=ACCENT_COLOR, font=FONT_BOLD).pack(anchor="w", pady=(5, 2))
        
        self.algo_var = tk.StringVar(value="astar")
        tk.Radiobutton(top_controls, text="A* Optimal", variable=self.algo_var, value="astar", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")
        tk.Radiobutton(top_controls, text="Naïf Simple", variable=self.algo_var, value="simple", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")

        tk.Label(top_controls, text="Feu :", bg=PANEL_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(5, 0))
        self.fire_var = tk.StringVar(value="dynamic")
        tk.Radiobutton(top_controls, text="Dynamique", variable=self.fire_var, value="dynamic", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")
        tk.Radiobutton(top_controls, text="Statique", variable=self.fire_var, value="static", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR, command=self.reset_level).pack(anchor="w")

        tk.Label(top_controls, text="Lecture :", bg=PANEL_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(5, 0))
        self.play_mode = tk.StringVar(value="auto")
        tk.Radiobutton(top_controls, text="Auto", variable=self.play_mode, value="auto", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR).pack(anchor="w")
        tk.Radiobutton(top_controls, text="Manuel", variable=self.play_mode, value="manual", bg=PANEL_COLOR, fg=TEXT_COLOR, selectcolor=PANEL_COLOR).pack(anchor="w")

    # charge un niveau specifique depuis la liste
    def load_level(self, idx):
        if not self.raw_instances: return
        self.current_level_idx = idx % len(self.raw_instances)
        n, m, grid = self.raw_instances[self.current_level_idx]
        self.sim = ExtendedSimulation(n, m, grid)
        self.lbl_level.config(text=f"NIVEAU {self.current_level_idx + 1}")
        self.reset_level()

    # passe au niveau precedent
    def prev_level(self): self.load_level(self.current_level_idx - 1)
    
    # passe au niveau suivant
    def next_level(self): self.load_level(self.current_level_idx + 1)

    # remet tout a zero pour recommencer le niveau
    def reset_level(self):
        self.running = False
        self.game_over = False
        self.move_count = 0
        if self.sim: self.sim.reset_grid()
        self.astar_path_moves = []
        
        self.update_status_display("PRÊT", BUTTON_BG, TEXT_COLOR)
        self.lbl_moves.config(text="Déplacements : 0")
        self.btn_action.config(text="DÉMARRER", bg=ACCENT_COLOR, state=tk.NORMAL)
        self.draw_grid()

    # met a jour le texte et la couleur du statut
    def update_status_display(self, text, bg_color, text_color):
        self.status_frame.config(bg=bg_color)
        self.lbl_status.config(text=text, bg=bg_color, fg=text_color)

    # gere le clic sur le bouton demarrer ou etape suivante
    def on_action_click(self):
        mode = self.play_mode.get()
        if self.game_over: return

        # si c'est le tout debut, on initialise
        if self.move_count == 0 and not self.running and not self.astar_path_moves:
            self.sim.fire_mode_static = (self.fire_var.get() == "static")
            
            if self.algo_var.get() == "astar":
                path = self.sim.solve_astar_dynamique()
                if path:
                    self.astar_path_moves = list(path) 
                    self.update_status_display("CHEMIN CALCULÉ", PATH_COLOR, BG_COLOR)
                    self.running = True
                else:
                    self.running = False
                    self.update_status_display("IMPOSSIBLE !\nAUCUN CHEMIN", FAIL_COLOR, BG_COLOR)
                    return
            else:
                self.running = True
                self.update_status_display("EN COURS...", ACCENT_COLOR, BG_COLOR)
        
        if mode == "auto":
            if self.btn_action['text'] == "PAUSE":
                self.running = False
                self.btn_action.config(text="REPRENDRE")
                self.update_status_display("PAUSE", PATH_COLOR, BG_COLOR)
            else:
                self.running = True
                self.btn_action.config(text="PAUSE", bg=PATH_COLOR)
                self.run_step_auto()
                
        elif mode == "manual":
            # petit fix pour eviter de cliquer si a* a echoue
            if self.algo_var.get() == "astar" and not self.astar_path_moves and self.move_count == 0:
                 return
            self.btn_action.config(text="ÉTAPE SUIVANTE", bg=PATH_COLOR)
            self.run_single_step()

    # boucle automatique pour l'animation
    def run_step_auto(self):
        if not self.running or self.game_over: return
        self.run_single_step()
        if not self.game_over:
            self.root.after(self.animation_speed, self.run_step_auto)

    # execute une seule etape de la simulation
    def run_single_step(self):
        if self.game_over: return

        # d'abord le feu se propage
        if self.fire_var.get() == "dynamic":
            fire_res = self.sim.update_fire_state()
            if fire_res != "OK":
                msg = "BRÛLÉ PAR LE FEU !" if fire_res == "PRISONNIER_BRULE" else "SORTIE DÉTRUITE !"
                self.end_game(False, msg)
                return

        moved = False
        algo = self.algo_var.get()

        if algo == "astar":
            # mode a* : on suit le chemin prevu
            if self.astar_path_moves:
                next_pos = self.astar_path_moves.pop(0)
                cell = self.sim.grid[next_pos[0]][next_pos[1]]
                # verification de securite
                if cell == 'F' or cell == '#':
                    self.end_game(False, "CHEMIN BLOQUÉ !")
                    return
                
                cr, cc = self.sim.prisoner_pos
                self.sim.grid[cr][cc] = '.'
                self.sim.grid[next_pos[0]][next_pos[1]] = 'D'
                self.sim.prisoner_pos = next_pos
                moved = True
                
                if not self.astar_path_moves:
                    self.end_game(True, "SORTIE ATTEINTE !")
                    
        elif algo == "simple":
            # mode naif : on calcule le coup a la volee
            if self.sim.move_prisoner():
                self.end_game(True, "SORTIE ATTEINTE !")
                moved = True
            else:
                moved = True

        if moved:
            self.move_count += 1
            self.lbl_moves.config(text=f"Déplacements : {self.move_count}")
        
        self.draw_grid()

    # gere la fin de la simulation (victoire ou defaite)
    def end_game(self, victory, msg):
        self.game_over = True
        self.running = False
        if victory:
            self.update_status_display(msg, SUCCESS_COLOR, BG_COLOR)
        else:
            self.update_status_display(msg, FAIL_COLOR, BG_COLOR)
        self.btn_action.config(text="TERMINÉ", bg=BUTTON_BG, state=tk.DISABLED)
        self.draw_grid()

    # dessine la grille et les elements sur le canevas
    def draw_grid(self):
        self.canvas.delete("all")
        if not self.sim: return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        rows, cols = self.sim.rows, self.sim.cols
        
        # calcule la taille ideale des cases
        cell_size = min(w // cols, h // rows) if rows > 0 else 20
        if cell_size < 5: cell_size = 5
        
        # centrage du labyrinthe
        ox = (w - cols * cell_size) // 2
        oy = (h - rows * cell_size) // 2

        # dessin du chemin a* en jaune
        if self.astar_path_moves and self.algo_var.get() == "astar" and not self.game_over:
            path_points = [self.sim.prisoner_pos] + self.astar_path_moves
            coords = []
            for r, c in path_points:
                x = ox + c * cell_size + cell_size // 2
                y = oy + r * cell_size + cell_size // 2
                coords.extend([x, y])
            if len(coords) >= 4:
                self.canvas.create_line(coords, fill=PATH_COLOR, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # dessin des entites (joueur, feu, murs)
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
                    # calcul precis pour que l'image tienne bien dans la case
                    target_size = cell_size - 2 
                    if target_size <= 0: target_size = 1
                    
                    factor = math.ceil(img.width() / target_size)
                    if factor < 1: factor = 1
                    
                    try:
                        final = img.subsample(factor)
                        self.keep_imgs.append(final)
                        self.canvas.create_image(x + cell_size//2, y + cell_size//2, image=final)
                    except: pass
                else:
                    # fallback couleur si image manquante
                    col = None
                    if char == '#': col = "#444"
                    elif char == 'F': col = "#E78284"
                    elif char == 'D': col = "#89DCEB"
                    elif char == 'S': col = "#A6E3A1"
                    if col:
                        self.canvas.create_rectangle(x, y, x+cell_size, y+cell_size, fill=col, outline="")

        # grillage par dessus pour faire joli
        for i in range(rows + 1):
            py = oy + i * cell_size
            self.canvas.create_line(ox, py, ox + cols * cell_size, py, fill=GRID_LINE)
        for i in range(cols + 1):
            px = ox + i * cell_size
            self.canvas.create_line(px, oy, px, rows * cell_size, fill=GRID_LINE)

# lit le fichier texte pour creer les niveaux
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

# point d'entree du programme
if __name__ == "__main__":
    file_to_load = sys.argv[1] if len(sys.argv) > 1 else "test.txt"
    if not os.path.exists(file_to_load):
        data = [(5, 5, [list("....."), list(".D.S."), list("..F.."), list("....."), list(".....")])]
    else:
        data = parse_file(file_to_load)

    root = tk.Tk()
    app = LabyrinthGUI(root, data)
    root.mainloop()