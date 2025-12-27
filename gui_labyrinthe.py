import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import sys
from typing import List, Tuple

# --- TA CLASSE DE SIMULATION (Adaptée pour le GUI) ---
class LabyrinthSimulation:
    def __init__(self, n_rows: int, m_cols: int, grid: List[List[str]]):
        self.rows = n_rows
        self.cols = m_cols
        # On fait une copie profonde de la grille pour ne pas casser l'original si on restart
        self.grid = [row[:] for row in grid] 
        self.prisoner_pos = self.find_positions()[0]
        self.path_to_draw = [] # Pour stocker le chemin A* en mode statique

    def find_positions(self):
        p, s = None, None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'D': p = (r, c)
                elif self.grid[r][c] == 'S': s = (r, c)
        return p, s

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # --- TON ALGO A* STATIQUE ---
    def solve_astar_static(self):
        start = self.prisoner_pos
        _, goal = self.find_positions()
        
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
                    if self.grid[nr][nc] in ['#', 'F', 'A']: continue
                    
                    tentative_g = g_score[current] + 1
                    neighbor = (nr, nc)
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + self.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f, neighbor))
        return None

    # --- MÉTHODES POUR LE MODE DYNAMIQUE (SIMULATION) ---
    def burn_around(self, r, c):
        # Logique simplifiée pour l'exemple
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] == '.': self.grid[nr][nc] = 'A'
                elif self.grid[nr][nc] in ['D', 'S']: return True
        return False

    def update_fire_state(self):
        # 1. A -> F
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'A': self.grid[r][c] = 'F'
        # 2. Propagation
        game_over = False
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    if self.burn_around(r, c): game_over = True
        return game_over

    def move_prisoner_naive(self):
        # Ta logique naïve (déplacement vers sortie)
        r, c = self.prisoner_pos
        _, (er, ec) = self.find_positions()
        
        # Victoire ?
        if abs(r-er) + abs(c-ec) == 1: return True 

        # Déplacement simple (Glouton)
        best_move = None
        min_dist = float('inf')
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] in ['.', 'S']:
                    d = abs(nr-er) + abs(nc-ec)
                    if d < min_dist:
                        min_dist = d
                        best_move = (nr, nc)
        
        if best_move:
            self.grid[r][c] = '.'
            self.grid[best_move[0]][best_move[1]] = 'D'
            self.prisoner_pos = best_move
        return False


# --- L'INTERFACE GRAPHIQUE ---

class LabyrinthGUI:
    def __init__(self, root, raw_instances):
        self.root = root
        self.root.title("Simulateur Labyrinthe - Projet Étudiant")
        self.raw_instances = raw_instances # Données brutes chargées du fichier
        self.sim = None
        self.running = False
        self.animation_speed = 300 # ms

        # --- 1. Panneau de Contrôle (Gauche) ---
        control_frame = tk.Frame(root, padx=10, pady=10, bg="#f0f0f0")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Choix du niveau
        tk.Label(control_frame, text="Choisir le Niveau :", bg="#f0f0f0").pack(pady=5)
        self.level_var = tk.IntVar(value=1)
        self.level_spin = tk.Spinbox(control_frame, from_=1, to=len(raw_instances), 
                                     textvariable=self.level_var, command=self.load_level, width=5)
        self.level_spin.pack(pady=5)

        # Choix du mode
        tk.Label(control_frame, text="Mode de Résolution :", bg="#f0f0f0").pack(pady=(15, 5))
        self.mode_var = tk.StringVar(value="static")
        tk.Radiobutton(control_frame, text="Statique (A*)", variable=self.mode_var, 
                       value="static", command=self.load_level, bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(control_frame, text="Dynamique (Simu)", variable=self.mode_var, 
                       value="dynamic", command=self.load_level, bg="#f0f0f0").pack(anchor="w")

        # Boutons
        tk.Button(control_frame, text="🔄 Réinitialiser", command=self.load_level).pack(pady=(20, 5), fill=tk.X)
        self.btn_start = tk.Button(control_frame, text="▶️ Lancer", command=self.toggle_run, bg="#dddddd")
        self.btn_start.pack(pady=5, fill=tk.X)

        # Légende
        self.create_legend(control_frame)

        # --- 2. Zone de Dessin (Droite) ---
        self.canvas = tk.Canvas(root, width=600, height=600, bg="white")
        self.canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Charger le premier niveau au démarrage
        self.load_level()

    def create_legend(self, parent):
        leg_frame = tk.LabelFrame(parent, text="Légende", bg="#f0f0f0", padx=5, pady=5)
        leg_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        items = [("D", "blue", "Prisonnier"), ("S", "green", "Sortie"), 
                 ("F", "red", "Feu"), ("#", "black", "Mur"), (".", "white", "Sol")]
        
        for char, color, desc in items:
            row = tk.Frame(leg_frame, bg="#f0f0f0")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="  ", bg=color, width=2, relief="solid").pack(side=tk.LEFT)
            tk.Label(row, text=f" : {desc}", bg="#f0f0f0").pack(side=tk.LEFT)

    def load_level(self):
        """ Charge l'instance sélectionnée et réinitialise tout """
        self.running = False
        self.btn_start.config(text="▶️ Lancer")
        
        # Récupérer les données
        idx = self.level_var.get() - 1
        n, m, grid_data = self.raw_instances[idx]
        
        # Créer la simulation
        self.sim = LabyrinthSimulation(n, m, grid_data)
        
        # Dessiner l'état initial
        self.draw_grid()

    def draw_grid(self):
        """ Dessine la grille actuelle sur le Canvas """
        self.canvas.delete("all")
        
        # Calcul taille des cases (auto-adaptatif)
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        # Sécurité si la fenêtre n'est pas encore affichée
        if c_width < 50: c_width, c_height = 600, 600
        
        cell_w = c_width / self.sim.cols
        cell_h = c_height / self.sim.rows
        
        colors = {
            '#': 'black', '.': 'white', 'S': '#00FF00', 
            'D': '#3333FF', 'F': '#FF3300', 'A': '#FF9933', 'L': 'gray'
        }

        for r in range(self.sim.rows):
            for c in range(self.sim.cols):
                char = self.sim.grid[r][c]
                x1 = c * cell_w
                y1 = r * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                
                # Couleur de base
                color = colors.get(char, 'white')
                
                # Si mode statique et chemin A* trouvé, on colorie le chemin
                if self.mode_var.get() == "static" and (r, c) in self.sim.path_to_draw:
                    if char == '.': color = "#FFFF99" # Jaune clair pour le chemin

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
                
                # Afficher les lettres pour plus de clarté
                if char in ['D', 'S', 'F']:
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=char, fill="white" if char in ['#','D','F'] else "black")

    def toggle_run(self):
        if not self.running:
            self.running = True
            self.btn_start.config(text="⏸️ Pause")
            
            if self.mode_var.get() == "static":
                self.run_static_animation()
            else:
                self.run_dynamic_step()
        else:
            self.running = False
            self.btn_start.config(text="▶️ Reprendre")

    def run_static_animation(self):
        """ Lance A* et affiche le résultat """
        path = self.sim.solve_astar_static()
        if path:
            self.sim.path_to_draw = path
            self.draw_grid()
            messagebox.showinfo("Résultat", f"Chemin trouvé en {len(path)} étapes !")
        else:
            messagebox.showwarning("Résultat", "Aucun chemin trouvé (bloqué par murs ou feu statique).")
        self.running = False
        self.btn_start.config(text="▶️ Lancer")

    def run_dynamic_step(self):
        """ Exécute un tour de simulation """
        if not self.running: return

        # 1. Feu
        game_over = self.sim.update_fire_state()
        if game_over:
            self.draw_grid()
            messagebox.showerror("Game Over", "Le feu a gagné !")
            self.running = False
            self.btn_start.config(text="▶️ Lancer")
            return

        # 2. Prisonnier
        victoire = self.sim.move_prisoner_naive()
        self.draw_grid()

        if victoire:
            messagebox.showinfo("Victoire", "Le prisonnier s'est échappé !")
            self.running = False
            self.btn_start.config(text="▶️ Lancer")
            return

        # Boucle (prochaine frame dans X ms)
        self.root.after(self.animation_speed, self.run_dynamic_step)


# --- LECTURE DU FICHIER (PARSER) ---
def parse_file(filename):
    instances = []
    try:
        with open(filename, 'r') as f:
            content = f.read().split()
        iterator = iter(content)
        num_instances = int(next(iterator))
        for _ in range(num_instances):
            r = int(next(iterator))
            c = int(next(iterator))
            grid = []
            for _ in range(r):
                grid.append(list(next(iterator)))
            instances.append((r, c, grid))
    except Exception as e:
        print(f"Erreur lecture: {e}")
        return []
    return instances

# --- MAIN ---
if __name__ == "__main__":
    # Charge ton fichier texte ici
    # Tu peux créer un fichier 'data.txt' avec tes labyrinthes
    data = parse_file("test.txt") 
    
    if not data:
        print("Aucune donnée chargée. Vérifiez 'test.txt'.")
        # Données factices pour tester si pas de fichier
        data = [(5, 5, [list("....."), list("F.D.S"), list("....."), list("....."), list(".....")])]

    root = tk.Tk()
    # On force une taille min
    root.geometry("900x600") 
    app = LabyrinthGUI(root, data)
    root.mainloop()