import heapq
from typing import List, Tuple

class LabyrinthSimulation:
    # initialise la simulation avec la grille et la position de depart
    def __init__(self, n_rows: int, m_cols: int, grid: List[List[str]]):
        self.rows = n_rows
        self.cols = m_cols
        self.grid = grid
        self.prisoner_pos = self.find_positions()[0]

    # repere ou se trouvent le prisonnier (D) et la sortie (S)
    def find_positions(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        prisoner = None
        exit_pos = None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'D':
                    prisoner = (r, c)
                elif self.grid[r][c] == 'S':
                    exit_pos = (r, c)
        return prisoner, exit_pos

    # propage le feu autour d'une case et verifie si quelqu'un brule
    def burn_around(self, row: int, col: int) -> str:
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        victim = None
        
        # on regarde les 4 voisins
        for r,c in directions:
            R = row + r
            C = col + c
            if 0 <= R < self.rows and 0 <= C < self.cols:
                voisin = self.grid[R][C]
                
                # si c'est le prisonnier, c'est la priorite
                if voisin == 'D':
                    victim = "PRISONNIER"
                elif voisin == 'S':
                    if victim != "PRISONNIER":
                        victim = "EXIT"
                # si c'est vide, le feu va se propager ici au prochain tour
                elif voisin == '.':
                    self.grid[R][C] = 'A'
                    
        return victim
    
    # verifie si un deplacement est possible dans une direction donnee
    def can_move_dir(self, row: int, col: int, direction: str) -> bool:
        r, c = 0, 0
        if direction == 'T': r = -1
        elif direction == 'B': r = 1
        elif direction == 'L': c = -1
        elif direction == 'R': c = 1
        else: return False
        
        R = row + r
        C = col + c
        # on verifie qu'on reste dans la grille et qu'on ne fonce pas dans un mur ou le feu
        if 0 <= R < self.rows and 0 <= C < self.cols:
            if self.grid[R][C] == '.' or self.grid[R][C] == 'S':
                return True
        return False
                
    # compte combien de mouvements sont possibles depuis une case
    def count_possible_moves(self, row: int, col: int) -> int:
        directions = ['T', 'B', 'L', 'R']
        compteur = 0
        for d in directions:   
            if self.can_move_dir(row, col, d):
                compteur += 1
        return compteur
                
    # regarde si un mouvement menant a la sortie est disponible immediatement
    def check_win_move(self, row: int, col: int) -> bool:
        if self.can_move_dir(row, col, 'T') and self.grid[row-1][col] == 'S': return True
        elif self.can_move_dir(row, col, 'B') and self.grid[row+1][col] == 'S': return True
        elif self.can_move_dir(row, col, 'R') and self.grid[row][col+1] == 'S': return True
        elif self.can_move_dir(row, col, 'L') and self.grid[row][col-1] == 'S': return True
        return False
    
    # gere le deplacement du prisonnier pour l'algorithme naif
    def move_prisoner(self) -> bool:
        pos = self.prisoner_pos
        
        # si on peut gagner tout de suite, on le fait
        if self.check_win_move(pos[0], pos[1]):
            return True
        
        # si on est bloqué, on arrete
        if self.count_possible_moves(pos[0], pos[1]) == 0:
            return False
        else:
            # sinon on cherche le mouvement qui nous rapproche le plus de la sortie
            directions = [(-1, 0, 'T'), (1, 0, 'B'), (0, -1, 'L'), (0, 1, 'R')]
            _, s = self.find_positions()
            best_dist = float('inf')
            best_move = None
            
            for r, c, d in directions:
                if self.can_move_dir(pos[0],pos[1],d):
                    newR = pos[0] + r
                    newC = pos[1] + c
                    # calcul de la distance de manhattan
                    dist = abs(newR - s[0]) + abs(newC - s[1])
                    if dist < best_dist:
                        best_dist = dist
                        best_move = (newR, newC)
            
            # on effectue le meilleur mouvement trouve
            if best_move:
                newR, newC = best_move
                self.grid[pos[0]][pos[1]] = '.'
                self.grid[newR][newC] = 'D'
                self.prisoner_pos = (newR, newC)
            return False
        return False
        
    # met a jour l'etat du feu sur toute la grille
    def update_fire_state(self) -> str:
        # d'abord on transforme les feux en attente (A) en feux reels (F)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'A':
                    self.grid[r][c] = 'F'

        status = "OK"
        # ensuite on propage le feu autour des cases en feu
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    result = self.burn_around(r, c)
                    if result == "PRISONNIER":
                        return "PRISONNIER_BRULE"
                    elif result == "EXIT":
                        status = "EXIT_BURNED"
        
        return status
    
    # calcule quand le feu arrivera sur chaque case (bfs)
    def compute_fire_spread(self) -> List[List[int]]:
        # on initialise avec infini partout sauf sur le feu actuel
        fire_times = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
        queue = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    fire_times[r][c] = 0
                    queue.append((r, c)) 
                elif self.grid[r][c] == '#':
                    fire_times[r][c] = -1 

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        # propagation largeur d'abord
        while queue:
            r, c = queue.pop(0) 
            current_time = fire_times[r][c]
            next_time = current_time + 1
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    # si la case n'est pas un mur et qu'on a trouve un chemin plus rapide pour le feu
                    if self.grid[nr][nc] != '#' and fire_times[nr][nc] > next_time:
                        fire_times[nr][nc] = next_time
                        queue.append((nr, nc))
        return fire_times
    
    # distance de manhattan pour l'heuristique a*
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # algorithme a* qui prend en compte la propagation du feu
    def solve_astar_dynamique(self) -> List[Tuple[int, int]]:
        # on pre-calcule la carte des temps de feu
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
            
            # si on a atteint la sortie, on reconstruit le chemin
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
                
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    cell_content = self.grid[nr][nc]
                    if cell_content == '#': continue

                    tentative_g_score = g_score[current] + 1
                    arrival_time = tentative_g_score 
                    
                    # condition cle : on doit arriver strictement avant le feu
                    if arrival_time < fire_times[nr][nc]:
                        if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g_score
                            f = tentative_g_score + self.heuristic(neighbor, goal)
                            f_score[neighbor] = f
                            heapq.heappush(open_set, (f, neighbor))
        return None 
    
    # lance la simulation tour par tour (mode naif)
    def run(self) -> str:
        # securite pour eviter les boucles infinies
        max_steps = self.rows * self.cols * 4 
        steps = 0
        
        while steps < max_steps:
            # on propage le feu et on verifie si on a perdu
            fire_status = self.update_fire_state()
            
            if fire_status == "PRISONNIER_BRULE":
                print(f"Simulation terminée : Le prisonnier a brûlé au tour {steps}.")
                print(self)
                return "N"
            elif fire_status == "EXIT_BURNED":
                print(f"Simulation terminée : La sortie a été détruite par le feu au tour {steps}.")
                print(self)
                return "N"
            
            # on bouge le prisonnier et on verifie si on a gagne
            if self.move_prisoner():
                print(f"Simulation terminée : Sortie atteinte au tour {steps} !")
                print(self)
                return "Y"
            
            if self.count_possible_moves(*self.prisoner_pos) == 0:
                print("Simulation terminée : Le prisonnier est coincé.")
                return "N"
            
            steps += 1
            
        print("Simulation terminée : Temps écoulé.")
        return "N"

    # permet d'afficher la grille proprement dans la console
    def __str__(self):
        res = []
        for row in self.grid:
            res.append("".join(row))
        return "\n".join(res)