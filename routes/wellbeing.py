from flask import Blueprint, request, jsonify
from services.gestao import ler_csv, escrever_csv, proximo_id
import os

bp = Blueprint('wellbeing', __name__, url_prefix='/api/wellbeing')
CSV_PATH = 'data/wellbeing.csv'
FIELDNAMES = ['id', 'atleta_id', 'data', 'sono', 'estresse', 'dor', 'disposicao']

@bp.route('/<int:atleta_id>', methods=['GET'])
def get_wellbeing_atleta(atleta_id):
    dados = ler_csv(CSV_PATH)
    filtrados = [r for r in dados if int(r['atleta_id']) == atleta_id]
    filtrados.sort(key=lambda x: x['data'], reverse=True)
    return jsonify(filtrados)

@bp.route('/', methods=['POST'])
def add_wellbeing():
    data = request.get_json()
    required = ['atleta_id', 'data', 'sono', 'estresse', 'dor', 'disposicao']
    if not all(k in data for k in required):
        return jsonify({'error': 'Campos obrigatórios'}), 400

    registros = ler_csv(CSV_PATH)
    novo_id = proximo_id(CSV_PATH)
    novo_reg = {k: str(data[k]) for k in FIELDNAMES if k != 'id'}
    novo_reg['id'] = str(novo_id)
    registros.append(novo_reg)
    escrever_csv(CSV_PATH, registros, FIELDNAMES)
    return jsonify(novo_reg), 201

@bp.route('/<int:registro_id>', methods=['DELETE'])
def delete_wellbeing(registro_id):
    registros = ler_csv(CSV_PATH)
    registros = [r for r in registros if int(r['id']) != registro_id]
    escrever_csv(CSV_PATH, registros, FIELDNAMES)
    return jsonify({'status': 'ok'})