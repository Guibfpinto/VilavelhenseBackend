from flask import Blueprint, request, jsonify
from services.gestao import ler_csv, escrever_csv, proximo_id

bp = Blueprint('gps', __name__, url_prefix='/api/gps')
CSV_PATH = 'data/gps.csv'
FIELDNAMES = ['id', 'atleta_id', 'data', 'distancia_total', 'velocidade_max', 'sprints']

@bp.route('/<int:atleta_id>', methods=['GET'])
def get_gps_atleta(atleta_id):
    dados = ler_csv(CSV_PATH)
    filtrados = [r for r in dados if int(r['atleta_id']) == atleta_id]
    filtrados.sort(key=lambda x: x['data'], reverse=True)
    return jsonify(filtrados)

@bp.route('/', methods=['POST'])
def add_gps():
    data = request.get_json()
    required = ['atleta_id', 'data', 'distancia_total', 'velocidade_max', 'sprints']
    if not all(k in data for k in required):
        return jsonify({'error': 'Campos obrigatórios'}), 400
    registros = ler_csv(CSV_PATH)
    novo_id = proximo_id(CSV_PATH)
    novo_reg = {k: str(data[k]) for k in FIELDNAMES if k != 'id'}
    novo_reg['id'] = str(novo_id)
    registros.append(novo_reg)
    escrever_csv(CSV_PATH, registros, FIELDNAMES)
    return jsonify(novo_reg), 201