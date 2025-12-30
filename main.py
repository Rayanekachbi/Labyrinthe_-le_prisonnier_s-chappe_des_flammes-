import sys
from simulation import LabyrinthSimulation 

# lit le fichier d'entree et lance la simulation pour chaque niveau trouve
def parse_input_file(filename: str, use_astar: bool):
    try:
        # on charge tout le contenu du fichier en memoire
        with open(filename, 'r') as f:
            content = f.read().split()
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{filename}' est introuvable.")
        sys.exit(1)

    # on utilise un iterateur pour lire les valeurs une par une facilement
    iterator = iter(content)

    try:
        num_instances = int(next(iterator))
        
        # boucle sur chaque instance de labyrinthe presente dans le fichier
        for i in range(num_instances):
            n_rows = int(next(iterator))
            m_cols = int(next(iterator))
            
            grid = []
            for _ in range(n_rows):
                line_str = next(iterator)
                grid.append(list(line_str))
            
            print(f"\n--- Instance {i + 1} ---")
            
            # on initialise la simulation avec la grille recuperee
            sim = LabyrinthSimulation(n_rows, m_cols, grid)
            
            if use_astar:
                # si on a choisi a*, on cherche le chemin optimal directement
                print("Mode : A* Optimal")
                path = sim.solve_astar_dynamique()
                
                if path:
                    print(f"Résultat : SUCCÈS - Sortie atteinte en {len(path)} étapes.")
                else:
                    print("Résultat : ÉCHEC - Aucun chemin trouvé ou bloqué par le feu.")
            else:
                # sinon on lance le mode naif qui joue tour par tour
                print("Mode : Naïf Simple")
                result = sim.run()
                print(f"Résultat : {result}")

    except StopIteration:
        print("Erreur : Le fichier semble incomplet ou mal formaté.")

# fonction principale qui gere les arguments et le menu de choix
def main():
    # si aucun fichier n'est donne en argument, on prend test2.txt par defaut
    if len(sys.argv) < 2:
        filename = "test2.txt"
    else:
        filename = sys.argv[1]

    print(f"Fichier chargé : {filename}")
    print("Choisissez l'algorithme de résolution :")
    print("1. Algorithme Naïf Simple")
    print("2. Algorithme A* Optimal")
    
    # on recupere le choix de l'utilisateur
    choix = input("Votre choix : ").strip()

    if choix == '2':
        use_astar = True
    else:
        use_astar = False

    # on lance le traitement du fichier avec l'option choisie
    parse_input_file(filename, use_astar)

if __name__ == "__main__":
    main()