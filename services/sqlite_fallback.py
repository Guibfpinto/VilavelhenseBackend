import sqlite3
import os
from config import Config

def conectar():
    caminho = Config.SQLITE_PATH
    if not os.path.exists(caminho):
        # Se o banco não existir, retorna None (para tratamento de erro)
        return None
    return sqlite3.connect(caminho)

def obter_detalhes_jogo(fixture_id):
    conn = conectar()
    if conn is None:
        return None
    cursor = conn.cursor()
    # Supondo que a tabela 'fixtures' tenha colunas similares à resposta da API
    # Ajuste conforme a estrutura real do seu banco
    cursor.execute("SELECT * FROM fixtures WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # Converter para dicionário no formato esperado pela API
        return {
            'fixture': {
                'id': row[0],
                'date': row[1],
                'status': {'short': row[2]},
                'venue': {'name': row[3]},
                'referee': row[4],
                'attendance': row[5]
            },
            'teams': {
                'home': {'id': row[6], 'name': row[7]},
                'away': {'id': row[8], 'name': row[9]}
            },
            'goals': {'home': row[10], 'away': row[11]},
            'score': {'penalty': {'home': row[12], 'away': row[13]}}
        }
    return None

def obter_eventos_jogo(fixture_id):
    conn = conectar()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE fixture_id = ?", (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    eventos = []
    for row in rows:
        eventos.append({
            'time': {'elapsed': row[1], 'extra': row[2]},
            'type': row[3],
            'detail': row[4],
            'player': {'id': row[5], 'name': row[6]},
            'team': {'id': row[7], 'name': row[8]}
        })
    return eventos

def obter_estatisticas_jogo(fixture_id):
    conn = conectar()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM statistics WHERE fixture_id = ?", (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    # Estrutura similar à da API
    estatisticas = []
    for row in rows:
        estatisticas.append({
            'team': {'id': row[1], 'name': row[2]},
            'statistics': [
                {'type': 'Ball Possession', 'value': row[3]},
                {'type': 'Total Shots', 'value': row[4]},
                # ... mais campos conforme seu banco
            ]
        })
    return estatisticas

def obter_players_stats(fixture_id):
    conn = conectar()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    # Monta estrutura
    stats = []
    for row in rows:
        stats.append({
            'player': {'id': row[1], 'name': row[2]},
            'statistics': [{
                'games': {'minutes': row[3]},
                'goals': {'total': row[4], 'assists': row[5]},
                'shots': {'total': row[6], 'on': row[7]},
                'passes': {'total': row[8], 'accurate': row[9]},
                'tackles': {'total': row[10], 'interceptions': row[11]},
                'fouls': {'committed': row[12], 'drawn': row[13]},
                'cards': {'yellow': row[14], 'red': row[15]}
            }]
        })
    return stats