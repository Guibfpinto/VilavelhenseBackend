from flask import Blueprint, jsonify
import importlib.util
import os
from config import Config

bp = Blueprint('proximo_jogo', __name__, url_prefix='/api/proximo_jogo')

@bp.route('/', methods=['GET'])
def get_proximo_jogo():
    try:
        spec = importlib.util.spec_from_file_location(
            "vila_profissional_crono_2027",
            os.path.join(Config.BASE_DIR, "vila_profissional_crono_2027.py")
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'obter_proximo_jogo'):
                jogo = module.obter_proximo_jogo()
                if jogo:
                    return jsonify(jogo)
        return jsonify({'error': 'Módulo de cronograma não disponível'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500