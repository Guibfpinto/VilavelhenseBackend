from flask import Blueprint, request, jsonify
import requests
import sqlite3
from config import Config
from services.api_football import (
    verificar_jogo_ao_vivo,
    obter_detalhes_jogo,
    obter_eventos_jogo,
    obter_estatisticas_jogo,
    obter_escalacao,
    obter_players_stats
)
from services.dados import carregar_dados_elenco, carregar_lesoes
from services.cartoes_service import carregar_cartoes, jogador_suspenso, mapear_nome_para_canonico
import numpy as np

bp = Blueprint('partida', __name__, url_prefix='/api/partida')

# ============================================================
# FUNÇÕES AUXILIARES PARA CHAMAR A FASTAPI (FALLBACK)
# ============================================================
def call_fastapi(endpoint, method='GET', params=None, json_data=None):
    """Faz requisição para a FastAPI local (porta 8000) e retorna o JSON."""
    url = f"{Config.FASTAPI_URL}{endpoint}"
    try:
        if method == 'GET':
            resp = requests.get(url, params=params, timeout=5)
        elif method == 'POST':
            resp = requests.post(url, json=json_data, timeout=5)
        elif method == 'PUT':
            resp = requests.put(url, json=json_data, timeout=5)
        else:
            return None
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Erro ao chamar FastAPI: {e}")
        return None


# ============================================================
# ENDPOINT: MONTAR TIME (EXISTENTE)
# ============================================================
@bp.route('/montar', methods=['POST'])
def montar_time():
    data = request.get_json()
    formacao = data.get('formacao', '4-4-2')
    adversario = data.get('adversario', '')
    categoria = data.get('categoria', 'profissional')
    incluir_lesionados = data.get('incluir_lesionados', False)

    if not adversario:
        return jsonify({'error': 'Adversário é obrigatório'}), 400
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify({'error': 'Dados não carregados'}), 404

    partes = formacao.split('-')
    if len(partes) < 3:
        return jsonify({'error': 'Formação inválida (ex: 4-4-2)'}), 400
    try:
        nums = [int(p) for p in partes]
        if sum(nums) != 10:
            return jsonify({'error': 'A soma dos números deve ser 10'}), 400
        defensores, atacantes = nums[0], nums[-1]
        meio_campistas = sum(nums[1:-1])
    except:
        return jsonify({'error': 'Formação inválida'}), 400

    posicoes = [('Goleiro', 'Goleiro')]
    for i in range(defensores):
        posicoes.append((f'Defensor {i+1}', 'Defensor'))
    for i in range(meio_campistas):
        posicoes.append((f'Meio-Campista {i+1}', 'Meio-Campo'))
    for i in range(atacantes):
        posicoes.append((f'Atacante {i+1}', 'Atacante'))

    cartoes = carregar_cartoes(categoria)
    lesoes = carregar_lesoes(categoria)
    df['lesionado'] = df.apply(
        lambda row: lesoes.get(row.get('ogol_id')) or lesoes.get(row.get('nome_completo'), False), axis=1
    )

    def obter_candidatos(pos_tipo, excluidos):
        candidatos = df.copy()
        if pos_tipo == 'Goleiro':
            candidatos = candidatos[candidatos['Posicao_Principal'] == 'Goleiro']
        else:
            candidatos = candidatos[~candidatos['Posicao_Principal'].isin(['Goleiro'])]
        candidatos = candidatos[~candidatos['nome_completo'].isin(excluidos)]
        candidatos = candidatos[~candidatos['nome_completo'].apply(
            lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
        )]
        if not incluir_lesionados:
            candidatos = candidatos[~candidatos['lesionado']]
        candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)
        return candidatos

    titulares = []
    excluidos = set()
    for pos_exibida, pos_tipo in posicoes:
        candidatos = obter_candidatos(pos_tipo, excluidos)
        if len(candidatos) == 0:
            return jsonify({'error': f'Nenhum jogador disponível para {pos_exibida}'}), 400
        escolhido = candidatos.iloc[0]
        titulares.append({
            'posicao_exibida': pos_exibida,
            'posicao_tipo': pos_tipo,
            'nome': escolhido['nome_completo'],
            'apelido': escolhido['apelido'],
            'ogol_id': escolhido.get('ogol_id'),
            'Rating': float(escolhido.get('Rating_Geral_FM26', 0))
        })
        excluidos.add(escolhido['nome_completo'])

    reservas = df[~df['nome_completo'].isin(excluidos)]
    reservas = reservas[~reservas['nome_completo'].apply(
        lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
    )]
    if not incluir_lesionados:
        reservas = reservas[~reservas['lesionado']]
    reservas_list = reservas[['nome_completo', 'apelido', 'Posicao_Principal']].to_dict(orient='records')

    return jsonify({
        'titulares': titulares,
        'reservas': reservas_list,
        'formacao': formacao,
        'adversario': adversario
    })


# ============================================================
# ENDPOINTS DE MONITORAMENTO AO VIVO
# ============================================================

@bp.route('/ao-vivo', methods=['GET'])
def ao_vivo():
    """Retorna o fixture_id do jogo ao vivo."""
    # 1. Tenta API-Football
    fixture_id = verificar_jogo_ao_vivo()
    if fixture_id:
        return jsonify({'fixture_id': fixture_id, 'source': 'api'})
    
    # 2. Fallback: FastAPI
    dados = call_fastapi('/api/fixtures/live', params={'team_id': Config.TEAM_ID})
    if dados and dados.get('fixture_id'):
        return jsonify({'fixture_id': dados['fixture_id'], 'source': 'fastapi'})
    
    # 3. Último fallback: SQLite direto
    try:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jogos WHERE status IN ('1H', '2H', 'HT') LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({'fixture_id': row[0], 'source': 'sqlite'})
    except Exception as e:
        print(f"Erro no SQLite fallback: {e}")
    
    return jsonify({'error': 'Nenhum jogo ao vivo encontrado'}), 404


@bp.route('/detalhes/<int:fixture_id>', methods=['GET'])
def detalhes(fixture_id):
    """Detalhes da partida (API → FastAPI → SQLite)."""
    # 1. API-Football
    dados = obter_detalhes_jogo(fixture_id)
    if dados:
        return jsonify(dados)
    
    # 2. FastAPI
    dados_fast = call_fastapi(f'/api/fixtures/{fixture_id}')
    if dados_fast:
        dados_fast['fallback'] = True
        dados_fast['source'] = 'fastapi'
        return jsonify(dados_fast)
    
    # 3. SQLite direto (sem FastAPI)
    try:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jogos WHERE id = ?", (fixture_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            # Formata no estilo da API (similar à função _formatar_partida da FastAPI)
            # Vamos fazer um mock simples para não quebrar o frontend
            return jsonify({
                'fixture': {'id': row[0], 'status': {'short': row[3]}},
                'teams': {'home': {'name': 'Time Casa'}, 'away': {'name': 'Time Fora'}},
                'goals': {'home': row[4], 'away': row[5]},
                'fallback': True,
                'source': 'sqlite'
            })
    except Exception as e:
        print(f"Erro no SQLite fallback: {e}")
    
    return jsonify({'error': 'Partida não encontrada'}), 404


@bp.route('/eventos/<int:fixture_id>', methods=['GET'])
def eventos(fixture_id):
    """Eventos da partida."""
    dados = obter_eventos_jogo(fixture_id)
    if dados is not None:
        return jsonify(dados)
    dados_fast = call_fastapi(f'/api/fixtures/{fixture_id}/events')
    if dados_fast is not None:
        return jsonify(dados_fast)
    # SQLite direto
    try:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eventos WHERE jogo_id = ? ORDER BY tempo", (fixture_id,))
        rows = cursor.fetchall()
        conn.close()
        eventos_list = []
        for r in rows:
            eventos_list.append({
                'time': {'elapsed': r[2]},
                'type': r[3],
                'detail': r[4],
                'player': {'name': 'Jogador'},
                'team': {'name': 'Time'}
            })
        return jsonify(eventos_list)
    except:
        pass
    return jsonify({'error': 'Eventos não disponíveis'}), 404


@bp.route('/estatisticas/<int:fixture_id>', methods=['GET'])
def estatisticas(fixture_id):
    """Estatísticas coletivas da partida."""
    dados = obter_estatisticas_jogo(fixture_id)
    if dados is not None:
        return jsonify(dados)
    dados_fast = call_fastapi(f'/api/fixtures/{fixture_id}/statistics')
    if dados_fast is not None:
        return jsonify(dados_fast)
    # SQLite direto (mock)
    try:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT time_casa_id, time_fora_id FROM jogos WHERE id = ?", (fixture_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify([
                {'team': {'name': 'Casa'}, 'statistics': [{'type': 'Ball Possession', 'value': '50%'}]},
                {'team': {'name': 'Fora'}, 'statistics': [{'type': 'Ball Possession', 'value': '50%'}]}
            ])
    except:
        pass
    return jsonify({'error': 'Estatísticas não disponíveis'}), 404


@bp.route('/escalacao/<int:fixture_id>', methods=['GET'])
def escalacao(fixture_id):
    """Escalação da partida."""
    dados = obter_escalacao(fixture_id)
    if dados is not None:
        titulares, reservas = dados
        return jsonify({'titulares': titulares, 'reservas': reservas})
    
    # FastAPI lineups
    dados_fast = call_fastapi(f'/api/fixtures/{fixture_id}/lineups')
    if dados_fast and isinstance(dados_fast, list) and len(dados_fast) > 0:
        titulares = []
        reservas = []
        for time in dados_fast:
            if time.get('startXI'):
                for jog in time['startXI']:
                    titulares.append(jog['player']['name'])
            if time.get('substitutes'):
                for jog in time['substitutes']:
                    reservas.append(jog['player']['name'])
        if titulares or reservas:
            return jsonify({'titulares': titulares, 'reservas': reservas, 'fallback': True})
    
    # SQLite direto
    try:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT player_name, is_substitute FROM lineups WHERE fixture_id = ?", (fixture_id,))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            titulares = [r[0] for r in rows if not r[1]]
            reservas = [r[0] for r in rows if r[1]]
            return jsonify({'titulares': titulares, 'reservas': reservas, 'fallback': True})
    except:
        pass
    return jsonify({'error': 'Escalação não disponível'}), 404


@bp.route('/players/<int:fixture_id>', methods=['GET'])
def players_stats(fixture_id):
    """Estatísticas individuais dos jogadores."""
    dados = obter_players_stats(fixture_id)
    if dados is not None:
        return jsonify(dados)
    dados_fast = call_fastapi(f'/api/fixtures/{fixture_id}/players')
    if dados_fast is not None:
        return jsonify(dados_fast)
    return jsonify({'error': 'Estatísticas individuais não disponíveis'}), 404