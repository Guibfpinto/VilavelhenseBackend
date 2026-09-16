# services/fotos.py
import os
from config import Config


# ============================================================================
# MAPEAMENTO DE CATEGORIAS PARA PASTAS
# ============================================================================
def obter_pasta_fotos(categoria):
    """Retorna o caminho da pasta de fotos para uma categoria."""
    mapa = {
        'profissional': os.path.join(Config.DATA_FOLDER, 'fotos', 'Jogadores', 'Profissional'),
        'sub20': os.path.join(Config.DATA_FOLDER, 'fotos', 'Jogadores', 'Sub20'),
        'sub17': os.path.join(Config.DATA_FOLDER, 'fotos', 'Jogadores', 'Sub17'),
        'comissao_profissional': os.path.join(Config.DATA_FOLDER, 'fotos', 'Comissao_Tecnica', 'Profissional'),
        'comissao_sub20': os.path.join(Config.DATA_FOLDER, 'fotos', 'Comissao_Tecnica', 'Sub20'),
        'comissao_sub17': os.path.join(Config.DATA_FOLDER, 'fotos', 'Comissao_Tecnica', 'Sub17'),
        'diretoria': os.path.join(Config.DATA_FOLDER, 'fotos', 'Diretoria'),
    }
    return mapa.get(categoria)


# ============================================================================
# ENCONTRAR FOTO (retorna URL relativa)
# ============================================================================
def encontrar_foto_url(categoria, nome):
    """
    Retorna a URL relativa da foto (ex: '/fotos/diretoria/Miguel Trés.png')
    ou None se não encontrar.
    """
    if not nome:
        return None

    pasta = obter_pasta_fotos(categoria)
    if not pasta:
        print(f"⚠️  Categoria desconhecida: {categoria}")
        return None

    if not os.path.exists(pasta):
        print(f"⚠️  Pasta não existe: {pasta}")
        return None

    extensoes = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']
    nome_str = str(nome).strip()

    # Lista todos os arquivos da pasta (para debug)
    try:
        arquivos_pasta = os.listdir(pasta)
        print(f"📁 Procurando '{nome_str}' em {pasta}")
        print(f"   Arquivos: {arquivos_pasta}")
    except Exception as e:
        print(f"⚠️  Erro ao listar pasta: {e}")
        return None

    # Tentativas de encontrar o arquivo
    tentativas = [
        nome_str,                          # Nome exato
        nome_str.replace(' ', '_'),        # Com underscore
        nome_str.lower(),                  # Minúsculo
        nome_str.lower().replace(' ', '_'),
    ]

    for tentativa in tentativas:
        for ext in extensoes:
            arquivo = f"{tentativa}{ext}"
            if arquivo in arquivos_pasta:
                url = f"/fotos/{categoria}/{arquivo}"
                print(f"✅ Foto encontrada: {url}")
                return url

    print(f"❌ Foto NÃO encontrada para '{nome_str}'")
    return None