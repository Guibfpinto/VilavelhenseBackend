# routes/jogadores.py
from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import os

from services.dados import (
    carregar_dados_elenco,
    carregar_lesoes,
    carregar_bioimpedancia,
    agrupar_atributos_jogador,
    adicionar_lesao,
    adicionar_lesao_com_data_fim,
)
from services.cartoes_service import (
    carregar_cartoes,
    jogador_suspenso,
    mapear_nome_para_canonico,
)
from services.fotos import encontrar_foto_url
from config import Config

bp = Blueprint('jogadores', __name__, url_prefix='/api/jogadores')


# ============================================================
# HELPERS
# ============================================================

def limpar_valor(v):
    """Converte NaN/inf/numpy → tipos JSON-safe."""
    if v is None:
        return None
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else f
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def row_para_dict(row):
    """Converte uma linha do DataFrame em dict JSON-safe."""
    return {k: limpar_valor(v) for k, v in row.items()}


def aplicar_bioimpedancia_em_peso_altura(df, bio):
    """
    Se houver bioimpedância cadastrada para o jogador, sobrescreve
    peso_kg / altura_cm do elenco com o valor mais recente medido.
    As demais colunas (gordura, massa) já vêm tratadas do dados.py.
    """
    if not bio:
        return df

    for idx, row in df.iterrows():
        nome = row.get('nome_completo')
        if nome not in bio:
            continue
        b = bio[nome]
        if b.get('peso'):
            df.at[idx, 'peso_kg'] = b['peso']
        if b.get('altura'):
            df.at[idx, 'altura_cm'] = b['altura'] * 100
    return df


def montar_item_jogador(row, categoria, cartoes_geral):
    """Monta o dicionário de resposta de um jogador."""
    item = row_para_dict(row)

    # Foto
    nome_busca = item.get('apelido') or item.get('nome_completo')
    item['foto_url'] = (
        encontrar_foto_url(categoria, nome_busca) if nome_busca else None
    )

    # Atributos FM26 agrupados
    item['atributos_fm26'] = agrupar_atributos_jogador(item)

    # Cartões
    nome_canonico = mapear_nome_para_canonico(item.get('nome_completo'))
    if nome_canonico and nome_canonico in cartoes_geral:
        item['cartoes'] = cartoes_geral[nome_canonico]
    else:
        item['cartoes'] = {}

    return item


# ============================================================
# LISTAR JOGADORES POR CATEGORIA
# ============================================================
@bp.route('/<categoria>', methods=['GET'])
def get_jogadores(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify({'error': 'Dados não encontrados'}), 404

    # Lesões
    lesoes = carregar_lesoes(categoria)
    df['lesionado'] = df.apply(
        lambda row: lesoes.get(row.get('ogol_id'))
        or lesoes.get(row.get('nome_completo'), False),
        axis=1,
    )

    # Se existir bioimpedância, sobrescreve peso/altura com o medido
    bio = carregar_bioimpedancia(categoria)
    df = aplicar_bioimpedancia_em_peso_altura(df, bio)

    # Cartões
    cartoes_geral = carregar_cartoes(categoria)

    resultado = [
        montar_item_jogador(row, categoria, cartoes_geral)
        for _, row in df.iterrows()
    ]

    return jsonify(resultado)


# ============================================================
# BUSCAR JOGADOR POR NOME/APELIDO
# ============================================================
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

    mask = (
        df['nome_completo'].str.lower().str.contains(termo, na=False)
        | df['apelido'].str.lower().str.contains(termo, na=False)
    )
    resultados = df[mask]

    bio = carregar_bioimpedancia(categoria)
    resultados = aplicar_bioimpedancia_em_peso_altura(resultados.copy(), bio)

    cartoes_geral = carregar_cartoes(categoria)

    resposta = [
        montar_item_jogador(row, categoria, cartoes_geral)
        for _, row in resultados.head(50).iterrows()
    ]

    return jsonify(resposta)


# ============================================================
# DETALHE DE UM JOGADOR (por nome)
# ============================================================
@bp.route('/<categoria>/detalhe/<path:nome>', methods=['GET'])
def detalhe_jogador(categoria, nome):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify({'error': 'Dados não encontrados'}), 404

    # Busca por nome completo, apelido ou nome canônico
    match = df[df['nome_completo'] == nome]
    if match.empty and 'apelido' in df.columns:
        match = df[df['apelido'] == nome]
    if match.empty and 'nome_canonico' in df.columns:
        match = df[df['nome_canonico'] == nome]

    if match.empty:
        return jsonify({'error': f'Jogador "{nome}" não encontrado'}), 404

    bio = carregar_bioimpedancia(categoria)
    match = aplicar_bioimpedancia_em_peso_altura(match.copy(), bio)

    lesoes = carregar_lesoes(categoria)
    row = match.iloc[0]

    lesionado = (
        lesoes.get(row.get('ogol_id'))
        or lesoes.get(row.get('nome_completo'), False)
    )
    match.loc[match.index[0], 'lesionado'] = lesionado

    cartoes_geral = carregar_cartoes(categoria)
    item = montar_item_jogador(match.iloc[0], categoria, cartoes_geral)

    return jsonify(item)


# ============================================================
# HISTÓRICO DE LESÕES DE UM JOGADOR
# ============================================================
@bp.route('/<categoria>/lesoes/<nome>', methods=['GET'])
def get_lesoes_jogador(categoria, nome):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    csv_path = Config.ARQUIVOS_LESOES.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return jsonify({'historico': 'Arquivo de lesões não encontrado.'})

    try:
        df_lesoes = pd.read_csv(
            csv_path, delimiter=';', encoding='utf-8-sig', dtype=str
        )
    except Exception as e:
        return jsonify({'error': f'Erro ao ler lesões: {str(e)}'}), 500

    linha = df_lesoes[df_lesoes['nome_completo'] == nome]
    if linha.empty:
        return jsonify({'historico': 'Nenhum registro de lesão encontrado.'})

    colunas_lesoes = [col for col in df_lesoes.columns if col.startswith('Lesao_')]
    if not colunas_lesoes:
        return jsonify({'historico': 'Nenhuma lesão registrada.'})

    linhas = []
    tem_lesao = False

    for col in colunas_lesoes:
        valor = linha.iloc[0].get(col, '')
        if pd.notna(valor) and str(valor).strip() != '':
            tem_lesao = True
            nome_lesao = col.replace('Lesao_', '').replace('_', ' ')
            ocorrencias = str(valor).split(',')
            ocorrencias_formatadas = []

            for occ in ocorrencias:
                occ = occ.strip().rstrip(';').strip()
                if ' / ' in occ or ' - ' in occ or '–' in occ:
                    ocorrencias_formatadas.append(occ)
                else:
                    ocorrencias_formatadas.append(f"{occ} (atual)")

            linhas.append(
                f"• {nome_lesao}: {', '.join(ocorrencias_formatadas)}"
            )

    if not tem_lesao:
        return jsonify({'historico': 'Nenhuma lesão registrada.'})

    return jsonify({'historico': '\n'.join(linhas)})


# ============================================================
# REGISTRAR NOVA LESÃO
# ============================================================
@bp.route('/lesoes', methods=['POST'])
def registrar_lesao():
    """
    Registra uma nova lesão para um jogador.
    Body:
    {
        "nome_completo": "Lucas Jorge",
        "tipo_lesao": "Tornozelo",
        "data_inicio": "2026-09-15",
        "data_fim": null
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    nome = data.get('nome_completo')
    tipo = data.get('tipo_lesao')
    data_ini = data.get('data_inicio')
    data_fim = data.get('data_fim')

    if not nome or not tipo or not data_ini:
        return jsonify({
            'error': 'Campos obrigatórios: nome_completo, tipo_lesao, data_inicio'
        }), 400

    csv_path = Config.ARQUIVOS_LESOES.get('profissional')
    if not csv_path:
        return jsonify({'error': 'CSV de lesões não configurado'}), 500

    try:
        adicionar_lesao(csv_path, nome, tipo, data_ini, data_fim)
        return jsonify({
            'status': 'ok',
            'mensagem': f'Lesão "{tipo}" registrada para {nome}',
        })
    except Exception as e:
        print(f"❌ Erro ao registrar lesão: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500