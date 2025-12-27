import sys
from typing import List, Tuple
import heapq 

class LabyrinthSimulation:
    def __init__(self, n_rows: int, m_cols: int, grid: List[List[str]]):
        self.rows = n_rows
        self.cols = m_cols
        self.grid = grid
        self.prisoner_pos = self.find_positions()[0] # On trouve direct la position

    def find_positions(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """ Trouve D et S au démarrage """
        prisoner = None
        exit_pos = None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'D':
                    prisoner = (r, c)
                elif self.grid[r][c] == 'S':
                    exit_pos = (r, c)
        return prisoner, exit_pos

    def burn_around(self, row: int, col: int) -> bool:
        #ici les 'F' (vieux feu) transforment les cases vides . voisines en 'A'
        #puis avec update_fire_state(self) les 'A' deviennent des feux 'F'
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        for r,c in directions:
            R = row + r
            C = col + c
            # on s'asure que les cases sont toutes dans la grille 
            if 0 <= R <self.rows and 0 <= C < self.cols:
                voisin = self.grid[R][C]
                #si le prisonnier ou la sortie sont brulés on retourne vrai
                if voisin == 'D' or voisin == 'S':
                    return True
                if voisin == '.':
                    self.grid[R][C] = 'A'
        
        return False
    
    
    def can_move_dir(self, row: int, col: int, direction: str) -> bool:
        r, c = 0, 0
        
        if direction == 'T':
            r = -1
        elif direction == 'B':
            r = 1
        elif direction == 'L':
            c = -1
        elif direction == 'R':
            c = 1
        else:
            return False
        R = row + r
        C = col + c
        
        if 0 <= R < self.rows and 0 <= C < self.cols:
            if self.grid[R][C] == '.' or self.grid[R][C] == 'S':
                return True
        return False
                
    def count_possible_moves(self, row: int, col: int) -> int:
        directions = ['T', 'B', 'L', 'R']
        comteur = 0
        for d in directions:   
            if self.can_move_dir(row, col, d):
                comteur += 1
        return comteur
                
    def check_win_move(self, row: int, col: int) -> bool:
        if self.can_move_dir(row, col, 'T') and self.grid[row-1][col] == 'S':
            return True
        elif self.can_move_dir(row, col, 'B') and self.grid[row+1][col] == 'S':
            return True
        elif self.can_move_dir(row, col, 'R') and self.grid[row][col+1] == 'S':
            return True
        elif self.can_move_dir(row, col, 'L') and self.grid[row][col-1] == 'S':
            return True
        return False
    
    def move_prisoner(self) -> bool:
        # on regarde d'aboord si la sortie est a cote
        pos = self.prisoner_pos
        if self.check_win_move(pos[0], pos[1]):
            #est-ce que le prisionnier doit etre deplacé a S ?
            return True
        #on verifie par la suite si tout les chemins adjacents sont bloqués
        if self.count_possible_moves(pos[0], pos[1]) == 0:
            return False
        else:
            directions = [(-1, 0, 'T'), (1, 0, 'B'), (0, -1, 'L'), (0, 1, 'R')]
            _, s = self.find_positions()
            best_dist = float('inf')
            best_move = None
            for r, c, d in directions:
                if self.can_move_dir(pos[0],pos[1],d):
                    newR = pos[0] + r
                    newC = pos[1] + c
                    # Distance de Manhattan : |x1-x2| + |y1-y2|
                    dist = abs(newR - s[0]) + abs(newC - s[1])
                    if dist<best_dist:
                        best_dist = dist
                        best_move = (newR, newC)
            if best_move:
                newR, newC = best_move
                self.grid[pos[0]][pos[1]] = '.'
                self.grid[newR][newC] = 'D'
                
                self.prisoner_pos = (newR, newC)
            return False
        return False
    
    
        
    def update_fire_state(self) -> bool:
        #on trouve toutes les cases qui s'appretent à bruler et on les met en F
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'A':
                    self.grid[r][c] = 'F'
        game_over = False
        #avec self.burn_around(r,c) on verifie si le prisonnier ou la sortie sont brulés
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    if self.burn_around(r,c):
                        game_over = True
        return game_over
    
    def compute_fire_spread(self) -> List[List[int]]:
        """
        Calcule pour chaque case le temps (tour) auquel le feu arrivera.
        Retourne une grille d'entiers (INF si le feu n'atteint jamais la case).
        """
        fire_times = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
        queue = []

        # On initialise avec tous les feux de départ
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    fire_times[r][c] = 0
                    queue.append((r, c)) 
                elif self.grid[r][c] == '#':
                    fire_times[r][c] = -1 

        # BFS pour propager les temps
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while queue:
            r, c = queue.pop(0) 
            
            current_time = fire_times[r][c]
            next_time = current_time + 1

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    # Si ce n'est pas un mur et qu'on n'a pas déjà trouvé un chemin plus court pour le feu
                    if self.grid[nr][nc] != '#' and fire_times[nr][nc] > next_time:
                        fire_times[nr][nc] = next_time
                        queue.append((nr, nc))
        
        return fire_times
    
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        # Distance de Manhattan : |x1 - x2| + |y1 - y2|
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def solve_astar(self) -> List[Tuple[int, int]]:
        """
        Trouve le chemin le plus court entre D et S en évitant les murs et le feu.
        Retourne la liste des cases du chemin [(r,c), (r,c)...] ou None.
        """
        start = self.prisoner_pos
        _, s_pos = self.find_positions()
        goal = s_pos

        # File de priorité : contient (f_score, (row, col))
        # On commence par le départ
        open_set = []
        heapq.heappush(open_set, (0, start))

        # Pour reconstruire le chemin à la fin : came_from[fils] = pere
        came_from = {} 
        # Coût du départ jusqu'à ici (tout est initialisé à l'infini sauf le départ 0). 
        g_score = {start: 0} 

        # Coût total estimé (g + h). 
        # Initialisé avec l'heuristique du départ
        f_score = {start: self.heuristic(start, goal)}

        # Boucle principale
        while open_set:
            # On prend la case avec le plus petit f_score
            current_f, current = heapq.heappop(open_set)

            # si on a trouvé la sortie :
            if current == goal:
                # On reconstruit le chemin en remontant de la fin vers le début
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            # sinon on explore les voisins
            r, c = current
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                neighbor = (r + dr, c + dc)
                if 0 <= neighbor[0] < self.rows and 0 <= neighbor[1] < self.cols:
                    
                    cell_content = self.grid[neighbor[0]][neighbor[1]]
                    # si un obstacle est touché on passe a la prochaine itération de la boucle
                    if cell_content == '#' or cell_content == 'F' or cell_content == 'A':
                        continue

                    # Le coût pour aller à un voisin est de 1 (+ le coût pour arriver ici)
                    tentative_g_score = g_score[current] + 1

                    # Si ce chemin est meilleur que celui qu'on connaissait pour atteindre ce voisin
                    # (ou si on ne connaissait pas encore ce voisin)
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        # On enregistre ce nouveau meilleur chemin
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f = tentative_g_score + self.heuristic(neighbor, goal)
                        f_score[neighbor] = f
                        
                        # On l'ajoute à la liste des cases à explorer
                        # si elle y est déjà avec un coût plus élevé on l'ajoute quand même
                        # la version la moins chère sortira en premier
                        heapq.heappush(open_set, (f, neighbor))
        return None 
    
    def solve_astar_dynamique(self) -> List[Tuple[int, int]]:
        """
        Trouve le chemin le plus court entre D et S en évitant les murs et le feu.
        Retourne la liste des cases du chemin [(r,c), (r,c)...] ou None.
        """
        fire_times = self.compute_fire_spread()
        
        start = self.prisoner_pos
        _, s_pos = self.find_positions()
        goal = s_pos

        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {} 
        g_score = {start: 0} 
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            r, c = current
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                neighbor = (nr, nc)
                
                # Vérification des limites de la grille
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    
                    cell_content = self.grid[nr][nc]
                    
                    # OBSTACLES STATIQUES
                    if cell_content == '#':
                        continue

                    # TEMPS ET FEU
                    tentative_g_score = g_score[current] + 1
                    # Le temps d'arrivée est égal au nombre de pas
                    arrival_time = tentative_g_score 
                    
                    if arrival_time < fire_times[nr][nc]:
                        
                        if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g_score
                            f = tentative_g_score + self.heuristic(neighbor, goal)
                            f_score[neighbor] = f
                            heapq.heappush(open_set, (f, neighbor))
                            
        return None 
    
    def run(self) -> str:
        print("--- Recherche de chemin avec A* ---")
        path = self.solve_astar_dynamique()
        
        if path:
            print(f"Chemin trouvé en {len(path)} étapes !")
            # On dessine le chemin sur la grille pour voir
            for r, c in path:
                if self.grid[r][c] != 'S': # On ne veut pas écraser le S
                    self.grid[r][c] = '*' # On marque le chemin avec des étoiles
            print(self)
            return "Y"
        else:
            print("Aucun chemin trouvé (Bloqué par les murs ou le feu).")
            return "N"
        '''
        turn = 0
        max_turns = self.rows * self.cols
        
        print("--- État initial ---")
        print(self)

        while turn < max_turns:
            turn += 1
            print(f"\n--- Tour {turn} ---")

            # 1. PROPAGATION DU FEU
            feu_gagne = self.update_fire_state()
            if feu_gagne:
                print(self) # On affiche le désastre
                print("Le feu a atteint le prisonnier ou la sortie !")
                return "N"

            # 2. DÉPLACEMENT DU PRISONNIER
            prisonnier_gagne = self.move_prisoner()
            
            # On affiche la carte après les deux mouvements
            print(self)

            if prisonnier_gagne:
                return "Y"
                
        return "N"
        '''

    def __str__(self):
        """
        Méthode magique pour l'affichage.
        Permet de faire print(simulation) et d'avoir un joli rendu.
        """
        res = []
        for row in self.grid:
            res.append("".join(row))
        return "\n".join(res)

# --- Partie Gestion de Fichiers ---

def parse_input_file(filename: str):
    """
    Lit le fichier et génère les instances de LabyrinthSimulation.
    """
    try:
        with open(filename, 'r') as f:
            # On lit tout le contenu et on sépare par espaces/sauts de ligne
            # Cela crée une liste de "mots" : ['2', '3', '4', '...D', ...]
            content = f.read().split()
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{filename}' est introuvable.")
        sys.exit(1)

    # On crée un itérateur pour consommer les données une par une
    iterator = iter(content)

    try:
        # 1. Lire le nombre d'instances (T)
        num_instances = int(next(iterator))
        
        for i in range(num_instances):
            # 2. Lire N et M pour l'instance courante
            n_rows = int(next(iterator))
            m_cols = int(next(iterator))
            
            # 3. Lire la grille
            grid = []
            for _ in range(n_rows):
                line_str = next(iterator)
                # On transforme la chaîne "F..D" en liste ['F', '.', '.', 'D']
                # pour pouvoir la modifier case par case si besoin
                grid.append(list(line_str))
            
            # 4. Créer l'objet et lancer
            print(f"--- Instance {i + 1} ---")
            sim = LabyrinthSimulation(n_rows, m_cols, grid)
            result = sim.run()
            print(f"Résultat : {result}\n")

    except StopIteration:
        print("Erreur : Le fichier semble incomplet ou mal formaté.")

def main():
    # Vérifie si l'utilisateur a donné un argument (le nom du fichier)
    if len(sys.argv) < 2:
        print("Usage: python mon_script.py test.txt")
        # Pour tester facilement dans ton IDE sans ligne de commande, 
        # tu peux décommenter la ligne ci-dessous et mettre un nom de fichier test :
        #parse_input_file("test.txt") 
    else:
        parse_input_file(sys.argv[1])

if __name__ == "__main__":
    main()