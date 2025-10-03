import random
from utils import euclidean_distance


def split_routes(chromosome, num_trucks, max_per_truck):
    """
    Divide cromossomo em sub-rotas (cada caminhão).
    """
    routes = [[] for _ in range(num_trucks)]
    truck = 0
    for client in chromosome:
        if len(routes[truck]) >= max_per_truck:
            truck = (truck + 1) % num_trucks
        routes[truck].append(client)
    return routes


def fitness(chromosome, distance_matrix, num_trucks=5, max_per_truck=12):
    """
    Calcula o custo (distância total) das rotas.
    """
    routes = split_routes(chromosome, num_trucks, max_per_truck)
    total_distance = 0

    for route in routes:
        if not route:
            continue
        current = 0  # hospital (índice 0)
        for client in route:
            total_distance += distance_matrix[current][client]
            current = client
        total_distance += distance_matrix[current][0]  # volta pro hospital

        # Penalização se passar da capacidade
        if len(route) > max_per_truck:
            total_distance += 1e6

    return total_distance


def create_individual(num_clients):
    """
    Cromossomo inicial: permutação de clientes.
    """
    clients = list(range(1, num_clients))  # ignora hospital (0)
    random.shuffle(clients)
    return clients


def crossover(parent1, parent2):
    """Crossover de ordem (OX)."""
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
    """Mutação por troca de posições."""
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            j = random.randint(0, len(individual) - 1)
            individual[i], individual[j] = individual[j], individual[i]
    return individual


def selection(population, fitnesses, k=3):
    """Seleção por torneio simples."""
    selected = random.sample(list(zip(population, fitnesses)), k)
    selected.sort(key=lambda x: x[1])
    return selected[0][0]


def genetic_algorithm(distance_matrix, num_trucks=5, max_per_truck=12,
                      population_size=50, generations=200, mutation_rate=0.05, callback=None):
    """
    Algoritmo Genético para VRP (Vechicle Routing Problem).
    - distance_matrix: matriz de distâncias
    - num_trucks: número de caminhões
    - max_per_truck: capacidade máxima (clientes por caminhão)
    - callback: função chamada a cada geração para visualização
    """
    num_clients = len(distance_matrix)
    population = [create_individual(num_clients) for _ in range(population_size)]

    best_solution = None
    best_cost = float("inf")

    for gen in range(generations):
        fitnesses = [fitness(ind, distance_matrix, num_trucks, max_per_truck) for ind in population]
        new_population = []

        for _ in range(population_size):
            parent1 = selection(population, fitnesses)
            parent2 = selection(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate=mutation_rate)
            new_population.append(child)

        population = new_population

        # Melhor da geração
        for ind in population:
            cost = fitness(ind, distance_matrix, num_trucks, max_per_truck)
            if cost < best_cost:
                best_cost = cost
                best_solution = ind

        # callback para visualização
        if callback and best_solution is not None:
            routes = split_routes(best_solution, num_trucks, max_per_truck)
            callback(gen, routes, best_cost)

    return best_solution, best_cost
