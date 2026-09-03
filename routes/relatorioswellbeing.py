from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import io
from openpyxl import Workbook
from services.gestao import ler_csv

bp = Blueprint('relatorios', __name__, url_prefix='/api/relatorios')

@bp.route('/wellbeing/<int:atleta_id>', methods=['GET'])
def relatorio_wellbeing(atleta_id):
    dados = ler_csv('data/wellbeing.csv')
    filtrados = [r for r in dados if int(r['atleta_id']) == atleta_id]
    if not filtrados:
        return jsonify({'error': 'Nenhum dado'}), 404
    df = pd.DataFrame(filtrados)
    df = df[['data', 'sono', 'estresse', 'dor', 'disposicao']]
    df = df.sort_values('data')
    
    # Gera Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Wellbeing', index=False)
    output.seek(0)
    return send_file(output, download_name=f'wellbeing_{atleta_id}.xlsx', as_attachment=True)