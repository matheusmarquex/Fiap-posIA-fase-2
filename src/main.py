# src/main.py (mostrar apenas as partes que mudam)
from utils import load_locations, build_distance_matrix, summarize_route
from ga import genetic_algorithm, split_routes
from visualize import Visualizer
from llm import make_llm, generate_driver_instructions, generate_daily_report, answer_question
import time
import os

def run_ga_for_group(group_id, locations_group, generations=500, population_size=50, mutation_rate=0.1):
    distance_matrix = build_distance_matrix(locations_group)
    visualizer = Visualizer(locations_group, width=900, height=700)

    def callback(gen, routes, dist):
        flat_route = []
        for route in routes:
            if route:
                flat_route.append(0)
                flat_route.extend(route)
                flat_route.append(0)
        visualizer.draw(gen, flat_route, dist)

    best_route, best_distance = genetic_algorithm(
        distance_matrix,
        population_size=population_size,
        generations=generations,
        mutation_rate=mutation_rate,
        callback=callback
    )

    # desenha rota final e segura a tela
    final_route = []
    for route in split_routes(best_route, num_trucks=5, max_per_truck=12):
        if route:
            final_route.append(0)
            final_route.extend(route)
            final_route.append(0)
    visualizer.draw(generations, final_route, best_distance,
                    overlay=f"Caminhão {group_id}\nDistância: {best_distance:.2f}")
    return best_route, best_distance, visualizer


def main():
    all_locations = load_locations("data/clientes_pedidos.csv")

    num_trucks = 5
    max_per_truck = 12
    ga_generations = 500
    ga_population = 60
    ga_mutation = 0.1

    constraints = {
        "num_trucks": num_trucks,
        "max_per_truck": max_per_truck,
        "max_distance_km": 120.0,
    }

    groups = []
    for i in range(num_trucks):
        start = 1 + i * max_per_truck
        end = start + max_per_truck
        group = [all_locations[0]] + all_locations[start:end]
        if len(group) > 1:
            groups.append((i + 1, group))

    results = []
    llm = make_llm()

    for truck_id, locs in groups:
        print(f"\n--- Otimizando Caminhão {truck_id} (clientes: {len(locs)-1}) — {ga_generations} gerações ---")
        best_route, best_distance, viz = run_ga_for_group(
            truck_id, locs,
            generations=ga_generations,
            population_size=ga_population,
            mutation_rate=ga_mutation
        )

        route_indices = [0] + best_route + [0]
        route_names = [f"{locs[idx][0]} [{locs[idx][3]} | {locs[idx][4]}]" for idx in route_indices]
        stops, high, low = summarize_route(route_indices, locs)

        # --- UI fica pausada aqui até o usuário apertar ENTER ---
        viz.hold_until_enter(
            message=f"Caminhão {truck_id}\n"
                    f"Distância: {best_distance:.2f}\n"
                    f"Paradas: {stops}  (Alta={high}, Baixa={low})\n\n"
                    f"Pressione ENTER para gerar instruções do motorista..."
        )

        # após ENTER, gera texto humanizado para ESTE caminhão
        text = generate_driver_instructions(
            llm=llm,
            truck_id=truck_id,
            route_indices=route_indices,
            locs=locs,
            constraints=constraints,
            distance=best_distance,
        )
        print(f"\n--- INSTRUÇÕES — Caminhão {truck_id} ---\n{text}\n")

        results.append({
            "truck_id": truck_id,
            "best_route": best_route,
            "distance": best_distance,
            "locs": locs,
            "route_indices": route_indices,
            "route_names": route_names,
            "stops": stops,
            "high_priority": high,
            "low_priority": low,
        })

    # fim: relatório diário consolidado
    routes_summary = [{
        "truck_id": r["truck_id"],
        "distance": r["distance"],
        "stops": r["stops"],
        "high_priority": r["high_priority"],
        "low_priority": r["low_priority"],
        "route_names": r["route_names"],
    } for r in results]

    print("\n\n=== RELATÓRIO DIÁRIO ===")
    report_text = generate_daily_report(llm, routes_summary, constraints)
    print(report_text)

    # (Opcional) Q&A
    sample_question = "Quais caminhões entregam mais itens de prioridade Alta e onde estão os maiores deslocamentos?"
    print("\n\n=== Q&A SOBRE ROTAS (exemplo) ===")
    qa_text = answer_question(llm, sample_question, routes_summary)
    print(qa_text)

if __name__ == "__main__":
    print(">>> chamando main()")
    main()
    print(">>> main() terminou")
