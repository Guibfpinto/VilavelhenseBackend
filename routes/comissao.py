from flask import Blueprint, jsonify
from services.dados import carregar_dados_comissao, agrupar_atributos_comissao
from services.cartoes_service import carregar_cartoes, jogador_suspenso
from services.fotos import encontrar_foto_url
from config import Config
import numpy as np

bp = Blueprint('comissao', __name__, url_prefix='/api/comissao')

@bp.route('/<categoria>', methods=['GET'])
def get_comissao(categoria):
    if categoria not in Config.CATEGORIAS_COMISSAO:
        return jsonify({'error': 'Categoria inválida'}), 400

    df = carregar_dados_comissao(categoria)
    if df is None or df.empty:
        return jsonify([])

    cartoes = carregar_cartoes(categoria)
    df['suspenso'] = df['nome_canonico'].apply(lambda x: jogador_suspenso(x, cartoes))

    resultado = []
    for _, row in df.iterrows():
        item = row.replace({np.nan: None}).to_dict()
        nome_busca = item.get('nome')
        item['foto_url'] = encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        item['cartoes'] = cartoes.get(item.get('nome_canonico'), {})
        item['atributos_fm26'] = agrupar_atributos_comissao(item)
        resultado.append(item)

    return jsonify(resultado)