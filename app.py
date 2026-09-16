#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VILAVELHENSE FC - BACKEND API
Flask + Proxy para FastAPI + Tailscale Funnel
"""
from flask import Flask, jsonify, request, Response, send_from_directory, abort
from flask_cors import CORS
from config import Config
import os
import requests as http_requests

# ========== IMPORTAÇÃO DOS BLUEPRINTS ==========
from routes import (
    auth,
    jogadores,
    comissao,
    diretoria,
    cartoes,
    partida,
    estatisticas,
    proximo_jogo,
    gps,
    jogos,
    treinos,
    wellbeing,
    relatorios,
)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# ========== REGISTRO DOS BLUEPRINTS ==========
app.register_blueprint(auth.bp)
app.register_blueprint(jogadores.bp)
app.register_blueprint(comissao.bp)
app.register_blueprint(diretoria.bp)
app.register_blueprint(cartoes.bp)
app.register_blueprint(partida.bp)
app.register_blueprint(estatisticas.bp)
app.register_blueprint(proximo_jogo.bp)
app.register_blueprint(gps.bp)
app.register_blueprint(jogos.bp)
app.register_blueprint(treinos.bp)
app.register_blueprint(wellbeing.bp)
app.register_blueprint(relatorios.bp)


# ============================================================
# ROTA RAIZ
# ============================================================
@app.route('/')
def home():
    return jsonify({
        'nome': 'Vilavelhense FC API',
        'versao': '2.2',
        'status': 'online',
        'endpoints': {
            'auth': '/api/auth/login',
            'jogadores': '/api/jogadores/<categoria>',
            'jogadores_buscar': '/api/jogadores/<categoria>/buscar?q=...',
            'comissao': '/api/comissao/<categoria>',
            'diretoria': '/api/diretoria/',
            'cartoes': '/api/cartoes/<categoria>',
            'partida_montar': '/api/partida/montar',
            'estatisticas_relatorio': '/api/estatisticas/<categoria>/relatorio',
            'estatisticas_posicao': '/api/estatisticas/<categoria>/posicao',
            'estatisticas_condicao': '/api/estatisticas/<categoria>/condicao',
            'proximo_jogo': '/api/proximo_jogo',
            'gps': '/api/gps/<int:atleta_id>',
            'jogos': '/api/jogos/<int:atleta_id>',
            'treinos': '/api/treinos/<int:atleta_id>',
            'wellbeing': '/api/wellbeing/<int:atleta_id>',
            'relatorios_diretoria': '/api/relatorios/diretoria',
            'relatorios_jogador': '/api/relatorios/jogador/<int:ogol_id>',
            'relatorios_comissao': '/api/relatorios/comissao/<int:membro_id>',
            'relatorios_comissao_completo': '/api/relatorios/comissao/completo',
            'relatorios_wellbeing': '/api/relatorios/wellbeing/<int:atleta_id>',
            'health': '/api/health',
            'fastapi_proxy': '/fastapi/<path>',
        }
    })


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/api/health')
def health():
    """Rota de health check para o app verificar se o servidor está ativo."""
    return jsonify({'status': 'ok'})


# ============================================================
# PROXY PARA FASTAPI (para funcionar através do Funnel)
# ============================================================
@app.route('/fastapi/<path:caminho>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy_fastapi(caminho):
    """
    Encaminha requisições para a FastAPI (localhost:8000).
    Permite que o app acesse a FastAPI através do mesmo túnel do Flask (Funnel/ngrok).
    """
    try:
        url = f"http://localhost:8000/{caminho}"

        # Repassa headers (exceto Host e Content-Length, que são recalculados)
        headers = {
            k: v for k, v in request.headers
            if k.lower() not in ['host', 'content-length']
        }

        # Faz a requisição para a FastAPI
        resp = http_requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            timeout=30,
            allow_redirects=False,
        )

        # Remove headers problemáticos da resposta
        headers_resp = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in [
                'content-encoding',
                'transfer-encoding',
                'connection',
                'content-length',
            ]
        }

        return Response(
            resp.content,
            status=resp.status_code,
            headers=headers_resp
        )

    except http_requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'FastAPI não está rodando',
            'dica': 'Inicie com: uvicorn api:app --port 8000',
            'fastapi_url': 'http://localhost:8000',
        }), 503

    except http_requests.exceptions.Timeout:
        return jsonify({
            'error': 'Timeout ao conectar na FastAPI',
        }), 504

    except Exception as e:
        return jsonify({
            'error': f'Erro no proxy FastAPI: {str(e)}',
        }), 500


# ============================================================
# ROTA PARA FOTOS
# ============================================================
@app.route('/fotos/<categoria>/<path:filename>')
def serve_foto(categoria, filename):
    """Serve fotos de jogadores, comissão e diretoria."""
    mapa_pastas = {
        'profissional': 'Jogadores/Profissional',
        'sub20': 'Jogadores/Sub20',
        'sub17': 'Jogadores/Sub17',
        'comissao_profissional': 'Comissao_Tecnica/Profissional',
        'comissao_sub20': 'Comissao_Tecnica/Sub20',
        'comissao_sub17': 'Comissao_Tecnica/Sub17',
        'diretoria': 'Diretoria',
    }

    subpasta = mapa_pastas.get(categoria)
    if not subpasta:
        abort(404)

    pasta = os.path.join(Config.DATA_FOLDER, 'fotos', subpasta)
    if not os.path.exists(pasta):
        abort(404)

    # Segurança: impede path traversal
    filename = os.path.basename(filename)

    return send_from_directory(pasta, filename)


# ============================================================
# HANDLER 404 CUSTOMIZADO
# ============================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Rota não encontrada.',
        'path': request.path,
        'metodo': request.method,
    }), 404


# ============================================================
# HANDLER 500 CUSTOMIZADO
# ============================================================
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erro interno do servidor.',
        'detalhes': str(error),
    }), 500


# ============================================================
# EXECUÇÃO
# ============================================================
if __name__ == '__main__':
    from services.auth_service import carregar_usuarios

    carregar_usuarios()

    print("=" * 60)
    print("VILAVELHENSE FC - BACKEND API")
    print(f"Servidor rodando em http://{Config.HOST}:{Config.PORT}")
    print(f"Pasta de dados: {Config.DATA_FOLDER}")
    print("=" * 60)
    print("Rotas disponíveis:")
    print("  GET  /                     → info da API")
    print("  GET  /api/health           → health check")
    print("  GET  /api/jogadores/<cat>  → lista de jogadores")
    print("  GET  /api/comissao/<cat>   → lista da comissão")
    print("  GET  /api/diretoria/       → lista da diretoria")
    print("  GET  /fotos/<cat>/<file>   → fotos")
    print("  ALL  /fastapi/<path>       → proxy para FastAPI (porta 8000)")
    print("=" * 60)

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)