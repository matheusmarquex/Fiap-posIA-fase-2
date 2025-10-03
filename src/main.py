# src/main_vrp_sequential.py
from utils import load_locations, build_distance_matrix
from ga import genetic_algorithm  # GA TSP (com callback)
from visualize import Visualizer
import time

import os
print("Diretório atual:", os.getcwd())

def run_ga_for_group(group_id, locations_group, generations=500, population_size=50, mutation_rate=0.1):
    """
    Roda o GA TSP para um grupo (hospital + até N clientes).
    locations_group: lista de tuples (nome, lat, lon, produto, prioridade)
    Retorna best_route (lista de indices) e best_distance (float).
    """
    distance_matrix = build_distance_matrix(locations_group)
    visualizer = Visualizer(locations_group, width=900, height=700)

    # callback que o GA chamará a cada geração
    def callback(gen, routes, dist):
        # flatten routes para visualização contínua, fechando cada rota no hospital
        flat_route = []
        for route in routes:
            if route:
                flat_route.append(0)       # hospital início
                flat_route.extend(route)
                flat_route.append(0)       # hospital fim
        visualizer.draw(gen, flat_route, dist)

    # roda o GA
    best_route, best_distance = genetic_algorithm(
        distance_matrix,
        population_size=population_size,
        generations=generations,
        mutation_rate=mutation_rate,
        callback=callback
    )

    # visualização final
    final_route = []
    for route in split_routes(best_route, num_trucks=5, max_per_truck=12):
        if route:
            final_route.append(0)
            final_route.extend(route)
            final_route.append(0)
    visualizer.draw(generations, final_route, best_distance)
    time.sleep(1.5)

    return best_route, best_distance


def main():
    all_locations = load_locations("data/clientes_pedidos.csv")  # espera (cliente, lat, lon, produto, prioridade)

    # parâmetros
    num_trucks = 5
    max_per_truck = 12  # cada caminhão atende até 12 clientes
    ga_generations = 500
    ga_population = 60
    ga_mutation = 0.1

    # dividir clientes em grupos contíguos
    groups = []
    for i in range(num_trucks):
        start = 1 + i * max_per_truck
        end = start + max_per_truck
        group = [all_locations[0]] + all_locations[start:end]  # hospital incluído
        if len(group) > 1:
            groups.append((i + 1, group))  # (truck_id, locations_list)

    print(f"Preparado para otimizar {len(groups)} caminhões (cada um até {max_per_truck} clientes).")

    results = []
    for truck_id, locs in groups:
        print(f"\n--- Otimizando Caminhão {truck_id} (clientes: {len(locs)-1}) — {ga_generations} gerações ---")
        best_route, best_distance = run_ga_for_group(
            truck_id,
            locs,
            generations=ga_generations,
            population_size=ga_population,
            mutation_rate=ga_mutation
        )

        # garante início/fim no hospital
        route_indices = [0] + best_route + [0]

        # converte indices em nomes/infos
        route_names = [f"{locs[idx][0]} [{locs[idx][3]} | {locs[idx][4]}]" for idx in route_indices]

        print(f"\nResultado Caminhão {truck_id}:")
        print(" -> ".join(route_names))
        print(f"Distância total (unidade relativa): {best_distance:.2f}")

        results.append((truck_id, best_route, best_distance, locs))

    print("\n=== Todas as otimizações finalizadas ===")
    for truck_id, best_route, best_distance, locs in results:
        route_indices = [0] + best_route + [0]
        print(f"\nCaminhão {truck_id} — Distância: {best_distance:.2f}")
        print("Rota:")
        for idx in route_indices:
            name, lat, lon, produto, prioridade = locs[idx]
            print(f" - {name} | {produto} | {prioridade} ({lat:.6f}, {lon:.6f})")


def split_routes(chromosome, num_trucks=5, max_per_truck=12):
    """
    Divide cromossomo em sub-rotas (cada caminhão).
    Útil para visualização.
    """
    routes = [[] for _ in range(num_trucks)]
    truck = 0
    for client in chromosome:
        if len(routes[truck]) >= max_per_truck:
            truck = (truck + 1) % num_trucks
        routes[truck].append(client)
    return routes


if __name__ == "__main__":
    main()
