# routes/ecossistema_proxy.py — repassa /api/ecossistema/* do Flask para a FastAPI (Config.FASTAPI_URL)
#
# Necessário quando o app mobile fala com o Flask (ex.: via Tailscale Funnel → porta 5000):
# o Flask não tem as rotas do ecossistema, que vivem na FastAPI (porta 8000).
# As rotas /api/ecossistema/ia/* (routes/ia.py) são mais específicas e continuam a ser tratadas pelo Flask.
#
# Registro no app.py:
#     from routes import (..., ecossistema_proxy)
#     app.register_blueprint(ecossistema_proxy.bp)
import requests
from flask import Blueprint, Response, jsonify, request

from config import Config

bp = Blueprint('ecossistema_proxy', __name__)


@bp.route('/api/ecossistema/<path:caminho>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_ecossistema(caminho):
    url = f"{Config.FASTAPI_URL}/api/ecossistema/{caminho}"
    headers = {k: v for k, v in request.headers if k.lower() not in ('host', 'content-length')}
    try:
        resp = requests.request(
            method=request.method, url=url, headers=headers,
            data=request.get_data(), params=request.args,
            timeout=30, allow_redirects=False,
        )
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'FastAPI não está rodando', 'fastapi_url': Config.FASTAPI_URL}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout ao conectar na FastAPI'}), 504

    ocultos = ('content-encoding', 'transfer-encoding', 'connection', 'content-length')
    saida = {k: v for k, v in resp.headers.items() if k.lower() not in ocultos}
    return Response(resp.content, status=resp.status_code, headers=saida)
