from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# ============================================================
# MODELOS DE DADOS (Pydantic)
# ============================================================
class PartidaUpdate(BaseModel):
    gols_casa: Optional[int] = None
    gols_fora: Optional[int] = None
    status: Optional[str] = None

class EventoCreate(BaseModel):
    jogo_id: int
    tempo: int
    tipo: str  # 'Goal', 'Card', 'subst', 'Var', etc.
    jogador_id: int
    detalhes: Optional[str] = ""

class EventoResponse(BaseModel):
    id: int
    jogo_id: int
    tempo: int
    tipo: str
    jogador_id: int
    detalhes: str

# ============================================================
# APLICAÇÃO FASTAPI
# ============================================================
app = FastAPI(title="API do Sistema de Análise de Elenco - Linhares FC")

# Permite requisições de qualquer origem (para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "meu_futebol.db"

def get_db_connection():
    """Retorna uma conexão SQLite com timeout e modo WAL."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row  # permite acesso por nome de coluna
    return conn

# ============================================================
# ROTAS ORIGINAIS
# ============================================================

@app.get("/partida/{jogo_id}")
def get_partida(jogo_id: int):
    """
    Retorna os dados da partida e seus eventos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jogos WHERE id = ?", (jogo_id,))
    partida = cursor.fetchone()
    if not partida:
        conn.close()
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (jogo_id,))
    eventos = cursor.fetchall()

    conn.close()

    return {
        "partida": dict(partida),
        "eventos": [dict(e) for e in eventos]
    }

@app.get("/eventos/{jogo_id}")
def get_eventos(jogo_id: int):
    """Retorna apenas os eventos de uma partida."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (jogo_id,))
    eventos = cursor.fetchall()
    conn.close()
    return [dict(e) for e in eventos]

@app.get("/jogos")
def list_jogos(
    status: Optional[str] = Query(None, description="Filtrar por status (NS, 1H, 2H, HT, FT, etc.)"),
    team_id: Optional[int] = Query(None, description="Filtrar por time (casa ou visitante)"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Lista jogos com filtros opcionais.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jogos WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if team_id:
        query += " AND (time_casa_id = ? OR time_fora_id = ?)"
        params.extend([team_id, team_id])

    query += " ORDER BY data_hora DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    jogos = cursor.fetchall()
    conn.close()

    return [dict(j) for j in jogos]

# ============================================================
# ENDPOINTS: ATUALIZAÇÕES (ESCRITA)
# ============================================================
@app.put("/partida/{jogo_id}/placar")
def update_placar(jogo_id: int, dados: PartidaUpdate):
    """
    Atualiza os gols da partida.
    """
    if dados.gols_casa is None and dados.gols_fora is None:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM jogos WHERE id = ?", (jogo_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    fields = []
    params = []
    if dados.gols_casa is not None:
        fields.append("gols_casa = ?")
        params.append(dados.gols_casa)
    if dados.gols_fora is not None:
        fields.append("gols_fora = ?")
        params.append(dados.gols_fora)
    params.append(jogo_id)

    query = f"UPDATE jogos SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()

    return {"status": "ok", "message": "Placar atualizado"}

@app.put("/partida/{jogo_id}/status")
def update_status(jogo_id: int, dados: PartidaUpdate):
    """
    Atualiza o status da partida.
    """
    if not dados.status:
        raise HTTPException(status_code=400, detail="Status não informado")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE jogos SET status = ? WHERE id = ?", (dados.status, jogo_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    conn.commit()
    conn.close()

    return {"status": "ok", "message": f"Status atualizado para {dados.status}"}

# ============================================================
# ENDPOINTS: EVENTOS
# ============================================================
@app.post("/eventos", response_model=EventoResponse)
def create_evento(evento: EventoCreate):
    """
    Adiciona um novo evento à partida.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM jogos WHERE id = ?", (evento.jogo_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    cursor.execute("SELECT id FROM elenco WHERE id = ?", (evento.jogador_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    cursor.execute("""
        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (evento.jogo_id, evento.tempo, evento.tipo, evento.jogador_id, evento.detalhes))

    evento_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": evento_id,
        "jogo_id": evento.jogo_id,
        "tempo": evento.tempo,
        "tipo": evento.tipo,
        "jogador_id": evento.jogador_id,
        "detalhes": evento.detalhes
    }

@app.delete("/eventos/{evento_id}")
def delete_evento(evento_id: int):
    """
    Remove um evento (caso de correção).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE id = ?", (evento_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Evento removido"}

# ============================================================
# ENDPOINTS: TIMES E ELENCO
# ============================================================
@app.get("/times")
def list_times():
    """Lista todos os times cadastrados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, sigla, logo_url, fundado FROM times ORDER BY nome")
    times = cursor.fetchall()
    conn.close()
    return [dict(t) for t in times]

@app.get("/elenco")
def list_elenco(
    time_id: Optional[int] = Query(None, description="Filtrar por time"),
    posicao: Optional[str] = Query(None, description="Filtrar por posição principal")
):
    """
    Lista jogadores com opção de filtros.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.id, e.nome, e.apelido, e.posicao, e.numero, e.idade, e.foto, e.time_id,
               t.nome AS time_nome
        FROM elenco e
        LEFT JOIN times t ON e.time_id = t.id
        WHERE 1=1
    """
    params = []
    if time_id is not None:
        query += " AND e.time_id = ?"
        params.append(time_id)
    if posicao:
        query += " AND e.posicao LIKE ?"
        params.append(f"%{posicao}%")

    query += " ORDER BY t.nome, e.numero"

    cursor.execute(query, params)
    jogadores = cursor.fetchall()
    conn.close()

    return [dict(j) for j in jogadores]

# ============================================================
# ENDPOINTS: ESTATÍSTICAS
# ============================================================
@app.get("/estatisticas")
def get_estatisticas(
    jogo_id: Optional[int] = Query(None, description="Filtrar por jogo"),
    jogador_id: Optional[int] = Query(None, description="Filtrar por jogador")
):
    """
    Retorna estatísticas dos jogadores.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT est.*, e.nome AS jogador_nome, t.nome AS time_nome
        FROM estatisticas_jogadores est
        LEFT JOIN elenco e ON est.jogador_id = e.id
        LEFT JOIN times t ON e.time_id = t.id
        WHERE 1=1
    """
    params = []
    if jogo_id:
        query += " AND est.jogo_id = ?"
        params.append(jogo_id)
    if jogador_id:
        query += " AND est.jogador_id = ?"
        params.append(jogador_id)

    cursor.execute(query, params)
    stats = cursor.fetchall()
    conn.close()

    return [dict(s) for s in stats]

# ============================================================
# ENDPOINTS: TÉCNICOS E ESTÁDIOS
# ============================================================
@app.get("/tecnicos")
def list_tecnicos(time_id: Optional[int] = None):
    """Lista a comissão técnica."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.*, tm.nome AS time_nome
        FROM tecnicos t
        LEFT JOIN times tm ON t.time_id = tm.id
        WHERE 1=1
    """
    params = []
    if time_id:
        query += " AND t.time_id = ?"
        params.append(time_id)

    cursor.execute(query, params)
    tecnicos = cursor.fetchall()
    conn.close()
    return [dict(t) for t in tecnicos]

@app.get("/estadios")
def list_estadios():
    """Lista todos os estádios."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM venues ORDER BY nome")
    estadios = cursor.fetchall()
    conn.close()
    return [dict(e) for e in estadios]

# ============================================================
# ENDPOINTS: STREAM DE EVENTOS (SSE)
# ============================================================
from fastapi.responses import StreamingResponse
import asyncio

@app.get("/stream/{jogo_id}")
async def stream_eventos(jogo_id: int):
    """
    Stream de eventos ao vivo via Server-Sent Events (SSE).
    """
    async def gerador():
        ultimo_id = None
        while True:
            conn = get_db_connection()
            cursor = conn.cursor()
            if ultimo_id is None:
                cursor.execute("SELECT MAX(id) FROM eventos WHERE jogo_id = ?", (jogo_id,))
                row = cursor.fetchone()
                ultimo_id = row[0] if row and row[0] else 0
            else:
                cursor.execute(
                    "SELECT * FROM eventos WHERE jogo_id = ? AND id > ? ORDER BY id",
                    (jogo_id, ultimo_id)
                )
                novos = cursor.fetchall()
                for ev in novos:
                    ultimo_id = ev['id']
                    yield f"data: {json.dumps(dict(ev))}\n\n"
            conn.close()
            await asyncio.sleep(1)

    return StreamingResponse(gerador(), media_type="text/event-stream")

# ============================================================
# ADAPTAÇÃO PARA OS ENDPOINTS DO FRONTEND (FastAPIMonitorClient)
# ============================================================

def _formatar_partida(row: dict) -> dict:
    """Converte um registro da tabela 'jogos' para o formato da API-Football."""
    return {
        "fixture": {
            "id": row["id"],
            "date": row.get("data_hora", ""),
            "status": {"short": row.get("status", "NS")},
            "venue": {"name": row.get("estadio", "Estádio")},
            "referee": row.get("arbitro", "Não informado")
        },
        "teams": {
            "home": {
                "id": row["time_casa_id"],
                "name": _get_time_nome(row["time_casa_id"])
            },
            "away": {
                "id": row["time_fora_id"],
                "name": _get_time_nome(row["time_fora_id"])
            }
        },
        "goals": {
            "home": row.get("gols_casa"),
            "away": row.get("gols_fora")
        },
        "score": {"penalty": None}
    }

def _get_time_nome(time_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM times WHERE id = ?", (time_id,))
    row = cursor.fetchone()
    conn.close()
    return row["nome"] if row else f"Time {time_id}"

def _get_jogador_nome(jogador_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM elenco WHERE id = ?", (jogador_id,))
    row = cursor.fetchone()
    conn.close()
    return row["nome"] if row else f"Jogador {jogador_id}"

# ----- ROTA: /api/fixtures/live (agora opcionalmente filtra por time) -----
@app.get("/api/fixtures/live")
def get_live_fixture(team_id: Optional[int] = Query(None, description="ID do time para filtrar")):
    """
    Retorna o ID do primeiro jogo ao vivo encontrado.
    Se 'team_id' for fornecido, filtra apenas jogos desse time.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT id FROM jogos
        WHERE status IN ('1H', '2H', 'HT', 'ET', 'P')
    """
    params = []
    if team_id:
        query += " AND (time_casa_id = ? OR time_fora_id = ?)"
        params.extend([team_id, team_id])
    query += " LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"fixture_id": row["id"]}
    return {"fixture_id": None}

# ----- ROTA: /api/fixtures/{fixture_id} -----
@app.get("/api/fixtures/{fixture_id}")
def get_fixture_details(fixture_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return _formatar_partida(dict(row))

# ----- ROTA: /api/fixtures/{fixture_id}/events -----
@app.get("/api/fixtures/{fixture_id}/events")
def get_fixture_events(fixture_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    eventos = []
    for ev in rows:
        eventos.append({
            "time": {"elapsed": ev["tempo"], "extra": None},
            "type": ev["tipo"],
            "detail": ev.get("detalhes", ""),
            "player": {"name": _get_jogador_nome(ev["jogador_id"])},
            "team": {"name": _get_time_nome(ev.get("time_id"))}
        })
    return eventos

# ----- ROTA: /api/fixtures/{fixture_id}/statistics (mock, mas sem fixar time) -----
@app.get("/api/fixtures/{fixture_id}/statistics")
def get_fixture_statistics(fixture_id: int):
    # Busca os times da partida para personalizar o mock
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time_casa_id, time_fora_id FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    time_casa = _get_time_nome(row["time_casa_id"])
    time_fora = _get_time_nome(row["time_fora_id"])
    return [
        {
            "team": {"name": time_casa},
            "statistics": [
                {"type": "Ball Possession", "value": "55%"},
                {"type": "Total Shots", "value": "12"},
                {"type": "Shots on Goal", "value": "5"},
                {"type": "Passes", "value": "320"},
                {"type": "Passes %", "value": "78%"},
                {"type": "Fouls", "value": "10"},
                {"type": "Yellow Cards", "value": "2"},
                {"type": "Red Cards", "value": "0"}
            ]
        },
        {
            "team": {"name": time_fora},
            "statistics": [
                {"type": "Ball Possession", "value": "45%"},
                {"type": "Total Shots", "value": "8"},
                {"type": "Shots on Goal", "value": "3"},
                {"type": "Passes", "value": "250"},
                {"type": "Passes %", "value": "72%"},
                {"type": "Fouls", "value": "15"},
                {"type": "Yellow Cards", "value": "3"},
                {"type": "Red Cards", "value": "0"}
            ]
        }
    ]

# ----- ROTA: /api/fixtures/{fixture_id}/players (mock genérico) -----
@app.get("/api/fixtures/{fixture_id}/players")
def get_fixture_players(fixture_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time_casa_id, time_fora_id FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    # Mock com jogadores genéricos
    return [
        {
            "team": {"id": row["time_casa_id"], "name": _get_time_nome(row["time_casa_id"])},
            "players": [
                {
                    "player": {"name": "Jogador Casa 1"},
                    "statistics": [{
                        "games": {"minutes": 90},
                        "goals": {"total": 1, "assists": 0},
                        "shots": {"total": 3, "on": 2},
                        "passes": {"total": 45, "accurate": 38},
                        "tackles": {"total": 2, "interceptions": 1},
                        "fouls": {"committed": 1, "drawn": 2},
                        "cards": {"yellow": 0, "red": 0}
                    }]
                },
                {
                    "player": {"name": "Jogador Casa 2"},
                    "statistics": [{
                        "games": {"minutes": 90},
                        "goals": {"total": 0, "assists": 1},
                        "shots": {"total": 2, "on": 1},
                        "passes": {"total": 30, "accurate": 25},
                        "tackles": {"total": 1, "interceptions": 0},
                        "fouls": {"committed": 2, "drawn": 1},
                        "cards": {"yellow": 1, "red": 0}
                    }]
                }
            ]
        },
        {
            "team": {"id": row["time_fora_id"], "name": _get_time_nome(row["time_fora_id"])},
            "players": [
                {
                    "player": {"name": "Jogador Fora 1"},
                    "statistics": [{
                        "games": {"minutes": 90},
                        "goals": {"total": 0, "assists": 0},
                        "shots": {"total": 1, "on": 0},
                        "passes": {"total": 30, "accurate": 25},
                        "tackles": {"total": 1, "interceptions": 0},
                        "fouls": {"committed": 2, "drawn": 1},
                        "cards": {"yellow": 1, "red": 0}
                    }]
                }
            ]
        }
    ]

# ----- ROTA: /api/fixtures/{fixture_id}/lineups (mock genérico) -----
@app.get("/api/fixtures/{fixture_id}/lineups")
def get_fixture_lineups(fixture_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time_casa_id, time_fora_id FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return [
        {
            "team": {"id": row["time_casa_id"], "name": _get_time_nome(row["time_casa_id"])},
            "startXI": [
                {"player": {"name": "Casa Goleiro", "number": 1, "pos": "Goleiro"}},
                {"player": {"name": "Casa Zagueiro", "number": 2, "pos": "Zagueiro"}}
            ],
            "substitutes": [
                {"player": {"name": "Casa Reserva", "number": 12, "pos": "Goleiro"}}
            ]
        },
        {
            "team": {"id": row["time_fora_id"], "name": _get_time_nome(row["time_fora_id"])},
            "startXI": [
                {"player": {"name": "Fora Goleiro", "number": 1, "pos": "Goleiro"}}
            ],
            "substitutes": []
        }
    ]

# ----- ROTA: /api/fixtures (agora com team opcional) -----
@app.get("/api/fixtures")
def get_fixtures(
    league: Optional[int] = Query(None, description="ID da liga"),
    season: Optional[int] = Query(None, description="Temporada"),
    team: Optional[int] = Query(None, description="ID do time"),
    from_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)")
):
    """
    Lista partidas com filtros opcionais.
    Se 'team' não for informado, retorna todas as partidas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM jogos WHERE 1=1"
    params = []
    if team:
        query += " AND (time_casa_id = ? OR time_fora_id = ?)"
        params.extend([team, team])
    if from_date:
        query += " AND data_hora >= ?"
        params.append(from_date)
    if to_date:
        query += " AND data_hora <= ?"
        params.append(to_date)
    query += " ORDER BY data_hora"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_formatar_partida(dict(row)) for row in rows]

# ============================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)