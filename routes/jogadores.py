from flask import Blueprint, request, jsonify
from services.dados import (
    carregar_dados_elenco,
    carregar_lesoes,
    carregar_bioimpedancia,
    agrupar_atributos_jogador,
    adicionar_lesao,           # 🔥 já existe em dados.py
    adicionar_lesao_com_data_fim,  # 🔥 já existe em dados.py
)
from services.cartoes_service import (
    carregar_cartoes,
    jogador_suspenso,
    mapear_nome_para_canonico,
)
from services.fotos import encontrar_foto_url
from config import Config
import pandas as pd
import os

bp = Blueprint('jogadores', __name__, url_prefix='/api/jogadores')


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

    lesoes = carregar_lesoes(categoria)
    df['lesionado'] = df.apply(
        lambda row: lesoes.get(row.get('ogol_id'))
        or lesoes.get(row.get('nome_completo'), False),
        axis=1,
    )

    bio = carregar_bioimpedancia(categoria)
    for idx, row in df.iterrows():
        nome = row.get('nome_completo')
        if nome in bio:
            b = bio[nome]
            if b.get('peso'):
                df.at[idx, 'peso_kg'] = b['peso']
            if b.get('altura'):
                df.at[idx, 'altura_cm'] = b['altura'] * 100
            if b.get('gordura'):
                df.at[idx, 'Gordura_Corporal_%'] = b['gordura']
            if b.get('massa_magra'):
                df.at[idx, 'Massa_Magra_kg'] = b['massa_magra']
            if b.get('massa_muscular'):
                df.at[idx, 'Massa_Muscular_Estimada_kg'] = b['massa_muscular']

    cartoes_geral = carregar_cartoes(categoria)

    resultado = []
    for _, row in df.iterrows():
        item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = (
            encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        )
        item['atributos_fm26'] = agrupar_atributos_jogador(item)

        nome_canonico = mapear_nome_para_canonico(item.get('nome_completo'))
        if nome_canonico and nome_canonico in cartoes_geral:
            item['cartoes'] = cartoes_geral[nome_canonico]
        else:
            item['cartoes'] = {}

        resultado.append(item)

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

    cartoes_geral = carregar_cartoes(categoria)
    resultado = []

    for _, row in resultados.head(50).iterrows():
        item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = (
            encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        )
        item['atributos_fm26'] = agrupar_atributos_jogador(item)

        nome_canonico = mapear_nome_para_canonico(item.get('nome_completo'))
        if nome_canonico and nome_canonico in cartoes_geral:
            item['cartoes'] = cartoes_geral[nome_canonico]
        else:
            item['cartoes'] = {}

        resultado.append(item)

    return jsonify(resultado)


# ============================================================
# HISTÓRICO DE LESÕES DE UM JOGADOR
# ============================================================
@bp.route('/<categoria>/lesoes/<nome>', methods=['GET'])
def get_lesoes_jogador(categoria, nome):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    # Define o caminho do CSV de lesões
    if categoria == 'profissional':
        csv_path = Config.ARQUIVOS_LESOES.get('profissional')
    elif categoria == 'sub20':
        csv_path = Config.ARQUIVOS_LESOES.get('sub20')
    elif categoria == 'sub17':
        csv_path = Config.ARQUIVOS_LESOES.get('sub17')
    else:
        return jsonify({'error': 'Categoria sem suporte'}), 400

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
# 🔥 REGISTRAR NOVA LESÃO (NOVO)
# ============================================================
@bp.route('/lesoes', methods=['POST'])
def registrar_lesao():
    """
    Registra uma nova lesão para um jogador.
    Body esperado:
    {
        "nome_completo": "Lucas Jorge",
        "tipo_lesao": "Tornozelo",
        "data_inicio": "2026-09-15",
        "data_fim": null  (ou "2026-09-20" se encerrada)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    nome = data.get('nome_completo')
    tipo = data.get('tipo_lesao')
    data_ini = data.get('data_inicio')
    data_fim = data.get('data_fim')  # pode ser None

    if not nome or not tipo or not data_ini:
        return jsonify({
            'error': 'Campos obrigatórios: nome_completo, tipo_lesao, data_inicio'
        }), 400

    # Define o CSV de lesões (sempre profissional por enquanto)
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