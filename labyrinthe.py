import sys
from typing import List, Tuple

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

    # --- Méthodes de logique (à compléter par toi plus tard) ---
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
        for r in self.rows:
            for c in self.cols:
                if self.grid[r][c] == 'A':
                    self.grid[r][c] = 'F'
        game_over = False
        #avec self.burn_around(r,c) on verifie si le prisonnier ou la sortie sont brulés
        for r in self.rows:
            for c in self.cols:
                if self.grid[r][c] == 'F':
                    if self.burn_around(r,c):
                        game_over = True
        return game_over
    
    def run(self) -> str:
        """
        Pour l'instant, on fait juste un test d'affichage.
        Plus tard, tu mettras ici ta boucle A* ou la simulation.
        """
        # Exemple de logique temporaire
        print(f"Lancement de la simulation sur une grille {self.rows}x{self.cols}")
        print(self) # Affiche la carte grâce à __str__
        return "Y" # Valeur par défaut pour tester

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