from flask import Blueprint, request, jsonify
from services.dados import carregar_dados_elenco, carregar_lesoes
from services.cartoes_service import carregar_cartoes, jogador_suspenso, mapear_nome_para_canonico
from config import Config
import numpy as np

bp = Blueprint('partida', __name__, url_prefix='/api/partida')

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