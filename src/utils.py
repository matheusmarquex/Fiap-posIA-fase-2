import pandas as pd
import math

# --- Distância geodésica (km) ---
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088  # raio médio da Terra em km
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def load_locations(csv_path: str):
    """
    Retorna lista: (nome_cliente, lat, lon, produto, prioridade)
    """
    df = pd.read_csv(csv_path)
    required = {"cliente", "lat", "lon", "produto", "prioridade"}
    if not required.issubset(df.columns):
        raise ValueError(f"O CSV precisa ter as colunas: {required}")
    return list(zip(df["cliente"], df["lat"], df["lon"], df["produto"], df["prioridade"]))

def load_demands(csv_path: str):
    """
    Vetor de demandas alinhado ao CSV.
    - Se existir coluna 'demanda', usa.
    - Senão, infere por tipo de produto (valores exemplo, ajuste se quiser):
        Kit Curativo = 1.0
        Vacina D     = 1.5
        Remédio A/B  = 2.0
        Antibiótico E= 2.5~3.0
        Insumo C     = 3.5~4.0
    Depósito (idx 0) = 0.0
    """
    df = pd.read_csv(csv_path)
    required = {"cliente", "lat", "lon", "produto", "prioridade"}
    if not required.issubset(df.columns):
        raise ValueError(f"O CSV precisa ter as colunas: {required}")

    if "demanda" in df.columns:
        demands = [0.0]
        demands.extend([float(x) for x in df["demanda"].iloc[1:].fillna(1.0).tolist()])
        return demands

    # inferência por produto (defaults razoáveis)
    weights = {
        "Kit Curativo": 1.0,
        "Vacina D": 1.5,
        "Remédio A": 2.0,
        "Remédio B": 2.0,
        "Antibiótico E": 3.0,
        "Insumo C": 3.5,
    }
    demands = [0.0]
    for prod in df["produto"].iloc[1:].tolist():
        demands.append(float(weights.get(str(prod).strip(), 2.0)))
    return demands

def build_distance_matrix(locations):
    """
    Matriz de distâncias reais (km) via Haversine.
    locations = [(nome, lat, lon, produto, prioridade), ...]
    """
    coords = [(lat, lon) for _, lat, lon, _, _ in locations]
    n = len(coords)
    M = [[0.0]*n for _ in range(n)]
    for i in range(n):
        lat1, lon1 = coords[i]
        for j in range(n):
            if i == j: 
                continue
            lat2, lon2 = coords[j]
            M[i][j] = haversine_km(lat1, lon1, lat2, lon2)
    return M

def route_distance(distance_matrix, route):
    """Distância da rota fechando no depósito 0 (km)."""
    if not route:
        return 0.0
    total = distance_matrix[0][route[0]]
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]
    total += distance_matrix[route[-1]][0]
    return total

def route_load(demands, route):
    """Soma de demanda dos clientes (desconsidera depósito)."""
    if not route:
        return 0.0
    return float(sum(float(demands[idx]) for idx in route))

def summarize_route(best_route_indices, locs):
    """
    Conta paradas totais e High/Low com base na coluna 'prioridade'.
    best_route_indices inclui 0 no início e no fim.
    """
    high = low = 0
    for idx in best_route_indices:
        nome, lat, lon, produto, prioridade = locs[idx]
        if nome.lower().startswith("hospital"):
            continue
        if str(prioridade).strip().lower() == "alta":
            high += 1
        else:
            low += 1
    stops = max(0, len(best_route_indices) - 2)
    return stops, high, low
