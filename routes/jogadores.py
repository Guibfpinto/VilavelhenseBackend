from flask import Blueprint, request, jsonify
from services.dados import carregar_dados_elenco, carregar_lesoes, carregar_bioimpedancia, agrupar_atributos_jogador
from services.fotos import encontrar_foto_url
from config import Config
import numpy as np

bp = Blueprint('jogadores', __name__, url_prefix='/api/jogadores')

@bp.route('/<categoria>', methods=['GET'])
def get_jogadores(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify({'error': 'Dados não encontrados'}), 404

    lesoes = carregar_lesoes(categoria)
    df['lesionado'] = df.apply(
        lambda row: lesoes.get(row.get('ogol_id')) or lesoes.get(row.get('nome_completo'), False), axis=1
    )

    bio = carregar_bioimpedancia(categoria)
    for idx, row in df.iterrows():
        nome = row.get('nome_completo')
        if nome in bio:
            b = bio[nome]
            if b.get('peso'): df.at[idx, 'peso_kg'] = b['peso']
            if b.get('altura'): df.at[idx, 'altura_cm'] = b['altura'] * 100
            if b.get('gordura'): df.at[idx, 'Gordura_Corporal_%'] = b['gordura']
            if b.get('massa_magra'): df.at[idx, 'Massa_Magra_kg'] = b['massa_magra']
            if b.get('massa_muscular'): df.at[idx, 'Massa_Muscular_Estimada_kg'] = b['massa_muscular']

    resultado = []
    for _, row in df.iterrows():
        item = row.replace({np.nan: None}).to_dict()
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        item['atributos_fm26'] = agrupar_atributos_jogador(item)
        resultado.append(item)

    return jsonify(resultado)

@bp.route('/<categoria>/buscar', methods=['GET'])
def buscar_jogador(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400
    termo = request.args.get('q', '').strip().lower()
    if not termo:
        return jsonify([])
    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify([])
    mask = df['nome_completo'].str.lower().str.contains(termo, na=False) | \
           df['apelido'].str.lower().str.contains(termo, na=False)
    resultados = df[mask]
    resultado = []
    for _, row in resultados.head(50).iterrows():
        item = row.replace({np.nan: None}).to_dict()
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        item['atributos_fm26'] = agrupar_atributos_jogador(item)
        resultado.append(item)
    return jsonify(resultado)