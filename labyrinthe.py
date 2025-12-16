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
    def burn_around(self, row: int, col: int) -> bool: pass
    def can_move_dir(self, row: int, col: int, direction: str) -> bool: pass
    def count_possible_moves(self, row: int, col: int) -> int: pass
    def check_win_move(self, row: int, col: int) -> bool: pass
    def move_prisoner(self) -> bool: pass
    def update_fire_state(self) -> bool: pass
    
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
        print("Usage: python mon_script.py <nom_du_fichier>")
        # Pour tester facilement dans ton IDE sans ligne de commande, 
        # tu peux décommenter la ligne ci-dessous et mettre un nom de fichier test :
        parse_input_file("test_data.txt") 
    else:
        parse_input_file(sys.argv[1])

if __name__ == "__main__":
    main()