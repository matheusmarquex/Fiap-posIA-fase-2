from utils import load_locations, build_distance_matrix
from ga import genetic_algorithm
from visualize import Visualizer

import os
print("Diretório atual:", os.getcwd())

def main():
    csv_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sample_locations.csv'))
    locations = load_locations(csv_path)

    distance_matrix = build_distance_matrix(locations)

    visualizer = Visualizer(locations)

    def callback(gen, route, dist):
        visualizer.draw(gen, route, dist)

    best_route, best_distance = genetic_algorithm(
        distance_matrix,
        population_size=50,
        generations=300,
        mutation_rate=0.1,
        callback=callback
    )

    print("\nMelhor rota encontrada:")
    for idx in best_route:
        print(f" - {locations[idx][0]} ({locations[idx][1]}, {locations[idx][2]})")

    print(f"\nDistância total: {best_distance:.2f}")


if __name__ == "__main__":
    main()
