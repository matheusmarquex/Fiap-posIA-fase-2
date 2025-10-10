from utils import (
    load_locations,
    load_demands,
    build_distance_matrix,
    summarize_route,
    route_distance,
    route_load,
)
from ga import genetic_algorithm, split_routes
from visualize import Visualizer
from llm import make_llm, generate_driver_instructions, generate_daily_report, answer_question

def run_ga_for_group(
    group_id,
    locations_group,
    demands_group,
    *,
    generations=500,
    population_size=60,
    mutation_rate=0.1,
    max_per_truck=12,          # limite por número de paradas (continua existindo)
    autonomy_km=250.0,         # autonomia mais realista para SP e região
    max_load_per_truck=80.0,   # capacidade (ex.: "kg" ou "unid. demanda")
):
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

    best_route, best_cost = genetic_algorithm(
        distance_matrix,
        num_trucks=1,
        max_per_truck=max_per_truck,
        population_size=population_size,
        generations=generations,
        mutation_rate=mutation_rate,
        demands=demands_group,
        max_load_per_truck=max_load_per_truck,
        max_distance_per_truck=autonomy_km,
        penalty_over_capacity=1e6,
        penalty_over_distance=1e6,
        callback=callback
    )

    # métricas reais (km/carga)
    real_dist = route_distance(distance_matrix, best_route)
    load_sum = route_load(demands_group, best_route)

    warn_load = (max_load_per_truck is not None) and (load_sum > max_load_per_truck)
    warn_auto = (autonomy_km is not None) and (real_dist > autonomy_km)

    overlay_lines = [
        f"Caminhão {group_id}",
        f"Distância (rota): {real_dist:.2f} km  {'⚠️> autonomia' if warn_auto else ''}",
        f"Carga: {load_sum:.2f} / {max_load_per_truck if max_load_per_truck is not None else 'N/A'}  {'⚠️> capacidade' if warn_load else ''}",
        f"Paradas máx.: {max_per_truck}",
    ]
    visualizer.draw(
        generations,
        [0] + best_route + [0],
        best_cost,
        overlay="\n".join(overlay_lines)
    )

    return best_route, best_cost, real_dist, load_sum, visualizer

def main():
    csv_path = "data/clientes_pedidos.csv"
    all_locations = load_locations(csv_path)
    all_demands = load_demands(csv_path)  # agora demanda ≠ #paradas (se não houver coluna, infere por produto)

    num_trucks = 5
    max_per_truck = 12
    ga_generations = 500
    ga_population = 60
    ga_mutation = 0.1

    # parâmetros realistas
    autonomy_km = 250.0         # autonomia por veículo (km)
    max_load_per_truck = 80.0   # capacidade de carga (ex.: "kg"/unid. demanda)

    constraints_base = {
        "num_trucks": num_trucks,
        "max_per_truck": max_per_truck,
        "max_distance_km": autonomy_km,
        "max_load_per_truck": max_load_per_truck,
    }

    # grupos (cada grupo ≈ 1 caminhão)
    groups = []
    for i in range(num_trucks):
        start = 1 + i * max_per_truck
        end = start + max_per_truck
        loc_group = [all_locations[0]] + all_locations[start:end]
        dem_group = [all_demands[0]] + all_demands[start:end]
        if len(loc_group) > 1:
            groups.append((i + 1, loc_group, dem_group))

    results = []
    llm = make_llm()

    for truck_id, locs, demands_group in groups:
        print(f"\n--- Otimizando Caminhão {truck_id} (clientes: {len(locs)-1}) — {ga_generations} gerações ---")
        best_route, best_cost, real_dist, load_sum, viz = run_ga_for_group(
            truck_id, locs, demands_group,
            generations=ga_generations,
            population_size=ga_population,
            mutation_rate=ga_mutation,
            max_per_truck=max_per_truck,
            autonomy_km=autonomy_km,
            max_load_per_truck=max_load_per_truck,
        )

        print(f"Resumo Caminhão {truck_id}:")
        print(f" - Distância (rota): {real_dist:.2f} km (autonomia: {autonomy_km:.2f} km) {'⚠️ EXCEDE' if real_dist>autonomy_km else ''}")
        print(f" - Carga estimada: {load_sum:.2f} (capacidade: {max_load_per_truck:.2f}) {'⚠️ EXCEDE' if load_sum>max_load_per_truck else ''}")

        route_indices = [0] + best_route + [0]
        route_names = [f"{locs[idx][0]} [{locs[idx][3]} | {locs[idx][4]}]" for idx in route_indices]
        stops, high, low = summarize_route(route_indices, locs)

        viz.hold_until_enter(
            message=(
                f"Caminhão {truck_id}\n"
                f"Distância (rota): {real_dist:.2f} / {autonomy_km:.2f} km\n"
                f"Carga: {load_sum:.2f} / {max_load_per_truck:.2f}\n"
                f"Paradas: {stops}  (Alta={high}, Baixa={low})\n\n"
                f"Pressione ENTER para gerar instruções do motorista..."
            )
        )

        # passa carga/distância reais pro LLM (para alertar se exceder)
        constraints = dict(constraints_base)
        constraints["route_load"] = load_sum
        constraints["route_distance_real"] = real_dist

        text = generate_driver_instructions(
            llm=llm,
            truck_id=truck_id,
            route_indices=route_indices,
            locs=locs,
            constraints=constraints,
            distance=best_cost,  # custo do GA (pode ter penalidade)
        )
        print(f"\n--- INSTRUÇÕES — Caminhão {truck_id} ---\n{text}\n")

        results.append({
            "truck_id": truck_id,
            "best_route": best_route,
            "distance": real_dist,   # relatório usa km reais
            "locs": locs,
            "route_indices": route_indices,
            "route_names": route_names,
            "stops": stops,
            "high_priority": high,
            "low_priority": low,
            "load_sum": load_sum,
        })

    # relatório consolidado
    routes_summary = [{
        "truck_id": r["truck_id"],
        "distance": r["distance"],
        "stops": r["stops"],
        "high_priority": r["high_priority"],
        "low_priority": r["low_priority"],
        "route_names": r["route_names"],
    } for r in results]

    print("\n\n=== RELATÓRIO DIÁRIO ===")
    report_text = generate_daily_report(llm, routes_summary, constraints_base)
    print(report_text)

    # Q&A (exemplo)
    sample_question = "Quais caminhões entregam mais itens de prioridade Alta e onde estão os maiores deslocamentos?"
    print("\n\n=== Q&A SOBRE ROTAS (exemplo) ===")
    qa_text = answer_question(llm, sample_question, routes_summary)
    print(qa_text)

if __name__ == "__main__":
    print(">>> chamando main()")
    main()
    print(">>> main() terminou")
