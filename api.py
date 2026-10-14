from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Depends
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
    tipo: str
    jogador_id: int
    detalhes: Optional[str] = ""

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

class SessaoGuardaRedesCreate(BaseModel):
    treino_id: Optional[int] = None
    atleta_id: Optional[int] = None
    foco: str
    series: int
    repeticoes: int = 0
    quedas_e_saltos_total: int = 0
    observacoes: Optional[str] = None

class VideoClipCreate(BaseModel):
    jogo_id: int
    minuto: int
    tag: str
    descricao: Optional[str] = ""
    url_clip: Optional[str] = ""

class ModeloJogoCreate(BaseModel):
    principio: str
    sub_principio: str
    descricao: str

class EditorTaticoCreate(BaseModel):
    titulo: str
    exercicio_json: str  # Layout de posições e setas da prancha tática
    criado_por: str

class CasoClinicoCreate(BaseModel):
    atleta_id: int
    lesao: str
    gravidade: str  # Leve, Moderada, Grave
    data_previsao_alta: str

# ============================================================
# APLICAÇÃO FASTAPI
# ============================================================
app = FastAPI(title="Vilavelhense FC - API Ecossistema de Alto Rendimento Completo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IA real (PitchMind): rotas /api/ecossistema/ia/contexto-equipa e /perguntar
try:
    from ia_router import router as ia_router
    app.include_router(ia_router)
except Exception as e:
    print(f"Aviso: ia_router não carregado ({e}). Rotas de IA indisponíveis.")

# ============================================================
# DEPENDÊNCIAS DE BASE DE DADOS (Gestão de Conexões)
# ============================================================
DB_SQLITE_PATH = "meu_futebol.db"

def get_sqlite_db():
    conn = sqlite3.connect(DB_SQLITE_PATH, timeout=10, check_same_thread=False)  # FastAPI pode usar threads diferentes
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def garantir_tabelas(conn):
    """Tabelas locais (SQLite) para as rotas do ecossistema que gravam dados."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS casos_clinicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, atleta_id INTEGER, lesao TEXT, gravidade TEXT,
            data_previsao_alta TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS principios_modelo (
            id INTEGER PRIMARY KEY AUTOINCREMENT, principio TEXT, sub_principio TEXT, descricao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS gr_sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, treino_id INTEGER, atleta_id INTEGER, foco TEXT, series INTEGER,
            repeticoes INTEGER, quedas_e_saltos_total INTEGER, observacoes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS video_clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT, jogo_id INTEGER, minuto INTEGER, tag TEXT, descricao TEXT,
            url_clip TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS pranchas_taticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, exercicio_json TEXT, criado_por TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS pwa_registos_local (
            id INTEGER PRIMARY KEY AUTOINCREMENT, atleta_id INTEGER, pse INTEGER, qtr INTEGER, observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    """)

DB_PG_CONFIG = {
    "dbname": "pitchmind",
    "user": "pitchmind",
    "password": "pitchmind",
    "host": "localhost",
    "port": 5432
}

def get_pg_db():
    conn = None
    try:
        conn = psycopg2.connect(**DB_PG_CONFIG)
        yield conn
    except Exception as e:
        print(f"Aviso PostgreSQL: {e}")
        yield None
    finally:
        if conn:
            conn.close()

# ============================================================
# ROTAS CORE: PARTIDAS, EVENTOS E ELENCO (SQLite Local)
# ============================================================

@app.get("/partida/{jogo_id}")
def get_partida(jogo_id: int, conn=Depends(get_sqlite_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jogos WHERE id = ?", (jogo_id,))
    partida = cursor.fetchone()
    if not partida:
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (jogo_id,))
    eventos = cursor.fetchall()

    return {
        "partida": dict(partida),
        "eventos": [dict(e) for e in eventos]
    }

@app.get("/jogos")
def list_jogos(status: Optional[str] = Query(None), team_id: Optional[int] = Query(None), limit: int = Query(50), conn=Depends(get_sqlite_db)):
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
    return [dict(j) for j in cursor.fetchall()]

@app.get("/elenco")
def list_elenco(time_id: Optional[int] = Query(None), posicao: Optional[str] = Query(None), conn=Depends(get_sqlite_db)):
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
    return [dict(j) for j in cursor.fetchall()]

@app.get("/times")
def list_times(conn=Depends(get_sqlite_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, sigla, logo_url, fundado FROM times ORDER BY nome")
    return [dict(t) for t in cursor.fetchall()]

@app.get("/estadios")
def list_estadios(conn=Depends(get_sqlite_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM venues ORDER BY nome")
    return [dict(e) for e in cursor.fetchall()]

# ============================================================
# ECOSSISTEMA DE ALTO RENDIMENTO (PostgreSQL Pitchmind)
# ============================================================

# NOTA: as rotas marcadas com "_stub": True devolvem valores FIXOS de exemplo (ainda não ligadas a dados reais).
# O app mobile mostra o aviso "dados de exemplo" quando recebe "_stub". Os dados reais (ACWR, RTP, microciclo,
# alertas de carga...) vivem no PitchMind (Postgres); a IA já os usa através do agente.

# 1. Agente IA Contextual & Matriz Estratégica
# (POST /api/ecossistema/ia/contexto-equipa e /perguntar vêm do ia_router, incluído acima)

@app.get("/api/ecossistema/matriz-estrategica")
def matriz_estrategica_detalhe(microciclo: str = "MD-4"):
    return {
        "_stub": True,
        "microciclo": microciclo,
        "foco_principal": "Organização Ofensiva e Força Especial",
        "volume_carga": "Moderado/Alto",
        "dimensoes_16": [{"dimensao": "Intensidade", "valor": "85%"}]
    }

# 2. GPS & Carga (ACWR)
@app.get("/api/ecossistema/carga/atleta/{atleta_id}")
def get_carga_atleta(atleta_id: int):
    return {"_stub": True, "atleta_id": atleta_id, "acwr": 1.15, "monotonia": 1.4, "risco_lesao": "Baixo", "velocidade_maxima_recente": "31.4 km/h"}

# 3. Módulo Guarda-Redes
@app.get("/api/ecossistema/guarda_redes/sessao/{treino_id}")
def get_dados_guarda_redes(treino_id: int):
    return {"_stub": True, "treino_id": treino_id, "foco": "Gesto técnico e saídas a cruzamentos", "series": 4, "repeticoes": 8, "quedas_e_saltos_total": 32}

@app.post("/api/ecossistema/guarda_redes/sessao")
def salvar_sessao_guarda_redes(dados: SessaoGuardaRedesCreate, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    conn.execute(
        "INSERT INTO gr_sessoes (treino_id, atleta_id, foco, series, repeticoes, quedas_e_saltos_total, observacoes) VALUES (?,?,?,?,?,?,?)",
        (dados.treino_id, dados.atleta_id, dados.foco, dados.series, dados.repeticoes, dados.quedas_e_saltos_total, dados.observacoes))
    conn.commit()
    return {"status": "sucesso", "mensagem": "Sessão de guarda-redes guardada."}

# 4. PWA & Fisioterapia / RTP 9 Fases & Casos Clínicos
@app.post("/api/ecossistema/pwa/registo-atleta")
def registo_pwa(dados: PWASubmission, conn=Depends(get_pg_db), lite=Depends(get_sqlite_db)):
    if not (1 <= dados.pse <= 10) or not (1 <= dados.qtr <= 5):
        raise HTTPException(status_code=400, detail="Valores de PSE ou QTR inválidos.")
    guardado = False
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pwa_registos (atleta_id, pse, qtr, observacao, data_registo) VALUES (%s, %s, %s, %s, NOW())",
                           (dados.atleta_id, dados.pse, dados.qtr, dados.observacao))
            conn.commit()
            cursor.close()
            guardado = True
        except Exception as e:
            conn.rollback()
            print(f"Aviso PostgreSQL (pwa_registos): {e}")
    if not guardado:  # sem Postgres ou sem a tabela: guarda localmente para não perder o registo
        garantir_tabelas(lite)
        lite.execute("INSERT INTO pwa_registos_local (atleta_id, pse, qtr, observacao) VALUES (?,?,?,?)",
                     (dados.atleta_id, dados.pse, dados.qtr, dados.observacao))
        lite.commit()
    return {"status": "registado", "mensagem": "Registo PWA gravado com sucesso."}

@app.get("/api/ecossistema/fisioterapia/rtp/{atleta_id}")
def consultar_rtp(atleta_id: int):
    return {"_stub": True, "atleta_id": atleta_id, "fase_atual": 4, "total_fases": 9, "descricao_fase": "Recondicionamento Cardiovascular"}

@app.post("/api/ecossistema/fisioterapia/casos-clinicos")
def criar_caso_clinico(dados: CasoClinicoCreate, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    conn.execute("INSERT INTO casos_clinicos (atleta_id, lesao, gravidade, data_previsao_alta) VALUES (?,?,?,?)",
                 (dados.atleta_id, dados.lesao, dados.gravidade, dados.data_previsao_alta))
    conn.commit()
    return {"status": "sucesso", "mensagem": "Caso clínico e controlo de gravidade registados."}

# 5. Análise de Vídeo & Clips
@app.post("/api/ecossistema/video/clips")
def criar_clip_video(dados: VideoClipCreate, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    conn.execute("INSERT INTO video_clips (jogo_id, minuto, tag, descricao, url_clip) VALUES (?,?,?,?,?)",
                 (dados.jogo_id, dados.minuto, dados.tag, dados.descricao, dados.url_clip))
    conn.commit()
    return {"status": "sucesso", "mensagem": "Clip de vídeo guardado e estruturado."}

@app.get("/api/ecossistema/video/clips/{jogo_id}")
def listar_clips_partida(jogo_id: int, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    cur = conn.execute("SELECT id, jogo_id, minuto, tag, descricao, url_clip FROM video_clips WHERE jogo_id = ? ORDER BY minuto", (jogo_id,))
    return [dict(r) for r in cur.fetchall()]

# 6. Editor Tático & Princípios do Modelo de Jogo
@app.post("/api/ecossistema/modelo-jogo/principios")
def definir_principio_modelo(dados: ModeloJogoCreate, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    conn.execute("INSERT INTO principios_modelo (principio, sub_principio, descricao) VALUES (?,?,?)",
                 (dados.principio, dados.sub_principio, dados.descricao))
    conn.commit()
    return {"status": "sucesso", "mensagem": "Princípio metodológico integrado ao modelo de jogo."}

@app.post("/api/ecossistema/editor-tatico/salvar")
def salvar_prancha_tatica(dados: EditorTaticoCreate, conn=Depends(get_sqlite_db)):
    garantir_tabelas(conn)
    conn.execute("INSERT INTO pranchas_taticas (titulo, exercicio_json, criado_por) VALUES (?,?,?)",
                 (dados.titulo, dados.exercicio_json, dados.criado_por))
    conn.commit()
    return {"status": "sucesso", "mensagem": "Prancha tática / apresentação guardada com sucesso."}

# 7. Avaliação Longitudinal & Visão Executiva
@app.get("/api/ecossistema/elenco/longitudinal/{atleta_id}")
def get_avaliacao_longitudinal(atleta_id: int):
    return {"_stub": True, "atleta_id": atleta_id, "fase_desenvolvimento": "Consolidação", "macro_dimensoes": {"fisica": 82, "tatica": 78, "tecnica": 85, "mental": 80}}

@app.get("/api/ecossistema/direcao/dashboard-executivo")
def dashboard_executivo_direcao():
    return {"_stub": True, "equipas_ativas": ["Profissional", "Sub-20", "Sub-17"], "orcamento_utilizado_percentual": 78.5, "disponibilidade_fisica_elenco": 92.0}

# ============================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)