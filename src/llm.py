import os
import textwrap
from typing import List, Tuple, Dict, Any

class OpenAILLM:

    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENAI_API_KEY no ambiente para usar OpenAI.")

        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, temperature: float = 0.2) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Você é um assistente de logística hospitalar. Responda em português do Brasil, claro e objetivo."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()


class LocalFallbackLLM:
    """
    Para não travar o fluxo de desenvolvimento, se não houver OPENAI_API_KEY, usa um gerador simples (não neural)
    """
    def complete(self, prompt: str, temperature: float = 0.1) -> str:

        header = "⚠️ Modo offline (sem LLM real). Abaixo um resumo heurístico:\n"
        return header + textwrap.shorten(prompt.replace("\n", " "), width=2500, placeholder=" ...")


def make_llm():
    try:
        return OpenAILLM()
    except Exception:
        return LocalFallbackLLM()


# ============
#  Helpers/Prompts
# ============
def _fmt_stop_list(route_indices: List[int], locs: List[Tuple[str, float, float, str, str]]) -> str:
    lines = []
    for i, idx in enumerate(route_indices):
        nome, lat, lon, produto, prioridade = locs[idx]
        tag = "HOSPITAL" if nome.lower().startswith("hospital") else f"{produto} | {prioridade}"
        lines.append(f"{i:02d}. {nome} ({lat:.6f}, {lon:.6f}) — {tag}")
    return "\n".join(lines)


def prompt_driver_instructions(
    truck_id: int,
    route_indices: List[int],
    locs: List[Tuple[str, float, float, str, str]],
    constraints: Dict[str, Any],
    distance: float,
) -> str:
    stops = _fmt_stop_list(route_indices, locs)
    rules = "\n".join([
        f"- Capacidade máx. de paradas: {constraints.get('max_per_truck', 'N/A')}",
        f"- Capacidade de carga (soma das demandas): {constraints.get('max_load_per_truck', 'N/A')}",
        f"- Autonomia (km estimados): {constraints.get('max_distance_km', 'N/A')}",
        f"- Prioridades: Alta deve ser atendida antes de Baixa sempre que possível.",
        "- Retornar ao hospital ao final da rota.",
    ])

    # Alertas (se houverem)
    alerts = []
    if constraints.get("route_load") is not None and constraints.get("max_load_per_truck") is not None:
        rl = constraints["route_load"]; ml = constraints["max_load_per_truck"]
        if rl > ml:
            alerts.append(f"⚠️ Carga estimada ({rl:.2f}) excede capacidade ({ml:.2f}).")
    if constraints.get("route_distance_real") is not None and constraints.get("max_distance_km") is not None:
        rd = constraints["route_distance_real"]; md = constraints["max_distance_km"]
        if rd > md:
            alerts.append(f"⚠️ Distância da rota ({rd:.2f} km) excede autonomia ({md:.2f} km).")

    alerts_text = "\n".join(alerts) if alerts else "Sem alertas."

    return f"""
Gere instruções claras para o MOTORISTA do Caminhão {truck_id}.
Contexto: entrega de medicamentos/insumos hospitalares (alto rigor e segurança).

Regras operacionais:
{rules}

Alertas de planejamento:
{alerts_text}

Distância total estimada (unidade relativa do GA): {distance:.2f}

Roteiro (ordem de paradas, incluindo início/fim no hospital):
{stops}

Instruções solicitadas (em tópicos curtos):
1) Resumo da rota (objetivo e prioridade).
2) Checagens pré-partida (itens, acondicionamento, documentação).
3) Ordem de atendimento (chame atenção às entregas de prioridade Alta).
4) Cuidados no manuseio (especialmente vacinas/antibióticos).
5) Recomendações de segurança e contato em caso de imprevistos.
6) Observações finais (retorno ao hospital, descarte adequado, etc.).
Responda apenas com o texto final destinado ao motorista.
""".strip()


def prompt_daily_report(
    routes_summary: List[Dict[str, Any]],
    constraints: Dict[str, Any],
) -> str:
    bullets = []
    total_dist = 0.0
    tot_stops = 0
    tot_high = 0
    tot_low = 0

    for r in routes_summary:
        total_dist += r["distance"]
        tot_stops += r["stops"]
        tot_high += r["high_priority"]
        tot_low += r["low_priority"]
        bullets.append(
            f"- Caminhão {r['truck_id']}: {r['stops']} paradas "
            f"(Alta={r['high_priority']}, Baixa={r['low_priority']}), "
            f"Distância={r['distance']:.2f}"
        )

    header = "\n".join(bullets)
    return f"""
Gere um RELATÓRIO DIÁRIO das rotas de entrega hospitalar, em PT-BR, com:
- Visão geral (consolidado)
- Métricas por caminhão
- Eficiência (ex.: paradas/rota, % alta prioridade atendida)
- Gargalos e recomendações de melhoria para o próximo dia
- Observações operacionais (inclua alertas de autonomia/capacidade quando existirem)

Dados consolidados de hoje:
{header}

Totais:
- Paradas: {tot_stops}
- Prioridade Alta: {tot_high}
- Prioridade Baixa: {tot_low}
- Distância total (unidade GA): {total_dist:.2f}

Restrições/Parâmetros:
- Capacidade por veículo (paradas): {constraints.get('max_per_truck')}
- Capacidade de carga (soma das demandas): {constraints.get('max_load_per_truck', 'N/A')}
- Autonomia estimada (km): {constraints.get('max_distance_km', 'N/A')}
- Veículos disponíveis: {constraints.get('num_trucks')}

Formato de saída:
1) Sumário executivo (5-8 linhas)
2) Tabela textual simples com métricas por caminhão
3) Recomendações objetivas (5-8 bullets)
4) Observações de risco/compliance
""".strip()


def prompt_qa(question: str, routes_context: str) -> str:
    return f"""
Você responderá perguntas em linguagem natural sobre rotas de entrega hospitalar.

Contexto estruturado (rotas do dia):
{routes_context}

Pergunta do usuário:
{question}

Regras:
- Responda de forma direta e breve (5-10 linhas).
- Use números e nomes quando ajudar.
- Se algo não estiver no contexto, diga o que FALTA e como obter.
""".strip()


def build_routes_context(results: List[Dict[str, Any]]) -> str:
    lines = []
    for r in results:
        lines.append(f"Caminhão {r['truck_id']}: Dist={r['distance']:.2f}, Paradas={r['stops']}")
        for name in r["route_names"]:
            lines.append(f"  - {name}")
    return "\n".join(lines)

def generate_driver_instructions(llm, truck_id: int, route_indices: List[int], locs, constraints, distance: float) -> str:
    prompt = prompt_driver_instructions(truck_id, route_indices, locs, constraints, distance)
    return llm.complete(prompt)

def generate_daily_report(llm, routes_summary: List[Dict[str, Any]], constraints: Dict[str, Any]) -> str:
    prompt = prompt_daily_report(routes_summary, constraints)
    return llm.complete(prompt)

def answer_question(llm, question: str, results_for_context: List[Dict[str, Any]]) -> str:
    ctx = build_routes_context(results_for_context)
    prompt = prompt_qa(question, ctx)
    return llm.complete(prompt)
