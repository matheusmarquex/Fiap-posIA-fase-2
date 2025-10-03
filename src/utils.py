import pandas as pd
import math


def load_locations(csv_path: str):
    """
    Carrega o CSV de clientes e retorna uma lista com:
    (nome_cliente, lat, lon, produto, prioridade)
    """
    df = pd.read_csv(csv_path)

    # garantir que colunas existem
    required = {"cliente", "lat", "lon", "produto", "prioridade"}
    if not required.issubset(df.columns):
        raise ValueError(f"O CSV precisa ter as colunas: {required}")

    return list(zip(df["cliente"], df["lat"], df["lon"], df["produto"], df["prioridade"]))


def euclidean_distance(coord1, coord2):
    """Distância euclidiana simples entre dois pontos (lat, lon)."""
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def build_distance_matrix(locations):
    """
    Cria matriz de distâncias entre todos os pontos.
    locations = [(nome, lat, lon, produto, prioridade), ...]
    """
    coords = [(lat, lon) for _, lat, lon, _, _ in locations]
    size = len(coords)
    matrix = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = euclidean_distance(coords[i], coords[j])
    return matrix
