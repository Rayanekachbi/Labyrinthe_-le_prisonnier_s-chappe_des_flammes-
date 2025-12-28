import sys
from simulation import LabyrinthSimulation 

def parse_input_file(filename: str):
    """
    Lit le fichier et génère les instances de LabyrinthSimulation.
    """
    try:
        with open(filename, 'r') as f:
            content = f.read().split()
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{filename}' est introuvable.")
        sys.exit(1)

    iterator = iter(content)

    try:
        num_instances = int(next(iterator))
        
        for i in range(num_instances):
            n_rows = int(next(iterator))
            m_cols = int(next(iterator))
            
            grid = []
            for _ in range(n_rows):
                line_str = next(iterator)
                grid.append(list(line_str))
            
            print(f"--- Instance {i + 1} ---")
            # On crée l'objet à partir de la classe importée
            sim = LabyrinthSimulation(n_rows, m_cols, grid)
            result = sim.run()
            print(f"Résultat : {result}\n")

    except StopIteration:
        print("Erreur : Le fichier semble incomplet ou mal formaté.")

def main():
    if len(sys.argv) < 2:
        parse_input_file("test2.txt") 
    else:
        parse_input_file(sys.argv[1])

if __name__ == "__main__":
    main()