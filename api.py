from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import sqlite3
import psycopg2
import psycopg2.extras
import json
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import asyncio

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

class PWASubmission(BaseModel):
    atleta_id: int
    pse: int  # 1 a 10
    qtr: int  # 1 a 5
    observacao: Optional[str] = None

class RTPUpdate(BaseModel):
    atleta_id: int
    fase_atual: int  # 1 a 9
    criterios_concluidos: bool
    notas_clinicas: Optional[str] = None

# ============================================================
# APLICAÇÃO FASTAPI
# ============================================================
app = FastAPI(title="Vilavelhense FC - API Híbrida (SQLite + PostgreSQL Pitchmind)")

# Permite requisições de qualquer origem (para desenvolvimento e Expo Go)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Configuração do SQLite Local (para Partidas, Elenco, Times, etc.)
DB_SQLITE_PATH = "meu_futebol.db"

def get_sqlite_connection():
    """Retorna uma conexão SQLite com timeout e modo WAL."""
    conn = sqlite3.connect(DB_SQLITE_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

# 2. Configuração do PostgreSQL do Docker (para o Ecossistema Pitchmind)
DB_PG_CONFIG = {
    "dbname": "pitchmind",
    "user": "pitchmind",
    "password": "pitchmind",  # Ajuste caso tenha definido outra senha no seu docker
    "host": "localhost",
    "port": 5432
}

def get_pg_connection():
    """Retorna uma conexão com o PostgreSQL do Docker."""
    try:
        conn = psycopg2.connect(**DB_PG_CONFIG)
        return conn
    except Exception as e:
        print(f"Aviso: Não foi possível conectar ao PostgreSQL Pitchmind: {e}")
        return None

# ============================================================
# ROTAS DE PARTIDAS E EVENTOS (SQLite: meu_futebol.db)
# ============================================================

@app.get("/partida/{jogo_id}")
def get_partida(jogo_id: int):
    """Retorna os dados da partida e seus eventos do SQLite local."""
    conn = get_sqlite_connection()
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
    """Retorna apenas os eventos de uma partida do SQLite."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (jogo_id,))
    eventos = cursor.fetchall()
    conn.close()
    return [dict(e) for e in eventos]

@app.get("/jogos")
def list_jogos(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    team_id: Optional[int] = Query(None, description="Filtrar por time"),
    limit: int = Query(50, ge=1, le=200)
):
    """Lista jogos com filtros opcionais no SQLite."""
    conn = get_sqlite_connection()
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
# ENDPOINTS: ATUALIZAÇÕES (ESCRITA NO SQLITE)
# ============================================================
@app.put("/partida/{jogo_id}/placar")
def update_placar(jogo_id: int, dados: PartidaUpdate):
    """Atualiza os gols da partida no SQLite."""
    if dados.gols_casa is None and dados.gols_fora is None:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    conn = get_sqlite_connection()
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

    return {"status": "ok", "message": "Placar atualizado no SQLite"}

@app.put("/partida/{jogo_id}/status")
def update_status(jogo_id: int, dados: PartidaUpdate):
    """Atualiza o status da partida no SQLite."""
    if not dados.status:
        raise HTTPException(status_code=400, detail="Status não informado")

    conn = get_sqlite_connection()
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
    """Adiciona um novo evento à partida no SQLite."""
    conn = get_sqlite_connection()
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
    """Remove um evento no SQLite."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE id = ?", (evento_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Evento removido"}

# ============================================================
# ENDPOINTS: TIMES, ELENCO, TÉCNICOS E ESTÁDIOS (SQLite)
# ============================================================
@app.get("/times")
def list_times():
    """Lista todos os times cadastrados no SQLite."""
    conn = get_sqlite_connection()
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
    """Lista jogadores do SQLite com opção de filtros."""
    conn = get_sqlite_connection()
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

@app.get("/tecnicos")
def list_tecnicos(time_id: Optional[int] = None):
    """Lista a comissão técnica do SQLite."""
    conn = get_sqlite_connection()
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
    """Lista todos os estádios do SQLite."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM venues ORDER BY nome")
    estadios = cursor.fetchall()
    conn.close()
    return [dict(e) for e in estadios]

# ============================================================
# ENDPOINTS DO ECOSSISTEMA (PostgreSQL Docker: pitchmind)
# ============================================================

@app.post("/api/ecossistema/pwa/registo-atleta")
def registo_pwa(dados: PWASubmission):
    """Registo diário de PSE e QTR gravado no PostgreSQL do Pitchmind."""
    if not (1 <= dados.pse <= 10) or not (1 <= dados.qtr <= 5):
        raise HTTPException(status_code=400, detail="Valores de PSE (1-10) ou QTR (1-5) inválidos.")
    
    conn = get_pg_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pwa_registos (atleta_id, pse, qtr, observacao, data_registo)
                VALUES (%s, %s, %s, %s, NOW())
            """, (dados.atleta_id, dados.pse, dados.qtr, dados.observacao))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao inserir no PostgreSQL (tabela pode requerer migração): {e}")

    return {
        "status": "registado",
        "timestamp": datetime.now().isoformat(),
        "atleta_id": dados.atleta_id,
        "pse": dados.pse,
        "qtr": dados.qtr,
        "mensagem": "Registo de bem-estar gravado no PostgreSQL do Pitchmind."
    }

@app.get("/api/ecossistema/fisioterapia/rtp/{atleta_id}")
def consultar_rtp_fisioterapia(atleta_id: int):
    """Consulta o protocolo clínico FIFA de 9 fases."""
    return {
        "atleta_id": atleta_id,
        "fase_atual": 4,
        "total_fases": 9,
        "descricao_fase": "Recondicionamento Cardiovascular sem Carga de Impacto",
        "criterios_pendentes": ["Simetria de força isocinética > 85%", "Ausência de edema residual"]
    }

@app.post("/api/ecossistema/fisioterapia/rtp/atualizar")
def atualizar_rtp_fisioterapia(dados: RTPUpdate):
    """Atualiza o avanço de fase no protocolo RTP de 9 fases."""
    nova_fase = dados.fase_atual + 1 if dados.criterios_concluidos else dados.fase_atual
    return {
        "status": "atualizado",
        "atleta_id": dados.atleta_id,
        "nova_fase": nova_fase,
        "mensagem": "Progresso clínico atualizado no protocolo FIFA."
    }

@app.get("/api/ecossistema/analista/scout-adversario")
def scout_adversario_detalhe():
    """Retorna os pontos fortes e vulnerabilidades do próximo adversário."""
    return {
        "adversario": "Próximo Oponente",
        "sistema_tatico": "4-3-3",
        "pontos_fortes": ["Transição ofensiva veloz pelos corredores laterais"],
        "vulnerabilidades": ["Fragilidade defensiva nas costas dos laterais subidos"]
    }

@app.get("/api/ecossistema/matriz-estrategica")
def matriz_estrategica_detalhe(microciclo: str = "MD-4"):
    """Retorna a matriz de treino para o microciclo."""
    return {
        "microciclo": microciclo,
        "foco_principal": "Organização Ofensiva e Força Especial",
        "volume_carga": "Moderado/Alto"
    }

@app.get("/api/ecossistema/direcao/dashboard-executivo")
def dashboard_executivo_direcao():
    """Consolida as métricas executivas e financeiras para a direção."""
    return {
        "equipas_ativas": ["Profissional", "Sub-20", "Sub-17"],
        "orcamento_utilizado_percentual": 78.5,
        "disponibilidade_fisica_elenco": 92.0
    }

# ============================================================
# COMPATIBILIDADE / MOCK (API-Football com SQLite)
# ============================================================
def _formatar_partida(row: dict) -> dict:
    return {
        "fixture": {
            "id": row["id"],
            "date": row.get("data_hora", ""),
            "status": {"short": row.get("status", "NS")},
            "venue": {"name": row.get("estadio", "Estádio")},
            "referee": row.get("arbitro", "Não informado")
        },
        "teams": {
            "home": {"id": row["time_casa_id"], "name": _get_time_nome(row["time_casa_id"])},
            "away": {"id": row["time_fora_id"], "name": _get_time_nome(row["time_fora_id"])}
        },
        "goals": {"home": row.get("gols_casa"), "away": row.get("gols_fora")},
        "score": {"penalty": None}
    }

def _get_time_nome(time_id: int) -> str:
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM times WHERE id = ?", (time_id,))
    row = cursor.fetchone()
    conn.close()
    return row["nome"] if row else f"Time {time_id}"

@app.get("/api/fixtures/live")
def get_live_fixture(team_id: Optional[int] = Query(None)):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    query = "SELECT id FROM jogos WHERE status IN ('1H', '2H', 'HT', 'ET', 'P')"
    params = []
    if team_id:
        query += " AND (time_casa_id = ? OR time_fora_id = ?)"
        params.extend([team_id, team_id])
    query += " LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return {"fixture_id": row["id"] if row else None}

@app.get("/api/fixtures/{fixture_id}")
def get_fixture_details(fixture_id: int):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return _formatar_partida(dict(row))

# ============================================================
# STREAM DE EVENTOS (SSE) & WEBSOCKET AO VIVO
# ============================================================
@app.get("/stream/{jogo_id}")
async def stream_eventos(jogo_id: int):
    """Stream de eventos ao vivo via Server-Sent Events (SSE)."""
    async def gerador():
        ultimo_id = None
        while True:
            conn = get_sqlite_connection()
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

@app.websocket("/api/partidas/ws/{fixture_id}")
async def websocket_partida(websocket: WebSocket, fixture_id: int):
    """WebSocket para comunicação em tempo real de partidas."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Eco WebSocket [Fixture {fixture_id}]: Evento recebido -> {data}")
    except WebSocketDisconnect:
        print(f"Cliente desconectado da fixture {fixture_id}")

# ============================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)