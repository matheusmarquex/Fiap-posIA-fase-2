import random

def split_routes(chromosome, num_trucks, max_per_truck):
    routes = [[] for _ in range(num_trucks)]
    truck = 0
    for client in chromosome:
        if len(routes[truck]) >= max_per_truck:
            truck = (truck + 1) % num_trucks
        routes[truck].append(client)
    return routes

def _route_distance(distance_matrix, route):
    if not route:
        return 0.0
    total = distance_matrix[0][route[0]]
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]
    total += distance_matrix[route[-1]][0]
    return total

def fitness(
    chromosome,
    distance_matrix,
    num_trucks=5,
    max_per_truck=12,
    *,
    demands=None,
    max_load_per_truck=None,      # capacidade (soma de demandas)
    max_distance_per_truck=None,  # autonomia (km)
    penalty_over_capacity=1e6,
    penalty_over_distance=1e6,
):
    routes = split_routes(chromosome, num_trucks, max_per_truck)
    total_distance = 0.0
    total_penalty = 0.0

    has_demands = demands is not None and len(demands) == len(distance_matrix)
    default_demand = 1.0

    for route in routes:
        if not route:
            continue

        dist_r = _route_distance(distance_matrix, route)  # km reais
        total_distance += dist_r

        if len(route) > max_per_truck:
            total_penalty += penalty_over_capacity

        if max_load_per_truck is not None:
            load_sum = 0.0
            for client in route:
                load_sum += float(demands[client]) if has_demands else default_demand
            if load_sum > max_load_per_truck:
                total_penalty += penalty_over_capacity * max(0.0, load_sum - max_load_per_truck)

        if max_distance_per_truck is not None and dist_r > max_distance_per_truck:
            total_penalty += penalty_over_distance * max(0.0, dist_r - max_distance_per_truck)

    return total_distance + total_penalty

def create_individual(num_clients):
    clients = list(range(1, num_clients))
    random.shuffle(clients)
    return clients

def crossover(parent1, parent2):
    start, end = sorted(random.sample(range(len(parent1)), 2))
    child = [None] * len(parent1)
    child[start:end] = parent1[start:end]
    pos = end
    for gene in parent2:
        if gene not in child:
            if pos == len(parent2):
                pos = 0
            child[pos] = gene
            pos += 1
    return child

def mutate(individual, mutation_rate=0.05):
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            j = random.randint(0, len(individual) - 1)
            individual[i], individual[j] = individual[j], individual[i]
    return individual

def selection(population, fitnesses, k=3):
    selected = random.sample(list(zip(population, fitnesses)), k)
    selected.sort(key=lambda x: x[1])
    return selected[0][0]

def genetic_algorithm(
    distance_matrix,
    num_trucks=5,
    max_per_truck=12,
    *,
    population_size=50,
    generations=200,
    mutation_rate=0.05,
    demands=None,
    max_load_per_truck=None,
    max_distance_per_truck=None,
    penalty_over_capacity=1e6,
    penalty_over_distance=1e6,
    callback=None,
):
    num_clients = len(distance_matrix)
    population = [create_individual(num_clients) for _ in range(population_size)]

    best_solution = None
    best_cost = float("inf")

    for gen in range(generations):
        fitnesses = [
            fitness(
                ind, distance_matrix,
                num_trucks=num_trucks,
                max_per_truck=max_per_truck,
                demands=demands,
                max_load_per_truck=max_load_per_truck,
                max_distance_per_truck=max_distance_per_truck,
                penalty_over_capacity=penalty_over_capacity,
                penalty_over_distance=penalty_over_distance,
            )
            for ind in population
        ]
        new_population = []
        for _ in range(population_size):
            parent1 = selection(population, fitnesses)
            parent2 = selection(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate=mutation_rate)
            new_population.append(child)
        population = new_population

        for ind in population:
            cost = fitness(
                ind, distance_matrix,
                num_trucks=num_trucks,
                max_per_truck=max_per_truck,
                demands=demands,
                max_load_per_truck=max_load_per_truck,
                max_distance_per_truck=max_distance_per_truck,
                penalty_over_capacity=penalty_over_capacity,
                penalty_over_distance=penalty_over_distance,
            )
            if cost < best_cost:
                best_cost = cost
                best_solution = ind

        if callback and best_solution is not None:
            routes = split_routes(best_solution, num_trucks, max_per_truck)
            callback(gen, routes, best_cost)

    return best_solution, best_cost
