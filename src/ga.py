import random


def create_route(num_points):
    """Cria uma rota aleatória (permutação dos pontos)."""
    route = list(range(1, num_points))  # ignora o ponto 0 (hospital)
    random.shuffle(route)
    return [0] + route + [0]  # sempre começa e termina no hospital


def fitness(route, distance_matrix):
    """Avalia a distância total de uma rota."""
    return sum(distance_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))


def selection(population, fitnesses, k=3):
    """Torneio simples."""
    selected = random.sample(list(zip(population, fitnesses)), k)
    selected.sort(key=lambda x: x[1])
    return selected[0][0]


def crossover(parent1, parent2):
    """Crossover de ordem (OX)."""
    start, end = sorted(random.sample(range(1, len(parent1) - 1), 2))
    child = [None] * len(parent1)
    child[start:end] = parent1[start:end]

    pos = end
    for gene in parent2[1:-1]:
        if gene not in child:
            if pos == len(parent2) - 1:
                pos = 1
            child[pos] = gene
            pos += 1

    child[0], child[-1] = 0, 0
    return child


def mutate(route, mutation_rate=0.1):
    """Mutação por troca de posições."""
    for i in range(1, len(route) - 1):
        if random.random() < mutation_rate:
            j = random.randint(1, len(route) - 2)
            route[i], route[j] = route[j], route[i]
    return route


def genetic_algorithm(distance_matrix, population_size=50, generations=200, mutation_rate=0.1, callback=None):
    num_points = len(distance_matrix)
    population = [create_route(num_points) for _ in range(population_size)]

    best_route = None
    best_distance = float("inf")

    for gen in range(generations):
        fitnesses = [fitness(ind, distance_matrix) for ind in population]
        new_population = []

        for _ in range(population_size):
            parent1 = selection(population, fitnesses)
            parent2 = selection(population, fitnesses)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate)
            new_population.append(child)

        population = new_population

        # Melhor da geração
        for ind in population:
            dist = fitness(ind, distance_matrix)
            if dist < best_distance:
                best_distance = dist
                best_route = ind

        # callback opcional (ex: atualizar tela pygame)
        if callback:
            callback(gen, best_route, best_distance)

    return best_route, best_distance
