# routes/relatorios.py
from flask import Blueprint, request, jsonify, send_file
from services.relatorios_service import (
    gerar_relatorio_diretoria,
    gerar_relatorio_jogador,
    gerar_relatorio_comissao,
    gerar_relatorio_comissao_completo
)
from services.dados import carregar_dados_elenco, carregar_dados_comissao
from services.gestao import ler_csv
import pandas as pd
import io

bp = Blueprint('relatorios', __name__, url_prefix='/api/relatorios')


# ============================================================
# RELATÓRIO PARA DIRETORIA
# ============================================================
@bp.route('/diretoria', methods=['POST'])
def relatorio_diretoria():
    """Gera relatório executivo para diretoria."""
    df_jogadores = carregar_dados_elenco('profissional')
    df_comissao = carregar_dados_comissao('comissao_profissional')
    if df_jogadores is None or df_comissao is None:
        return jsonify({'error': 'Dados não carregados'}), 404
    arquivo = gerar_relatorio_diretoria(df_jogadores, df_comissao)
    return send_file(
        arquivo,
        download_name=f'relatorio_diretoria_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        as_attachment=True
    )


# ============================================================
# RELATÓRIO INDIVIDUAL DO JOGADOR
# ============================================================
@bp.route('/jogador/<int:ogol_id>', methods=['GET'])
def relatorio_jogador(ogol_id):
    """Gera relatório individual de um jogador."""
    df = carregar_dados_elenco('profissional')
    if df is None:
        return jsonify({'error': 'Dados não carregados'}), 404
    jogador = df[df['ogol_id'] == ogol_id]
    if jogador.empty:
        return jsonify({'error': 'Jogador não encontrado'}), 404
    arquivo = gerar_relatorio_jogador(jogador.iloc[0])
    nome = jogador.iloc[0].get('nome_completo', 'jogador').replace(' ', '_')
    return send_file(
        arquivo,
        download_name=f'relatorio_{nome}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        as_attachment=True
    )


# ============================================================
# RELATÓRIO INDIVIDUAL DA COMISSÃO
# ============================================================
@bp.route('/comissao/<int:membro_id>', methods=['GET'])
def relatorio_comissao(membro_id):
    """Gera relatório individual de um membro da comissão."""
    df = carregar_dados_comissao('comissao_profissional')
    if df is None:
        return jsonify({'error': 'Dados não carregados'}), 404
    membro = df[df['id'] == membro_id]
    if membro.empty:
        return jsonify({'error': 'Membro não encontrado'}), 404
    arquivo = gerar_relatorio_comissao(membro.iloc[0])
    nome = membro.iloc[0].get('nome', 'membro').replace(' ', '_')
    return send_file(
        arquivo,
        download_name=f'relatorio_{nome}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        as_attachment=True
    )


# ============================================================
# RELATÓRIO COMPLETO DA COMISSÃO (com análise tática)
# ============================================================
@bp.route('/comissao/completo', methods=['POST'])
def relatorio_comissao_completo():
    """
    Gera relatório completo para um técnico/membro da comissão com análise tática.
    Recebe: { membro_id, formacao, estilo }
    """
    data = request.get_json()
    membro_id = data.get('membro_id')
    formacao = data.get('formacao', '4-4-2')
    estilo = data.get('estilo', 'Posse de Bola')

    df_comissao = carregar_dados_comissao('comissao_profissional')
    df_jogadores = carregar_dados_elenco('profissional')
    if df_comissao is None or df_jogadores is None:
        return jsonify({'error': 'Dados não carregados'}), 404

    membro = df_comissao[df_comissao['id'] == membro_id]
    if membro.empty:
        return jsonify({'error': 'Membro não encontrado'}), 404

    arquivo = gerar_relatorio_comissao_completo(membro.iloc[0], df_jogadores, formacao, estilo)
    nome = membro.iloc[0].get('nome', 'membro').replace(' ', '_')
    return send_file(
        arquivo,
        download_name=f'relatorio_completo_{nome}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        as_attachment=True
    )


# ============================================================
# RELATÓRIO DE WELL-BEING (integrado)
# ============================================================
@bp.route('/wellbeing/<int:atleta_id>', methods=['GET'])
def relatorio_wellbeing(atleta_id):
    """Gera relatório de bem-estar de um atleta em Excel."""
    dados = ler_csv('data/wellbeing.csv')
    filtrados = [r for r in dados if int(r['atleta_id']) == atleta_id]
    if not filtrados:
        return jsonify({'error': 'Nenhum dado de wellbeing encontrado'}), 404

    df = pd.DataFrame(filtrados)
    df = df[['data', 'sono', 'estresse', 'dor', 'disposicao']]
    df = df.sort_values('data')

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Wellbeing', index=False)
    output.seek(0)

    return send_file(
        output,
        download_name=f'wellbeing_{atleta_id}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        as_attachment=True
    )