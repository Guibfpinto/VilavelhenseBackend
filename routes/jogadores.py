from flask import Blueprint, request, jsonify
from services.dados import carregar_dados_elenco, carregar_lesoes, carregar_bioimpedancia, agrupar_atributos_jogador
from services.cartoes_service import carregar_cartoes, jogador_suspenso, mapear_nome_para_canonico
from services.fotos import encontrar_foto_url
from config import Config
import numpy as np
import pandas as pd
import os

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

    # Carrega cartões da categoria
    cartoes_geral = carregar_cartoes(categoria)

    resultado = []
    for _, row in df.iterrows():
        # Converte NaN para None
        item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        item['atributos_fm26'] = agrupar_atributos_jogador(item)
        # Adiciona cartões do jogador
        nome_canonico = mapear_nome_para_canonico(item.get('nome_completo'))
        if nome_canonico and nome_canonico in cartoes_geral:
            item['cartoes'] = cartoes_geral[nome_canonico]
        else:
            item['cartoes'] = {}
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
    cartoes_geral = carregar_cartoes(categoria)
    resultado = []
    for _, row in resultados.head(50).iterrows():
        item = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        nome_busca = item.get('apelido') or item.get('nome_completo')
        item['foto_url'] = encontrar_foto_url(categoria, nome_busca) if nome_busca else None
        item['atributos_fm26'] = agrupar_atributos_jogador(item)
        nome_canonico = mapear_nome_para_canonico(item.get('nome_completo'))
        if nome_canonico and nome_canonico in cartoes_geral:
            item['cartoes'] = cartoes_geral[nome_canonico]
        else:
            item['cartoes'] = {}
        resultado.append(item)
    return jsonify(resultado)


@bp.route('/<categoria>/lesoes/<nome>', methods=['GET'])
def get_lesoes_jogador(categoria, nome):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Categoria inválida'}), 400

    if categoria == 'profissional':
        csv_path = Config.ARQUIVOS_LESOES.get('profissional')
    elif categoria == 'sub20':
        csv_path = Config.ARQUIVOS_LESOES.get('sub20')
    else:
        return jsonify({'error': 'Categoria sem suporte para lesões'}), 400

    if not csv_path or not os.path.exists(csv_path):
        return jsonify({'error': 'Arquivo de lesões não encontrado'}), 404

    try:
        df_lesoes = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
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
                # Verifica se tem separador de intervalo
                if ' / ' in occ or ' - ' in occ or '–' in occ:
                    # Já tem data fim, não adicionar "(atual)"
                    ocorrencias_formatadas.append(occ)
                else:
                    # Apenas uma data (lesão atual)
                    ocorrencias_formatadas.append(f"{occ} (atual)")
            linhas.append(f"• {nome_lesao}: {', '.join(ocorrencias_formatadas)}")
    if not tem_lesao:
        return jsonify({'historico': 'Nenhuma lesão registrada.'})
    return jsonify({'historico': '\n'.join(linhas)})