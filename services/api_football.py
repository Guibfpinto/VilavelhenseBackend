import requests
import time
from config import Config

API_KEY = "51e827a67129dbf7e4126c59ac155623"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

def fazer_requisicao_api(endpoint, params={}, tentativa=1):
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 429:
            print(f"⏳ Rate limit (tentativa {tentativa}/3), aguardando 60s...")
            time.sleep(60)
            if tentativa < 3:
                return fazer_requisicao_api(endpoint, params, tentativa+1)
            else:
                return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None

def verificar_jogo_ao_vivo():
    params = {"live": "all"}
    dados = fazer_requisicao_api("/fixtures", params)
    if not dados or not dados.get('response'):
        return None
    TEAM_ID = 15609  # ID do Vilavelhense na API
    for jogo in dados['response']:
        if jogo['teams']['home']['id'] == TEAM_ID or jogo['teams']['away']['id'] == TEAM_ID:
            return jogo['fixture']['id']
    return None

def obter_detalhes_jogo(fixture_id):
    params = {"id": fixture_id}
    dados = fazer_requisicao_api("/fixtures", params)
    if dados and dados.get('response'):
        return dados['response'][0]
    return None

def obter_eventos_jogo(fixture_id):
    params = {"fixture": fixture_id}
    dados = fazer_requisicao_api("/fixtures/events", params)
    if dados and dados.get('response'):
        return dados['response']
    return None

def obter_estatisticas_jogo(fixture_id):
    params = {"fixture": fixture_id}
    dados = fazer_requisicao_api("/fixtures/statistics", params)
    if dados and dados.get('response'):
        return dados['response']
    return None

def obter_escalacao(fixture_id):
    params = {"fixture": fixture_id}
    dados = fazer_requisicao_api("/fixtures/lineups", params)
    if not dados or not dados.get('response'):
        return None
    TEAM_ID = 15609
    for time in dados['response']:
        if time['team']['id'] == TEAM_ID:
            titulares = [j['player']['name'] for j in time['startXI']]
            reservas = [j['player']['name'] for j in time['substitutes']]
            return titulares, reservas
    return None

def obter_players_stats(fixture_id):
    params = {"fixture": fixture_id}
    dados = fazer_requisicao_api("/fixtures/players", params)
    if dados and dados.get('response'):
        return dados['response']
    return None