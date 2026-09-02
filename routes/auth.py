from flask import Blueprint, request, jsonify
from services.auth_service import autenticar_usuario, listar_usuarios, adicionar_usuario, remover_usuario
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = request.headers.get('X-User')
        if not user or user not in listar_usuarios():
            return jsonify({'error': 'Usuário não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    senha = data.get('senha', '')
    if autenticar_usuario(usuario, senha):
        return jsonify({'status': 'ok', 'usuario': usuario, 'token': usuario}), 200
    return jsonify({'error': 'Usuário ou senha inválidos'}), 401

@bp.route('/users', methods=['GET'])
@token_required
def list_users():
    return jsonify(listar_usuarios())

@bp.route('/users', methods=['POST'])
@token_required
def add_user():
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    senha = data.get('senha', '')
    if not usuario or not senha:
        return jsonify({'error': 'Usuário e senha obrigatórios'}), 400
    if adicionar_usuario(usuario, senha):
        return jsonify({'status': 'ok', 'usuario': usuario}), 201
    return jsonify({'error': 'Usuário já existe'}), 409

@bp.route('/users/<usuario>', methods=['DELETE'])
@token_required
def delete_user(usuario):
    if remover_usuario(usuario):
        return jsonify({'status': 'ok'}), 200
    return jsonify({'error': 'Não foi possível remover'}), 400