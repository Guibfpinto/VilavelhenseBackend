import os
import unicodedata
from config import Config

def slugify(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return texto.replace(' ', '_')

def encontrar_foto_url(categoria, nome_apelido):
    if not nome_apelido:
        return None

    mapa_subpastas = {
        'profissional': 'Jogadores/Profissional',
        'sub20': 'Jogadores/Sub20',
        'sub17': 'Jogadores/Sub17',
        'comissao_profissional': 'Comissao_Tecnica/Profissional',
        'comissao_sub20': 'Comissao_Tecnica/Sub20',
        'comissao_sub17': 'Comissao_Tecnica/Sub17',
    }
    subpasta = mapa_subpastas.get(categoria)
    if not subpasta:
        return None

    pasta = os.path.join(Config.DATA_FOLDER, 'fotos', subpasta)
    if not os.path.exists(pasta):
        return None

    nome_slug = slugify(nome_apelido)

    for nome_tentativa in [nome_apelido, nome_slug]:
        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
            caminho = os.path.join(pasta, nome_tentativa + ext)
            if os.path.exists(caminho):
                return f"/fotos/{categoria}/{nome_tentativa}{ext}"

    try:
        arquivos = os.listdir(pasta)
        for arquivo in arquivos:
            nome_arquivo, ext = os.path.splitext(arquivo)
            if ext.lower() in ['.png', '.jpg', '.jpeg']:
                if slugify(nome_arquivo).lower() == nome_slug.lower():
                    return f"/fotos/{categoria}/{arquivo}"
    except:
        pass

    return None