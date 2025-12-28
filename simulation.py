import heapq
from typing import List, Tuple

class LabyrinthSimulation:
    def __init__(self, n_rows: int, m_cols: int, grid: List[List[str]]):
        self.rows = n_rows
        self.cols = m_cols
        self.grid = grid
        self.prisoner_pos = self.find_positions()[0]

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
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        for r,c in directions:
            R = row + r
            C = col + c
            if 0 <= R <self.rows and 0 <= C < self.cols:
                voisin = self.grid[R][C]
                if voisin == 'D' or voisin == 'S':
                    return True
                if voisin == '.':
                    self.grid[R][C] = 'A'
        return False
    
    def can_move_dir(self, row: int, col: int, direction: str) -> bool:
        r, c = 0, 0
        if direction == 'T': r = -1
        elif direction == 'B': r = 1
        elif direction == 'L': c = -1
        elif direction == 'R': c = 1
        else: return False
        
        R = row + r
        C = col + c
        if 0 <= R < self.rows and 0 <= C < self.cols:
            if self.grid[R][C] == '.' or self.grid[R][C] == 'S':
                return True
        return False
                
    def count_possible_moves(self, row: int, col: int) -> int:
        directions = ['T', 'B', 'L', 'R']
        compteur = 0
        for d in directions:   
            if self.can_move_dir(row, col, d):
                compteur += 1
        return compteur
                
    def check_win_move(self, row: int, col: int) -> bool:
        if self.can_move_dir(row, col, 'T') and self.grid[row-1][col] == 'S': return True
        elif self.can_move_dir(row, col, 'B') and self.grid[row+1][col] == 'S': return True
        elif self.can_move_dir(row, col, 'R') and self.grid[row][col+1] == 'S': return True
        elif self.can_move_dir(row, col, 'L') and self.grid[row][col-1] == 'S': return True
        return False
    
    def move_prisoner(self) -> bool:
        pos = self.prisoner_pos
        if self.check_win_move(pos[0], pos[1]):
            return True
        
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
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'A':
                    self.grid[r][c] = 'F'
        game_over = False
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 'F':
                    if self.burn_around(r,c):
                        game_over = True
        return game_over
    
    def compute_fire_spread(self) -> List[List[int]]:
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
        while queue:
            r, c = queue.pop(0) 
            current_time = fire_times[r][c]
            next_time = current_time + 1
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.grid[nr][nc] != '#' and fire_times[nr][nc] > next_time:
                        fire_times[nr][nc] = next_time
                        queue.append((nr, nc))
        return fire_times
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def solve_astar_dynamique(self) -> List[Tuple[int, int]]:
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
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    cell_content = self.grid[nr][nc]
                    if cell_content == '#': continue

                    tentative_g_score = g_score[current] + 1
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
            for r, c in path:
                if self.grid[r][c] != 'S': 
                    self.grid[r][c] = '*' 
            print(self)
            return "Y"
        else:
            print("Aucun chemin trouvé (Bloqué par les murs ou le feu).")
            return "N"

    def __str__(self):
        res = []
        for row in self.grid:
            res.append("".join(row))
        return "\n".join(res)