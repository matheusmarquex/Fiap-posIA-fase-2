# Fiap-posIA-fase-2

Repositório destinado à Fase 2 – Tech Challenge da pós IA para Devs (FIAP).
Este projeto resolve uma variação simples do VRP (Vehicle Routing Problem) para logística hospitalar com Algoritmo Genético, gerando:

Rotas por caminhão com restrições reais (autonomia em km, capacidade de carga e nº máx. de paradas);

Visualização em tempo real da evolução do GA (pygame);

Instruções ao motorista e relatório diário gerados por LLM (via OpenAI) — com fallback offline;

Q&A em linguagem natural sobre as rotas do dia.

## 📂 Estrutura de Pastas

```
.
├── data/
│   ├── clientes_pedidos.csv     # Base principal (hospital + clientes, lat/lon, produto, prioridade)
│   ├── sample_locations.csv     # Amostra reduzida para testes rápidos
├── src/
│   ├── ga.py                    # Algoritmo Genético (fitness c/ penalidades, crossover, mutate…)
│   ├── llm.py                   # Integração LLM (OpenAI) + prompts e fallback local
│   ├── main.py                  # Orquestração: carrega dados, roda GA por caminhão, chama LLMs
│   ├── utils.py                 # Haversine, leitura do CSV, inferência de demanda, métricas
│   ├── visualize.py             # Visualização da rota e do avanço das gerações (pygame)
│
├── requirements.txt          # Dependências do projeto
├── .gitignore
├── README.md                 # Este arquivo
```

---

## ⚙️ Pré-requisitos

- **Python 3.12+**
- **Pip** instalado
- (Opcional) Chave da OpenAI para gerar textos reais (OPENAI_API_KEY). Sem chave, o projeto usa um fallback local que produz resumos heurísticos.
- **pygame** requer janela gráfica (funciona em macOS, Windows e Linux com servidor gráfico ativo).

---

## 📦 Instalação e Execução Local

### 1️⃣ Clonar o repositório
```bash
git clone https://github.com/matheusmarquex/Fiap-posIA-fase-2.git
cd Fiap-posIA-fase-2
```

### 2️⃣ Criar e ativar um ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

### 3️⃣ Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4️⃣ (Opcional) Configurar a OpenAI
```bash
export OPENAI_API_KEY="sua_chave_aqui"   # Linux/Mac
setx OPENAI_API_KEY "sua_chave_aqui"     # Windows (PowerShell)
```

### 5️⃣ Executar
```bash
python src/main.py

```

---

## 📊 Dados de Entrada

Arquivos CSV em data/ com cabeçalho:

| coluna	  |  descrição |  
|---|---|
|  cliente	  |  Nome do ponto. O índice 0 deve ser o Hospital Central |
|  lat,lon	 |  Coordenadas em graus decimais | 
|  produto	 | Tipo do item (ex.: “Vacina D”, “Antibiótico E”… )  | 
|  prioridade		 | Alta ou Baixa  | 
         

Demanda: se não houver coluna demanda, o sistema infere pesos por produto (ver utils.py):

Kit Curativo=1.0 · Vacina D=1.5 · Remédio A/B=2.0 · Antibiótico E=3.0 · Insumo C=3.5

---

## 🧠 Como funciona

### Algoritmo Genético (src/ga.py)

- Representação: permutação dos clientes (índices 1..N), sempre saindo/voltando ao depósito 0.

- Divisão de rotas (split_routes): fatia a permutação em rotas respeitando max_per_truck.

- Fitness com penalidades: Distância real em km (Haversine) por rota;
    - Penalidade se exceder:

      nº máx. de paradas por veículo (max_per_truck);

      capacidade de carga (soma de demandas);

autonomia (km) por veículo.

Seleção por torneio, OX-like crossover, mutação por swap.

### Visualização (src/visualize.py)

- Mostra pontos (hospital em amarelo; Alta=vermelho; Baixa=verde) e linhas da rota.

- Cabeçalho com geração e custo; overlay final com métricas reais.

### Geração de textos com LLM (src/llm.py)

- Instruções para o motorista (por caminhão);

- Relatório diário consolidado;

- Q&A em linguagem natural.

- Fallback: se OPENAI_API_KEY não estiver definido, usa um modo offline explicativo.


### Parâmetros principais (edite em src/main.py)

```bash
num_trucks = 5
max_per_truck = 12
ga_generations = 500
ga_population = 60
ga_mutation = 0.1

autonomy_km = 250.0        # autonomia por veículo (km)
max_load_per_truck = 80.0  # capacidade de carga (unidades de demanda)

```
    Como os grupos são formados: o script cria 1 grupo ≈ 1 caminhão
    pegando blocos de até max_per_truck clientes sequenciais do CSV (ignorando o índice 0 — hospital).

### ▶️ Exemplo de saída (terminal)

- Resumo por caminhão (km, capacidade, alertas)
- INSTRUÇÕES — Caminhão X (texto ao motorista)
- RELATÓRIO DIÁRIO (sumário executivo, métricas, recomendações)
- Q&A SOBRE ROTAS (respostas curtas e objetivas)

---

## ✨ Tecnologias Utilizadas

- **Python**
- **Pandas**
- **Algoritmos Genéticos**
- **pygame** (visualização)
- **OpenAI (LLM)** - opcional

## 📝 Licença

Livre para uso educacional no contexto do Tech Challenge FIAP.
