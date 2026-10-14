# routes/ia.py — Blueprint FLASK que liga o app mobile ao PitchMind (agente de IA)
#
# No app.py:
#     from routes import (..., ia)
#     app.register_blueprint(ia.bp)
#
# O PitchMind (api_http.py, porta 5001) só precisa ser acessível por este backend.
# A chave do LLM fica apenas no .env do PitchMind.
import os

import requests
from flask import Blueprint, jsonify, request

bp = Blueprint('ia', __name__, url_prefix='/api/ecossistema/ia')

PITCHMIND_URL = os.getenv('PITCHMIND_URL', 'http://127.0.0.1:5001')
TIMEOUT_S = int(os.getenv('PITCHMIND_TIMEOUT', '120'))

_REGRAS = (
    ' Consulte as ferramentas para obter dados reais e não invente números.'
    ' Responda em português, em texto corrido, com no máximo 10 linhas.'
)

PROMPTS = {
    'treinador': (
        'Faça um resumo da situação atual da equipa para o treinador principal: lesões ativas e casos de RTP, '
        'alertas de carga (ACWR), próximo jogo e prontidão do plantel.' + _REGRAS
    ),
    'executivo': (
        'Faça um relatório executivo para a direção do clube: disponibilidade física do plantel, lesões ativas, '
        'riscos de carga e o calendário dos próximos jogos.' + _REGRAS
    ),
    'tatico': (
        'Faça um relatório tático para o analista de desempenho: perfil do próximo adversário, jogadores-chave, '
        'formação provável, princípios do nosso modelo de jogo e pontos de atenção.' + _REGRAS
    ),
    'consolidado': (
        'Faça um relatório consolidado para o coordenador técnico: coerência entre o modelo de jogo e o microciclo '
        'atual, estado do plantel (lesões, carga, bem-estar) e prioridades da semana.' + _REGRAS
    ),
}


class _ErroIA(Exception):
    def __init__(self, mensagem, status):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _perguntar(prompt, history=None):
    """Chama POST /ask do PitchMind e devolve o JSON de sucesso."""
    try:
        r = requests.post(
            f'{PITCHMIND_URL}/ask',
            json={'prompt': prompt, 'history': history},
            timeout=TIMEOUT_S,
        )
    except requests.exceptions.RequestException as e:
        raise _ErroIA(f'PitchMind indisponível: {e}', 503)

    if r.status_code != 200:
        raise _ErroIA(f'PitchMind respondeu {r.status_code}: {r.text[:200]}', 502)

    data = r.json()
    if not data.get('ok'):
        raise _ErroIA(data.get('erro') or 'Falha no agente de IA.', 502)
    return data


def _resposta_erro(e):
    # 'detail' é o campo que o app mostra no chat
    return jsonify({'error': e.mensagem, 'detail': e.mensagem}), e.status


@bp.route('/status', methods=['GET'])
def status():
    """Diagnóstico: confirma que o Flask alcança o PitchMind."""
    try:
        r = requests.get(f'{PITCHMIND_URL}/health', timeout=5)
        return jsonify({'pitchmind_url': PITCHMIND_URL, 'pitchmind': r.json()})
    except Exception as e:
        return jsonify({'pitchmind_url': PITCHMIND_URL, 'erro': str(e)}), 503


@bp.route('/contexto-equipa', methods=['POST'])
def contexto_equipa():
    """Relatório automático. O app espera {"resumo_ia": "..."}."""
    dados = request.get_json(silent=True) or {}
    perfil = dados.get('perfil', 'treinador')
    try:
        resp = _perguntar(PROMPTS.get(perfil, PROMPTS['treinador']))
    except _ErroIA as e:
        return _resposta_erro(e)
    return jsonify({'resumo_ia': resp['resposta'], 'tempo_s': resp.get('tempo_s')})


@bp.route('/perguntar', methods=['POST'])
def perguntar():
    """Chat livre com o agente. O histórico é mantido pelo app."""
    dados = request.get_json(silent=True) or {}
    prompt = (dados.get('prompt') or '').strip()
    if not prompt:
        return jsonify({'error': 'Pergunta vazia', 'detail': 'Pergunta vazia'}), 400
    try:
        resp = _perguntar(prompt, dados.get('history'))
    except _ErroIA as e:
        return _resposta_erro(e)
    return jsonify({
        'resposta': resp['resposta'],
        'history': resp.get('history'),
        'tempo_s': resp.get('tempo_s'),
    })
