from flask import Blueprint, jsonify
from services.dados import carregar_dados_elenco, carregar_dados_comissao, carregar_lesoes
from config import Config
import numpy as np
import pandas as pd

bp = Blueprint('estatisticas', __name__, url_prefix='/api/estatisticas')

@bp.route('/<categoria>/relatorio', methods=['GET'])
def relatorio_completo(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES + Config.CATEGORIAS_COMISSAO:
        return jsonify({'error': 'Categoria inválida'}), 400

    if categoria in Config.CATEGORIAS_JOGADORES:
        df = carregar_dados_elenco(categoria)
        if df is None or df.empty:
            return jsonify({'error': 'Dados não encontrados'}), 404
        lesoes = carregar_lesoes(categoria)
        df['lesionado'] = df.apply(
            lambda row: lesoes.get(row.get('ogol_id')) or lesoes.get(row.get('nome_completo'), False), axis=1
        )
        texto = f"=== RELATÓRIO {categoria.upper()} ===\n"
        texto += f"Total de jogadores: {len(df)}\n"
        if 'Idade' in df.columns and df['Idade'].notna().any():
            texto += f"Idade média: {df['Idade'].mean():.1f} anos\n"
        if 'IMC' in df.columns and df['IMC'].notna().any():
            texto += f"IMC médio: {df['IMC'].mean():.1f}\n"
        if 'Gordura_Corporal_%' in df.columns and df['Gordura_Corporal_%'].notna().any():
            texto += f"Gordura média: {df['Gordura_Corporal_%'].mean():.1f}%\n"
        if 'Rating_Geral_FM26' in df.columns and df['Rating_Geral_FM26'].notna().any():
            texto += f"Rating médio: {df['Rating_Geral_FM26'].mean():.1f}\n"
        if 'Posicao_Principal' in df.columns:
            texto += "\nDistribuição por posição:\n"
            for pos, qtd in df['Posicao_Principal'].value_counts().items():
                texto += f"  {pos}: {qtd}\n"
        if 'lesionado' in df.columns:
            texto += f"\nJogadores lesionados: {df['lesionado'].sum()}\n"
        return jsonify({'relatorio': texto})
    else:
        df = carregar_dados_comissao(categoria)
        if df is None or df.empty:
            return jsonify({'error': 'Dados não encontrados'}), 404
        texto = f"=== RELATÓRIO {categoria.upper()} ===\n"
        texto += f"Total de membros: {len(df)}\n"
        if 'idade' in df.columns and df['idade'].notna().any():
            texto += f"Idade média: {df['idade'].mean():.1f} anos\n"
        if 'cargo' in df.columns:
            texto += "\nDistribuição por cargo:\n"
            for cargo, qtd in df['cargo'].value_counts().items():
                texto += f"  {cargo}: {qtd}\n"
        return jsonify({'relatorio': texto})

@bp.route('/<categoria>/posicao', methods=['GET'])
def analise_posicao(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES + Config.CATEGORIAS_COMISSAO:
        return jsonify({'error': 'Categoria inválida'}), 400
    if categoria in Config.CATEGORIAS_JOGADORES:
        df = carregar_dados_elenco(categoria)
        if df is None or df.empty:
            return jsonify([])
        contagem = df['Posicao_Principal'].value_counts().to_dict()
        return jsonify(contagem)
    else:
        df = carregar_dados_comissao(categoria)
        if df is None or df.empty:
            return jsonify([])
        contagem = df['cargo'].value_counts().to_dict()
        return jsonify(contagem)

@bp.route('/<categoria>/condicao', methods=['GET'])
def condicao_fisica(categoria):
    if categoria not in Config.CATEGORIAS_JOGADORES:
        return jsonify({'error': 'Disponível apenas para jogadores'}), 400
    df = carregar_dados_elenco(categoria)
    if df is None or df.empty:
        return jsonify([])
    resultado = []
    for _, row in df.iterrows():
        resultado.append({
            'nome': row.get('nome_completo'),
            'apelido': row.get('apelido'),
            'estado': row.get('Estado_Fisico'),
            'imc': float(row.get('IMC')) if pd.notna(row.get('IMC')) else None,
            'gordura': float(row.get('Gordura_Corporal_%')) if pd.notna(row.get('Gordura_Corporal_%')) else None
        })
    return jsonify(resultado)