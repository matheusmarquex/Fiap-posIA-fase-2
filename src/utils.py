import pandas as pd
import math


def load_locations(csv_path: str):
    df = pd.read_csv(csv_path)
    return list(zip(df["id"], df["lat"], df["lon"]))


def euclidean_distance(coord1, coord2):
    """Distância euclidiana simples entre dois pontos (lat, lon)."""
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def build_distance_matrix(locations):
    """Cria matriz de distâncias entre todos os pontos."""
    coords = [(lat, lon) for _, lat, lon in locations]
    size = len(coords)
    matrix = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = euclidean_distance(coords[i], coords[j])
    return matrix
