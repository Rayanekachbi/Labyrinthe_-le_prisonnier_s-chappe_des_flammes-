import random
import sys

def create_maze(width, height):
    # On force des dimensions impaires pour avoir des murs "propres" autour
    if width % 2 == 0: width += 1
    if height % 2 == 0: height += 1
    
    # 1. Remplir tout de murs (#)
    maze = [['#' for _ in range(width)] for _ in range(height)]
    
    # 2. Algorithme de creusement (DFS itératif)
    # On commence à (1,1)
    stack = [(1, 1)]
    maze[1][1] = '.'
    
    while stack:
        x, y = stack[-1]
        neighbors = []
        
        # On cherche des voisins à une distance de 2 cases (pour sauter le mur)
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            # Si le voisin est dans la grille et est encore un mur
            if 0 < nx < height and 0 < ny < width and maze[nx][ny] == '#':
                neighbors.append((nx, ny, dx, dy))
        
        if neighbors:
            # On choisit un voisin au hasard
            nx, ny, dx, dy = random.choice(neighbors)
            # On casse le mur entre les deux
            maze[x + dx // 2][y + dy // 2] = '.'
            # On marque la nouvelle case
            maze[nx][ny] = '.'
            stack.append((nx, ny))
        else:
            stack.pop()
            
    # 3. Placer D (Départ), S (Sortie), F (Feu)
    # Départ en haut à gauche
    maze[1][1] = 'D'
    
    # Sortie en bas à droite (on remonte si c'est un mur)
    sx, sy = height - 2, width - 2
    while maze[sx][sy] == '#':
        sx -= 1
    maze[sx][sy] = 'S'
    
    # Feu : On le place au hasard sur une case vide, mais loin du départ
    placed_fire = False
    while not placed_fire:
        fx, fy = random.randint(1, height-2), random.randint(1, width-2)
        # On vérifie que ce n'est pas un mur, ni D, ni S, et assez loin de D
        if maze[fx][fy] == '.' and (fx > 5 or fy > 5):
            maze[fx][fy] = 'F'
            placed_fire = True
            
    return maze

def save_mazes_to_file(filename):
    # On définit 3 niveaux : (Lignes, Colonnes)
    # Dimensions impaires recommandées pour cet algo
    levels = [
        (15, 15),  # Niveau 1 : Petit
        (25, 25),  # Niveau 2 : Moyen
        (41, 61)   # Niveau 3 : Grand (Rectangulaire comme un écran)
    ]
    
    try:
        with open(filename, 'w') as f:
            f.write(f"{len(levels)}\n") # Nombre d'instances
            
            for rows, cols in levels:
                maze = create_maze(cols, rows) # Attention inversé x/y
                
                # Écriture des dimensions
                f.write(f"{rows} {cols}\n")
                
                # Écriture de la grille
                for row in maze:
                    f.write("".join(row) + "\n")
                    
        print(f"Succès ! Fichier '{filename}' généré avec 3 labyrinthes parfaits.")
        print("Tu peux maintenant lancer ton jeu : python main.py test3.txt")
        
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    save_mazes_to_file("test3.txt")