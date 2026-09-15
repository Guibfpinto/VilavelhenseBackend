# routes/diretoria.py
from flask import Blueprint, jsonify
from services.dados import carregar_dados_diretoria
from services.cartoes_service import carregar_cartoes, jogador_suspenso
from services.fotos import encontrar_foto_url
from config import Config
import pandas as pd

bp = Blueprint('diretoria', __name__, url_prefix='/api/diretoria')


@bp.route('/', methods=['GET'])
def get_diretoria():
    """Retorna todos os membros da diretoria."""
    df = carregar_dados_diretoria('diretoria')
    if df is None or df.empty:
        return jsonify([])

    cartoes = carregar_cartoes('diretoria') if 'diretoria' in Config.CATEGORIAS_CARTOES else {}

    resultado = []
    for _, row in df.iterrows():
        item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        nome_busca = item.get('nome')
        item['foto_url'] = encontrar_foto_url('diretoria', nome_busca) if nome_busca else None
        item['cartoes'] = cartoes.get(item.get('nome_canonico'), {})
        item['suspenso'] = jogador_suspenso(item.get('nome_canonico'), cartoes)
        resultado.append(item)

    return jsonify(resultado)


@bp.route('/<nome_canonico>', methods=['GET'])
def get_membro_diretoria(nome_canonico):
    """Retorna um membro específico da diretoria."""
    df = carregar_dados_diretoria('diretoria')
    if df is None or df.empty:
        return jsonify({'error': 'Dados não carregados'}), 404

    membro = df[df['nome_canonico'] == nome_canonico]
    if membro.empty:
        return jsonify({'error': 'Membro não encontrado'}), 404

    row = membro.iloc[0]
    item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
    item['foto_url'] = encontrar_foto_url('diretoria', item.get('nome'))
    return jsonify(item)