#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

# ========== IMPORTAÇÃO DE TODOS OS BLUEPRINTS ==========
from routes import (
    auth,
    jogadores,
    comissao,
    cartoes,
    partida,
    estatisticas,
    proximo_jogo,
    gps,
    jogos,
    treinos,
    wellbeing,
    relatorios,                # blueprint principal de relatórios
    relatorioswellbeing        # agora com nome único (relatorios_wellbeing)
)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# ========== REGISTRO DOS BLUEPRINTS ==========
app.register_blueprint(auth.bp)
app.register_blueprint(jogadores.bp)
app.register_blueprint(comissao.bp)
app.register_blueprint(cartoes.bp)
app.register_blueprint(partida.bp)
app.register_blueprint(estatisticas.bp)
app.register_blueprint(proximo_jogo.bp)
app.register_blueprint(gps.bp)
app.register_blueprint(jogos.bp)
app.register_blueprint(treinos.bp)
app.register_blueprint(wellbeing.bp)
app.register_blueprint(relatorios.bp)
app.register_blueprint(relatorioswellbeing.bp)   # agora com nome único

# ========== ROTA RAIZ ==========
@app.route('/')
def home():
    return jsonify({
        'nome': 'Vilavelhense FC API',
        'versao': '2.0',
        'status': 'online',
        'endpoints': [
            '/api/auth/login',
            '/api/jogadores/<categoria>',
            '/api/jogadores/<categoria>/buscar?q=...',
            '/api/comissao/<categoria>',
            '/api/cartoes/<categoria>',
            '/api/partida/montar',
            '/api/estatisticas/<categoria>/relatorio',
            '/api/estatisticas/<categoria>/posicao',
            '/api/estatisticas/<categoria>/condicao',
            '/api/proximo_jogo',
            '/api/gps/<int:atleta_id>',
            '/api/jogos/<int:atleta_id>',
            '/api/treinos/<int:atleta_id>',
            '/api/wellbeing/<int:atleta_id>',
            '/api/relatorios/diretoria',
            '/api/relatorios/jogador/<int:ogol_id>',
            '/api/relatorios/comissao/<int:membro_id>',
            '/api/relatorios/comissao/completo',
            '/api/relatorios/wellbeing/<int:atleta_id>'   # nova rota
        ]
    })

# ========== ROTA PARA FOTOS ==========
@app.route('/fotos/<categoria>/<path:filename>')
def serve_foto(categoria, filename):
    from flask import send_from_directory, abort
    import os
    mapa_pastas = {
        'profissional': 'Jogadores/Profissional',
        'sub20': 'Jogadores/Sub20',
        'sub17': 'Jogadores/Sub17',
        'comissao_profissional': 'Comissao_Tecnica/Profissional',
        'comissao_sub20': 'Comissao_Tecnica/Sub20',
        'comissao_sub17': 'Comissao_Tecnica/Sub17',
    }
    subpasta = mapa_pastas.get(categoria)
    if not subpasta:
        abort(404)
    pasta = os.path.join(Config.DATA_FOLDER, 'fotos', subpasta)
    filename = os.path.basename(filename)  # segurança
    return send_from_directory(pasta, filename)

# ========== EXECUÇÃO ==========
if __name__ == '__main__':
    from services.auth_service import carregar_usuarios
    carregar_usuarios()
    print("="*60)
    print("VILAVELHENSE FC - BACKEND API")
    print(f"Servidor rodando em http://{Config.HOST}:{Config.PORT}")
    print(f"Pasta de dados: {Config.DATA_FOLDER}")
    print("="*60)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)