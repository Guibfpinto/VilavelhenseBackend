import os
import json
import bcrypt
from config import Config

ARQUIVO_USUARIOS = Config.ARQUIVO_USUARIOS

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        senha_admin = "@W.d06302005"
        hash_admin = bcrypt.hashpw(senha_admin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        usuarios = {"Guibfpinto": hash_admin}
        salvar_usuarios(usuarios)
        return usuarios
    try:
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"Guibfpinto": ""}

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def autenticar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario not in usuarios:
        return False
    hash_senha = usuarios[usuario].encode('utf-8')
    return bcrypt.checkpw(senha.encode('utf-8'), hash_senha)

def adicionar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    hash_novo = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    usuarios[usuario] = hash_novo
    salvar_usuarios(usuarios)
    return True

def remover_usuario(usuario):
    usuarios = carregar_usuarios()
    if usuario == "Guibfpinto":
        return False
    if usuario in usuarios:
        del usuarios[usuario]
        salvar_usuarios(usuarios)
        return True
    return False

def listar_usuarios():
    return list(carregar_usuarios().keys())