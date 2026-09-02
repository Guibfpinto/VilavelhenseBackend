import os
import json
from config import Config

def carregar_cartoes(categoria):
    caminho = Config.ARQUIVOS_CARTOES.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('cartoes', {})
    except:
        return {}

def salvar_cartoes(categoria, cartoes):
    caminho = Config.ARQUIVOS_CARTOES.get(categoria)
    if not caminho:
        return False
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump({'cartoes': cartoes}, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def jogador_suspenso(nome, cartoes):
    if nome not in cartoes:
        return False
    return cartoes[nome].get('suspenso_proxima', False)

def mapear_nome_para_canonico(nome):
    if not nome:
        return None
    return str(nome).strip()