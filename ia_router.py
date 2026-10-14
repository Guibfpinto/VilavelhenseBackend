# ia_router.py — ponte entre o app mobile e o PitchMind (agente de IA)
#
# Uso no backend principal (FastAPI, porta 8000):
#     from ia_router import router as ia_router
#     app.include_router(ia_router)
#
# O PitchMind (api_http.py, porta 5001) fica só acessível pelo backend.
# A chave do LLM (LLM_API_KEY) continua apenas no .env do PitchMind.
import os

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

PITCHMIND_URL = os.getenv("PITCHMIND_URL", "http://100.118.148.32:5001")
TIMEOUT_S = int(os.getenv("PITCHMIND_TIMEOUT", "120"))

router = APIRouter(prefix="/api/ecossistema/ia", tags=["ia"])

_REGRAS = (
    " Consulte as ferramentas para obter dados reais e não invente números."
    " Responda em português, em texto corrido, com no máximo 10 linhas."
)

PROMPTS = {
    "treinador": (
        "Faça um resumo da situação atual da equipa para o treinador principal: lesões ativas e casos de RTP, "
        "alertas de carga (ACWR), próximo jogo e prontidão do plantel." + _REGRAS
    ),
    "executivo": (
        "Faça um relatório executivo para a direção do clube: disponibilidade física do plantel, lesões ativas, "
        "riscos de carga e o calendário dos próximos jogos." + _REGRAS
    ),
    "tatico": (
        "Faça um relatório tático para o analista de desempenho: perfil do próximo adversário, jogadores-chave, "
        "formação provável, princípios do nosso modelo de jogo e pontos de atenção." + _REGRAS
    ),
    "consolidado": (
        "Faça um relatório consolidado para o coordenador técnico: coerência entre o modelo de jogo e o microciclo "
        "atual, estado do plantel (lesões, carga, bem-estar) e prioridades da semana." + _REGRAS
    ),
}


class Contexto(BaseModel):
    perfil: str = "treinador"


class Pergunta(BaseModel):
    prompt: str
    history: list | None = None


def _perguntar(prompt: str, history: list | None = None) -> dict:
    try:
        r = requests.post(
            f"{PITCHMIND_URL}/ask",
            json={"prompt": prompt, "history": history},
            timeout=TIMEOUT_S,
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(503, f"PitchMind indisponível: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"PitchMind respondeu {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("ok"):
        raise HTTPException(502, data.get("erro") or "Falha no agente de IA.")
    return data


@router.post("/contexto-equipa")
def contexto_equipa(body: Contexto | None = None):
    """Relatório automático. O app espera {"resumo_ia": "..."}."""
    perfil = (body.perfil if body else "treinador")
    data = _perguntar(PROMPTS.get(perfil, PROMPTS["treinador"]))
    return {"resumo_ia": data["resposta"], "tempo_s": data.get("tempo_s")}


@router.post("/perguntar")
def perguntar(body: Pergunta):
    """Chat livre com o agente. O histórico é mantido pelo app."""
    if not body.prompt.strip():
        raise HTTPException(400, "Pergunta vazia")
    data = _perguntar(body.prompt, body.history)
    return {"resposta": data["resposta"], "history": data.get("history"), "tempo_s": data.get("tempo_s")}
