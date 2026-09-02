from flask import Blueprint, request, jsonify
from services.cartoes_service import carregar_cartoes, salvar_cartoes, jogador_suspenso, mapear_nome_para_canonico
from config import Config
from datetime import datetime

bp = Blueprint('cartoes', __name__, url_prefix='/api/cartoes')

@bp.route('/<categoria>', methods=['GET'])
def get_cartoes(categoria):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400
    cartoes = carregar_cartoes(categoria)
    return jsonify(cartoes)

@bp.route('/<categoria>', methods=['POST'])
def update_cartoes(categoria):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400
    data = request.get_json()
    cartoes = data.get('cartoes')
    if cartoes is None:
        return jsonify({'error': 'Dados inválidos'}), 400
    if salvar_cartoes(categoria, cartoes):
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Falha ao salvar'}), 500

@bp.route('/<categoria>/jogador/<nome>', methods=['POST'])
def registrar_cartao_individual(categoria, nome):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400
    data = request.get_json()
    cor = data.get('cor')
    minuto = data.get('minuto', 0)
    adversario = data.get('adversario', 'Desconhecido')
    data_jogo = data.get('data_jogo', datetime.now().strftime("%d/%m/%Y"))

    if cor not in ['amarelo', 'vermelho']:
        return jsonify({'error': 'Cor inválida'}), 400

    cartoes = carregar_cartoes(categoria)
    canonico = mapear_nome_para_canonico(nome)
    if not canonico:
        return jsonify({'error': 'Jogador não identificado'}), 404

    if canonico not in cartoes:
        cartoes[canonico] = {'amarelos': 0, 'vermelho': False, 'suspenso_proxima': False, 'historico': []}

    terceiro_amarelo = False
    if cor == 'amarelo':
        cartoes[canonico]['amarelos'] += 1
        if cartoes[canonico]['amarelos'] >= 3:
            cartoes[canonico]['suspenso_proxima'] = True
            terceiro_amarelo = True
    else:
        cartoes[canonico]['vermelho'] = True
        cartoes[canonico]['suspenso_proxima'] = True

    cartoes[canonico]['historico'].append({
        'data': data_jogo,
        'adversario': adversario,
        'cor': cor,
        'terceiro_amarelo': terceiro_amarelo,
        'suspenso_causada': (cor == 'vermelho' or terceiro_amarelo),
        'suspenso_cumprida': False
    })

    if salvar_cartoes(categoria, cartoes):
        return jsonify({'status': 'ok', 'suspenso': cartoes[canonico]['suspenso_proxima']})
    return jsonify({'error': 'Falha ao salvar'}), 500