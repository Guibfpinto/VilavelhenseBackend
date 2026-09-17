# services/dados.py - Classificação via atributos_mapper

import os
import pandas as pd
import numpy as np
from config import Config
from utils.datas import calcular_idade
from services.bioimpedancia import classif_imc, classif_gordura, estado_fisico
from services.cartoes_service import mapear_nome_para_canonico
from services.atributos_mapper import (
    classificar_por_tipo,
    normalizar_valor_atributo,
)


# ============================================================================
# TRADUÇÃO DE NOMES (COMISSÃO)
# ============================================================================

TRADUCAO_ATRIBUTOS_COMISSAO = {
    'Ca': 'CA', 'Pa': 'PA',
    'Reputacao Mundial': 'Reputação Mundial',
    'Reputacao Atual': 'Reputação Atual',
    'Reputacao Local': 'Reputação Local',
    'Qualificacoes Treinador': 'Qualificações Treinador',
    'Jogos Selecao': 'Jogos na Seleção',
    'Gols Selecao': 'Gols na Seleção',
    'Attacking': 'Ataque', 'Defending': 'Defesa', 'Fitness': 'Condicionamento',
    'Goalkeeping': 'Goleiros', 'Possession': 'Posse de Bola', 'Player': 'Jogadores',
    'Tactical': 'Tática', 'Technical': 'Técnica',
    'Peoplemanagement': 'Gestão de Pessoas',
    'Workingwithyoungsters': 'Trabalho com Jovens',
    'Dirtinessallowance': 'Tolerância à Sujeira',
    'Versatility': 'Versatilidade', 'Setpieces': 'Bolas Paradas',
    'Adaptability': 'Adaptabilidade', 'Determination': 'Determinação',
    'Judgingplayerability': 'Avaliação Habilidade',
    'Judgingplayerpotential': 'Avaliação Potencial',
    'Judgingstaffability': 'Avaliação Staff',
    'Negotiating': 'Negociação', 'Authority': 'Autoridade',
    'Motivating': 'Motivação', 'Physiotherapy': 'Fisioterapia',
    'Tacticalknowledge': 'Conhecimento Tático',
    'Depth': 'Profundidade', 'Directness': 'Objetividade',
    'Flamboyancy': 'Efebismo', 'Flexibility': 'Flexibilidade',
    'Freeroles': 'Funções Livres', 'Marking': 'Marcação',
    'Offside': 'Impedimento', 'Pressing': 'Pressão', 'Sittingback': 'Recuo',
    'Tempo': 'Ritmo', 'Useofplaymaker': 'Uso do Armador',
    'Useofsubstitutions': 'Uso de Substituições', 'Width': 'Largura',
    'Judgingplayerdata': 'Avaliação Dados Jogador',
    'Judgingteamdata': 'Avaliação Dados Time',
    'Presentingdata': 'Apresentação de Dados',
    'Sports Science': 'Ciência do Esporte',
    'Ambition': 'Ambição', 'Loyalty': 'Lealdade', 'Pressure': 'Pressão',
    'Professional': 'Profissionalismo', 'Sportsmanship': 'Espírito Esportivo',
    'Temperament': 'Temperamento', 'Controversy': 'Controvérsia',
    'Assistantmanager': 'Auxiliar Técnico', 'Coach': 'Treinador',
    'Fitnesscoach': 'Preparador Físico', 'Goalkeepingcoach': 'Preparador de Goleiros',
    'Manager': 'Técnico Principal', 'Physio': 'Fisioterapeuta', 'Scout': 'Olheiro',
    'Chairman': 'Presidente', 'Directoroffootball': 'Diretor de Futebol',
    'Headofyouthdevelopment': 'Coordenador de Base',
    'Dataanalyst': 'Analista de Dados', 'Sportsscientist': 'Cientista do Esporte',
    'Loanmanager': 'Gerente de Empréstimos', 'Technicaldirector': 'Diretor Técnico',
    'Setpiececoach': 'Treinador de Bolas Paradas',
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def safe_float(valor):
    if pd.isna(valor) or valor is None or str(valor).strip() == '':
        return None
    try:
        return float(str(valor).replace(',', '.'))
    except (ValueError, TypeError):
        return None


def parse_numero_coluna(serie):
    if serie is None:
        return serie
    # Converte para string e troca vírgula decimal por ponto
    s = serie.astype(str).str.replace(',', '.', regex=False)
    # Substitui SOMENTE valores vazios/nulos por '0' (sem mexer nos reais)
    s = s.where(~s.str.strip().isin(['', 'nan', 'None', 'NaN', '<NA>']), '0')
    return pd.to_numeric(s, errors='coerce')

def safe_divide(numerador, denominador):
    if denominador is None or pd.isna(denominador) or denominador == 0:
        return np.nan
    return numerador / denominador


def classificar(valor, tipo):
    """
    Wrapper seguro:
      1) Normaliza o valor (str/float → int) via normalizar_valor_atributo.
      2) Chama o classificador de rótulos (classificar_por_tipo).
    Retorna apenas o label classificado (ex.: 'Bom', 'Médio', 'Alto').
    """
    if pd.isna(valor) or valor is None:
        return None

    valor_norm = normalizar_valor_atributo(valor)

    # Se a normalização falhou (ex.: string não numérica), não classifica
    if valor_norm is None or (isinstance(valor_norm, float) and pd.isna(valor_norm)):
        return None

    return classificar_por_tipo(valor_norm, tipo)


# ============================================================================
# CARREGAMENTO DE JOGADORES
# ============================================================================

def carregar_dados_elenco(categoria):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        return None

    try:
        df_raw = pd.read_csv(
            caminho, sep=';', dtype=str, encoding='utf-8-sig', header=None
        )
        cabecalhos_originais = df_raw.iloc[0].tolist()
        df = df_raw.iloc[1:].reset_index(drop=True)

        nomes_fixos = [
            'nome_completo', 'apelido', 'data_nascimento', 'posicao', 'pe_pref',
            'altura_cm', 'peso_kg', 'salario', 'cidade_nascimento', 'uf_nascimento',
            'pais_nascimento', 'historico'
        ]
        for i, nome in enumerate(nomes_fixos):
            if i < df.shape[1]:
                df.rename(columns={i: nome}, inplace=True)

        for i in range(12, df.shape[1]):
            nome_original = (
                cabecalhos_originais[i] if i < len(cabecalhos_originais)
                else f'col_{i}'
            )
            nome_normalizado = (
                str(nome_original).strip().replace('\ufeff', '')
                .replace(' ', '_').lower()
            )
            df.rename(columns={i: nome_normalizado}, inplace=True)

        colunas_numericas = [
            'altura_cm', 'peso_kg', 'habilidade_atual', 'habilidade_potencial'
        ]
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = parse_numero_coluna(df[col])

        for attr in Config.ATRIBUTOS_FM26_JOGADORES:
            if attr in df.columns:
                df[attr] = parse_numero_coluna(df[attr])

        estatisticas_jogador = [
            'jogos_temporada', 'gols_totais', 'assistencias_totais',
            'cartoes_amarelos_totais', 'cartoes_vermelhos_totais',
            'minutos_totais', 'media_minutos_por_jogo',
            'chutes_totais', 'chutes_ao_gol_totais', 'desarmes_totais',
            'interceptacoes_totais', 'passes_certos_totais', 'passes_chave_totais',
            'defesas_totais', 'jogos_sem_sofrer_gols', 'gols_sofridos',
            'participacoes_diretas', 'ogol_rating_estatisticas', 'ogol_aproveitamento'
        ]
        for col in estatisticas_jogador:
            if col in df.columns:
                df[col] = parse_numero_coluna(df[col])
            else:
                df[col] = 0

        def calc_imc(row):
            altura = row.get('altura_cm')
            peso = row.get('peso_kg')
            if (altura is None or peso is None
                    or pd.isna(altura) or pd.isna(peso)):
                return np.nan
            try:
                altura_f = float(altura)
                peso_f = float(peso)
            except (TypeError, ValueError):
                return np.nan
            if altura_f <= 0:
                return np.nan
            return round(peso_f / ((altura_f / 100) ** 2), 1)

        df['IMC'] = df.apply(calc_imc, axis=1)
        df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)

        df['Idade'] = df['data_nascimento'].apply(
            lambda x: calcular_idade(x) if pd.notna(x) else None
        )

        def calc_gordura(row):
            imc = row.get('IMC')
            idade = row.get('Idade')
            if (imc is None or idade is None
                    or pd.isna(imc) or pd.isna(idade)):
                return np.nan
            try:
                return round((1.20 * float(imc)) + (0.23 * float(idade)) - 16.2, 1)
            except (TypeError, ValueError):
                return np.nan

        df['Gordura_Corporal_%'] = df.apply(calc_gordura, axis=1)

        def calc_massa_magra(row):
            peso = row.get('peso_kg')
            gordura = row.get('Gordura_Corporal_%')
            if (peso is None or gordura is None
                    or pd.isna(peso) or pd.isna(gordura)):
                return np.nan
            try:
                return round(float(peso) * (1 - float(gordura) / 100), 1)
            except (TypeError, ValueError):
                return np.nan

        df['Massa_Magra_kg'] = df.apply(calc_massa_magra, axis=1)

        def calc_massa_muscular(row):
            mm = row.get('Massa_Magra_kg')
            if mm is None or pd.isna(mm):
                return np.nan
            try:
                return round(float(mm) * 0.55, 1)
            except (TypeError, ValueError):
                return np.nan

        df['Massa_Muscular_Estimada_kg'] = df.apply(calc_massa_muscular, axis=1)

        df['Classificacao_Gordura'] = df.apply(
            lambda x: classif_gordura(
                x.get('Gordura_Corporal_%'), x.get('Idade')
            ), axis=1
        )
        df['Estado_Fisico'] = df.apply(
            lambda row: estado_fisico(
                row.get('Classificacao_IMC'),
                row.get('Classificacao_Gordura')
            ), axis=1
        )

        def cat_pos(pos_str):
            if pd.isna(pos_str):
                return 'Outros'
            pos = str(pos_str).upper().strip()
            if 'GOLEIRO' in pos: return 'Goleiro'
            if 'ZAGUEIRO' in pos: return 'Zagueiro'
            if 'LATERAL DIREITO' in pos or 'LAT. DIREITO' in pos:
                return 'Lateral Direito'
            if 'LATERAL ESQUERDO' in pos or 'LAT. ESQUERDO' in pos:
                return 'Lateral Esquerdo'
            if 'LATERAL' in pos: return 'Lateral'
            if 'VOLANTE' in pos: return 'Volante'
            if 'MEIA-CENTRAL' in pos or 'MEIA CENTRAL' in pos:
                return 'Meia-Central'
            if 'MEIA-ATACANTE' in pos or 'MEIA ATACANTE' in pos:
                return 'Meia-Atacante'
            if 'MEIA' in pos or 'MEIO' in pos: return 'Meia'
            if 'PONTA DIREITA' in pos: return 'Ponta Direita'
            if 'PONTA ESQUERDA' in pos: return 'Ponta Esquerda'
            if 'PONTA' in pos: return 'Ponta'
            if 'CENTROAVANTE' in pos: return 'Centroavante'
            if 'SEGUNDO ATACANTE' in pos: return 'Segundo Atacante'
            if 'ATACANTE' in pos: return 'Atacante'
            return 'Outros'

        df['Posicao_Principal'] = df['posicao'].apply(cat_pos)

        def calc_rating(valor):
            if pd.notna(valor):
                try:
                    return min(100, float(valor) / 2)
                except (TypeError, ValueError):
                    return 50
            return 50

        if 'habilidade_atual' in df.columns:
            df['Rating_Geral_FM26'] = df['habilidade_atual'].apply(calc_rating)
        else:
            df['Rating_Geral_FM26'] = 50

        df['atributos_fm26'] = df.apply(agrupar_atributos_jogador, axis=1)
        df = df[df['nome_completo'].notna()]

        print(f"✅ Elenco {categoria} carregado com {len(df)} jogadores.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar {categoria}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# CARREGAMENTO DA COMISSÃO
# ============================================================================

def carregar_dados_comissao(categoria):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return None

    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig', dtype=str)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        if 'nome_completo' not in df.columns:
            df['nome_completo'] = ''
        df['nome_completo'] = df['nome_completo'].fillna('').astype(str).str.strip()

        if 'apelido' in df.columns:
            df['nome'] = df['apelido'].fillna('').astype(str).str.strip()
        else:
            df['nome'] = df['nome_completo']

        df['nome_completo'] = df.apply(
            lambda r: r['nome_completo'] if r['nome_completo'] else r['nome'],
            axis=1,
        )
        df['nome'] = df.apply(
            lambda r: r['nome'] if r['nome'] else r['nome_completo'], axis=1
        )

        if 'cargo' not in df.columns:
            df['cargo'] = 'Técnico'

        if 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(
                lambda x: calcular_idade(x) if pd.notna(x) else None
            )
        else:
            df['idade'] = None

        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)

        estatisticas = {
            'jogos_temporada': 'jogos_temporada',
            'cartoes_amarelos_totais': 'cartoes_amarelos_totais',
            'cartoes_vermelhos_totais': 'cartoes_vermelhos_totais',
            'media_cartoes_amarelos': 'media_cartoes_amarelos',
            'media_cartoes_vermelhos': 'media_cartoes_vermelhos',
        }
        for col, original in estatisticas.items():
            if original in df.columns:
                df[col] = pd.to_numeric(
                    df[original].str.replace(',', '.'), errors='coerce'
                )
                if 'jogos' in col or 'cartoes' in col:
                    df[col] = df[col].fillna(0).astype(int)
            else:
                df[col] = 0

        df['atributos_fm26'] = df.apply(agrupar_atributos_comissao, axis=1)

        print(f"✅ Comissão {categoria} carregada com {len(df)} membros.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar comissão {categoria}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# CARREGAMENTO DA DIRETORIA
# ============================================================================

def carregar_dados_diretoria(categoria='diretoria'):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        print(f"Arquivo da diretoria não encontrado: {caminho}")
        return None

    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig', dtype=str)
        df.columns = (
            df.columns
            .str.replace('\ufeff', '', regex=False)
            .str.strip()
            .str.lower()
            .str.replace(' ', '_')
        )

        if 'nome_completo' not in df.columns:
            df['nome_completo'] = ''
        df['nome_completo'] = df['nome_completo'].fillna('').astype(str).str.strip()

        if 'apelido' in df.columns:
            df['nome'] = df['apelido'].fillna('').astype(str).str.strip()
        else:
            df['nome'] = df['nome_completo']

        df['nome_completo'] = df.apply(
            lambda r: r['nome_completo'] if r['nome_completo'] else r['nome'],
            axis=1,
        )
        df['nome'] = df.apply(
            lambda r: r['nome'] if r['nome'] else r['nome_completo'], axis=1
        )

        if 'cargo' not in df.columns:
            df['cargo'] = 'Diretor'

        if 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(
                lambda x: calcular_idade(x) if pd.notna(x) else None
            )
        elif 'idade' in df.columns:
            df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
        else:
            df['idade'] = None

        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)

        for col in [
            'jogos_temporada', 'cartoes_amarelos_totais',
            'cartoes_vermelhos_totais', 'media_cartoes_amarelos',
            'media_cartoes_vermelhos'
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].str.replace(',', '.'), errors='coerce'
                )
                if 'jogos' in col or 'cartoes' in col:
                    df[col] = df[col].fillna(0).astype(int)
            else:
                df[col] = 0

        df['atributos_fm26'] = df.apply(agrupar_atributos_diretoria, axis=1)

        print(f"✅ Diretoria carregada com {len(df)} membros.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar diretoria: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# AGRUPAMENTO - JOGADORES (retorna APENAS classificação)
# ============================================================================

def agrupar_atributos_jogador(row):
    """Agrupa atributos do jogador retornando APENAS a classificação."""
    atributos = {}

    tecnicos = [
        'escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
        'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
        'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica',
    ]
    atributos['tecnicos'] = {
        a: classificar(row.get(a), "habilidade") for a in tecnicos
        if a in row and pd.notna(row.get(a))
    }

    mentais = [
        'agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
        'decisao', 'determinacao', 'criatividade', 'lideranca',
        'movimentacao_sem_bola', 'posicionamento', 'trabalho_equipe',
        'visao_jogo', 'intensidade_trabalho',
    ]
    atributos['mentais'] = {
        a: classificar(row.get(a), "habilidade") for a in mentais
        if a in row and pd.notna(row.get(a))
    }

    fisicos = [
        'aceleracao', 'agilidade', 'equilibrio', 'altura_salto',
        'condicao_fisica_natural', 'velocidade_maxima', 'resistencia',
        'forca_fisica',
    ]
    atributos['fisicos'] = {
        a: classificar(row.get(a), "habilidade") for a in fisicos
        if a in row and pd.notna(row.get(a))
    }

    goleiro = [
        'reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro', 'comando_area',
        'comunicacao_goleiro', 'chutes_goleiro', 'um_contra_um_goleiro',
        'saida_gol', 'tendencia_socar', 'arremessos_goleiro', 'excentricidade',
    ]
    atributos['goleiro'] = {
        a: classificar(row.get(a), "habilidade") for a in goleiro
        if a in row and pd.notna(row.get(a))
    }

    ocultos = [
        'consistencia', 'jogo_sujo', 'jogos_importantes',
        'propensao_lesao', 'versatilidade',
    ]
    atributos['ocultos'] = {
        a: classificar(row.get(a), "habilidade") for a in ocultos
        if a in row and pd.notna(row.get(a))
    }

    personalidade = [
        'adaptabilidade', 'ambicao', 'lealdade', 'pressao',
        'profissionalismo', 'esportividade', 'temperamento', 'controversia',
    ]
    atributos['personalidade'] = {
        a: classificar(row.get(a), "habilidade") for a in personalidade
        if a in row and pd.notna(row.get(a))
    }

    return atributos


# ============================================================================
# AGRUPAMENTO - COMISSÃO (retorna APENAS classificação)
# ============================================================================

def agrupar_atributos_comissao(row):
    """Agrupa atributos da comissão retornando APENAS a classificação.
    CA/PA → ca_pa | Reputação → reputacao | Outros → habilidade
    """
    atributos = {}

    # ---- Gerais ----
    atributos['gerais'] = {}

    if 'ca' in row and pd.notna(row.get('ca')):
        atributos['gerais']['CA'] = classificar(row.get('ca'), "ca_pa")
    if 'pa' in row and pd.notna(row.get('pa')):
        atributos['gerais']['PA'] = classificar(row.get('pa'), "ca_pa")

    # Reputação
    if 'reputacao_mundial' in row and pd.notna(row.get('reputacao_mundial')):
        atributos['gerais']['Reputação Mundial'] = classificar(
            row.get('reputacao_mundial'), "reputacao"
        )
    if 'reputacao_atual' in row and pd.notna(row.get('reputacao_atual')):
        atributos['gerais']['Reputação Atual'] = classificar(
            row.get('reputacao_atual'), "reputacao"
        )
    if 'reputacao_local' in row and pd.notna(row.get('reputacao_local')):
        atributos['gerais']['Reputação Local'] = classificar(
            row.get('reputacao_local'), "reputacao"
        )

    # Outros gerais
    outros_gerais = ['qualificacoes_treinador', 'jogos_selecao', 'gols_selecao']
    for a in outros_gerais:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['gerais'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Treinamento ----
    coaching = [
        'coachingattributes_attacking', 'coachingattributes_defending',
        'coachingattributes_fitness', 'coachingattributes_goalkeeping',
        'coachingattributes_possession', 'coachingattributes_player',
        'coachingattributes_tactical', 'coachingattributes_technical',
        'coachingattributes_peoplemanagement',
        'coachingattributes_workingwithyoungsters',
        'coachingattributes_dirtinessallowance',
        'coachingattributes_versatility', 'coachingattributes_setpieces',
    ]
    atributos['treinamento'] = {}
    for a in coaching:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('coachingattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['treinamento'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Staff Mental ----
    staff_mental = [
        'staffmentalattributes_adaptability',
        'staffmentalattributes_determination',
        'staffmentalattributes_judgingplayerability',
        'staffmentalattributes_judgingplayerpotential',
        'staffmentalattributes_judgingstaffability',
        'staffmentalattributes_negotiating',
        'staffmentalattributes_authority',
        'staffmentalattributes_motivating',
        'staffmentalattributes_physiotherapy',
        'staffmentalattributes_tacticalknowledge',
    ]
    atributos['staff_mental'] = {}
    for a in staff_mental:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('staffmentalattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['staff_mental'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Táticas ----
    taticas = [
        'tacticalattributes_attacking', 'tacticalattributes_depth',
        'tacticalattributes_directness', 'tacticalattributes_flamboyancy',
        'tacticalattributes_flexibility', 'tacticalattributes_freeroles',
        'tacticalattributes_marking', 'tacticalattributes_offside',
        'tacticalattributes_pressing', 'tacticalattributes_sittingback',
        'tacticalattributes_tempo', 'tacticalattributes_useofplaymaker',
        'tacticalattributes_useofsubstitutions', 'tacticalattributes_width',
    ]
    atributos['taticas'] = {}
    for a in taticas:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('tacticalattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['taticas'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Scouting ----
    scouting = [
        'scoutingattributes_judgingplayerdata',
        'scoutingattributes_judgingteamdata',
        'scoutingattributes_presentingdata',
    ]
    atributos['scouting'] = {}
    for a in scouting:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('scoutingattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['scouting'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Médica ----
    if 'medicalattributes_sportsscience' in row and pd.notna(
        row.get('medicalattributes_sportsscience')
    ):
        chave = TRADUCAO_ATRIBUTOS_COMISSAO.get('Sports Science', 'Sports Science')
        atributos['medica'] = {
            chave: classificar(row.get('medicalattributes_sportsscience'), "habilidade")
        }

    # ---- Personalidade ----
    personalidade = [
        'personalityattributes_adaptability', 'personalityattributes_ambition',
        'personalityattributes_loyalty', 'personalityattributes_pressure',
        'personalityattributes_professional', 'personalityattributes_sportsmanship',
        'personalityattributes_temperament', 'personalityattributes_controversy',
    ]
    atributos['personalidade'] = {}
    for a in personalidade:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('personalityattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['personalidade'][chave_t] = classificar(row.get(a), "habilidade")

    # ---- Funções ----
    roles = [
        'rolesattributes_assistantmanager', 'rolesattributes_coach',
        'rolesattributes_fitnesscoach', 'rolesattributes_goalkeepingcoach',
        'rolesattributes_manager', 'rolesattributes_physio',
        'rolesattributes_scout', 'rolesattributes_chairman',
        'rolesattributes_directoroffootball',
        'rolesattributes_headofyouthdevelopment',
        'rolesattributes_dataanalyst', 'rolesattributes_sportsscientist',
        'rolesattributes_loanmanager', 'rolesattributes_technicaldirector',
        'rolesattributes_setpiececoach',
    ]
    atributos['funcoes'] = {}
    for a in roles:
        if a in row and pd.notna(row.get(a)):
            chave = a.replace('rolesattributes_', '').replace('_', ' ').title()
            chave_t = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave, chave)
            atributos['funcoes'][chave_t] = classificar(row.get(a), "habilidade")

    return {k: v for k, v in atributos.items() if v}


# ============================================================================
# AGRUPAMENTO - DIRETORIA (retorna APENAS classificação)
# ============================================================================

def agrupar_atributos_diretoria(row):
    """Agrupa atributos da diretoria retornando APENAS a classificação.
    CA/PA → ca_pa | Reputação → reputacao | Outros → habilidade
    """
    atributos = {}

    # ---- Gerais ----
    atributos['gerais'] = {}

    if 'ca_diretoria' in row and pd.notna(row.get('ca_diretoria')):
        atributos['gerais']['CA'] = classificar(row.get('ca_diretoria'), "ca_pa")
    if 'pa_diretoria' in row and pd.notna(row.get('pa_diretoria')):
        atributos['gerais']['PA'] = classificar(row.get('pa_diretoria'), "ca_pa")

    # Reputação
    if 'reputacao_mundial' in row and pd.notna(row.get('reputacao_mundial')):
        atributos['gerais']['Reputação Mundial'] = classificar(
            row.get('reputacao_mundial'), "reputacao"
        )
    if 'reputacao_atual' in row and pd.notna(row.get('reputacao_atual')):
        atributos['gerais']['Reputação Atual'] = classificar(
            row.get('reputacao_atual'), "reputacao"
        )
    if 'reputacao_local' in row and pd.notna(row.get('reputacao_local')):
        atributos['gerais']['Reputação Local'] = classificar(
            row.get('reputacao_local'), "reputacao"
        )

    # ---- Presidência ----
    presidencia = {
        'habilidade_negocios': 'Habilidade de Negócios',
        'interferencia': 'Interferência',
        'paciencia_diretoria': 'Paciência',
        'recursos_financeiros': 'Recursos Financeiros',
    }
    atributos['presidencia'] = {}
    for col, label in presidencia.items():
        if col in row and pd.notna(row.get(col)):
            atributos['presidencia'][label] = classificar(row.get(col), "habilidade")

    # ---- Não-Táticos ----
    nao_taticos = {
        'compra_jogadores': 'Compra de Jogadores',
        'intensidade_treino': 'Intensidade do Treino',
        'jogos_mentais': 'Jogos Mentais',
        'rotacao_elenco': 'Rotação do Elenco',
    }
    atributos['nao_taticos'] = {}
    for col, label in nao_taticos.items():
        if col in row and pd.notna(row.get(col)):
            atributos['nao_taticos'][label] = classificar(row.get(col), "habilidade")

    # ---- Staff Mental ----
    staff_mental = {
        'adaptabilidade': 'Adaptabilidade',
        'determinacao': 'Determinação',
        'julgamento_jogador': 'Julgamento de Jogador',
        'julgamento_potencial': 'Julgamento de Potencial',
        'julgamento_staff': 'Julgamento de Staff',
        'negociacao': 'Negociação',
        'autoridade': 'Autoridade',
        'motivacao': 'Motivação',
        'conhecimento_tatico': 'Conhecimento Tático',
    }
    atributos['staff_mental'] = {}
    for col, label in staff_mental.items():
        if col in row and pd.notna(row.get(col)):
            atributos['staff_mental'][label] = classificar(row.get(col), "habilidade")

    # ---- Scouting ----
    scouting = {
        'analise_dados_jogador': 'Análise de Dados de Jogador',
        'analise_dados_time': 'Análise de Dados de Time',
        'apresentacao_dados': 'Apresentação de Dados',
    }
    atributos['scouting'] = {}
    for col, label in scouting.items():
        if col in row and pd.notna(row.get(col)):
            atributos['scouting'][label] = classificar(row.get(col), "habilidade")

    # ---- Treinamento ----
    treinamento = {
        'gestao_pessoas': 'Gestão de Pessoas',
        'trabalho_jovens': 'Trabalho com Jovens',
        'bolas_paradas': 'Bolas Paradas',
        'tolerancia_sujeira': 'Tolerância à Sujeira',
        'versatilidade': 'Versatilidade',
    }
    atributos['treinamento'] = {}
    for col, label in treinamento.items():
        if col in row and pd.notna(row.get(col)):
            atributos['treinamento'][label] = classificar(row.get(col), "habilidade")

    # ---- Personalidade ----
    personalidade = {
        'ambicao': 'Ambição',
        'lealdade': 'Lealdade',
        'pressao': 'Pressão',
        'profissionalismo': 'Profissionalismo',
        'esportividade': 'Espírito Esportivo',
        'temperamento': 'Temperamento',
        'controversia': 'Controvérsia',
        'personalidade': 'Personalidade',
    }
    atributos['personalidade'] = {}
    for col, label in personalidade.items():
        if col in row and pd.notna(row.get(col)):
            atributos['personalidade'][label] = classificar(row.get(col), "habilidade")

    # ---- Informações ----
    info = {
        'nacionalidade': 'Nacionalidade',
        'clube': 'Clube',
        'divisao': 'Divisão',
        'no_clube_desde': 'No Clube Desde',
        'fmrte_id': 'FMRTE ID',
        'historico_profissional': 'Histórico Profissional',
    }
    atributos['informacoes'] = {}
    for col, label in info.items():
        if (col in row and pd.notna(row.get(col))
                and str(row.get(col)).strip()):
            atributos['informacoes'][label] = row.get(col)

    return {k: v for k, v in atributos.items() if v}


# ============================================================================
# LESÕES
# ============================================================================

def carregar_lesoes(categoria):
    caminho = Config.ARQUIVOS_LESOES.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return {}

    try:
        df = pd.read_csv(caminho, delimiter=';', encoding='utf-8-sig', dtype=str)
        lesionados = {}

        for _, row in df.iterrows():
            nome = row.get('nome_completo')
            ogol_id = row.get('ogol_id')
            tem_lesao = False

            colunas_lesoes = [c for c in df.columns if c.startswith('Lesao_')]
            for col in colunas_lesoes:
                valor = row.get(col, '')
                if pd.notna(valor) and str(valor).strip():
                    ocorrencias = str(valor).split(',')
                    ultima = ocorrencias[-1].strip().rstrip(';').strip()
                    separadores = [' / ', ' - ', '–', ' a ']
                    tem_intervalo = any(sep in ultima for sep in separadores)
                    if not tem_intervalo:
                        tem_lesao = True
                        break

            if tem_lesao:
                if ogol_id and pd.notna(ogol_id):
                    try:
                        lesionados[int(float(ogol_id))] = True
                    except:
                        pass
                if nome:
                    lesionados[nome] = True

        return lesionados

    except Exception as e:
        print(f"❌ Erro ao carregar lesões {categoria}: {e}")
        return {}


def adicionar_lesao(csv_path, nome_jogador, tipo_lesao, data_inicio, data_fim=None):
    if not os.path.exists(csv_path):
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return False

    try:
        df = pd.read_csv(
            csv_path, delimiter=';', encoding='utf-8-sig', dtype=str,
            on_bad_lines='skip',
        )
    except Exception as e:
        print(f"❌ Erro ao ler {csv_path}: {e}")
        return False

    if 'nome_completo' not in df.columns:
        print(f"❌ Coluna 'nome_completo' não encontrada em {csv_path}")
        return False

    coluna_lesao = f"Lesao_{tipo_lesao.replace(' ', '_').title()}"
    if coluna_lesao not in df.columns:
        df[coluna_lesao] = ''

    match = df[df['nome_completo'] == nome_jogador]
    if match.empty:
        print(f"⚠️  Jogador '{nome_jogador}' não encontrado no CSV.")
        return False

    idx = match.index[0]
    nova_ocorrencia = f"{data_inicio} - {data_fim}" if data_fim else data_inicio

    valor_atual = df.at[idx, coluna_lesao]
    if pd.isna(valor_atual) or str(valor_atual).strip() == '':
        df.at[idx, coluna_lesao] = nova_ocorrencia
    else:
        df.at[idx, coluna_lesao] = f"{valor_atual}, {nova_ocorrencia}"

    try:
        df.to_csv(csv_path, sep=';', encoding='utf-8-sig', index=False)
        print(f"✅ Lesão registrada: {nome_jogador} - {tipo_lesao} - {nova_ocorrencia}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar {csv_path}: {e}")
        return False


def adicionar_lesao_com_data_fim(csv_path, nome_jogador, tipo_lesao, data_fim):
    if not os.path.exists(csv_path):
        return False

    try:
        df = pd.read_csv(
            csv_path, delimiter=';', encoding='utf-8-sig', dtype=str,
            on_bad_lines='skip',
        )
    except Exception as e:
        print(f"❌ Erro ao ler {csv_path}: {e}")
        return False

    coluna_lesao = f"Lesao_{tipo_lesao.replace(' ', '_').title()}"
    if coluna_lesao not in df.columns:
        return False

    match = df[df['nome_completo'] == nome_jogador]
    if match.empty:
        return False

    idx = match.index[0]
    valor = df.at[idx, coluna_lesao]
    if pd.isna(valor) or str(valor).strip() == '':
        return False

    ocorrencias = [o.strip() for o in str(valor).split(',')]
    ultima = ocorrencias[-1]

    if ' - ' in ultima or '–' in ultima:
        return False

    ocorrencias[-1] = f"{ultima} - {data_fim}"
    df.at[idx, coluna_lesao] = ', '.join(ocorrencias)

    try:
        df.to_csv(csv_path, sep=';', encoding='utf-8-sig', index=False)
        print(f"✅ Lesão encerrada: {nome_jogador} - {tipo_lesao} - Fim: {data_fim}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar {csv_path}: {e}")
        return False


# ============================================================================
# BIOIMPEDÂNCIA
# ============================================================================

def carregar_bioimpedancia(categoria):
    caminho = Config.ARQUIVOS_BIO.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return {}

    try:
        df = pd.read_csv(caminho, delimiter=';', encoding='utf-8-sig', dtype=str)
        dados = {}

        for _, row in df.iterrows():
            nome = row.get('nome_completo')
            if not nome:
                continue

            def parse(val):
                if pd.isna(val):
                    return None
                return safe_float(val)

            altura_cm = parse(row.get('altura_cm'))
            dados[nome] = {
                'peso': parse(row.get('peso_kg')),
                'altura': altura_cm / 100.0 if altura_cm is not None else None,
                'gordura': parse(row.get('gordura_corporal')),
                'massa_magra': parse(row.get('massa_magra')),
                'massa_muscular': parse(row.get('massa_muscular')),
                'data_coleta': row.get('data_bioimpedancia'),
            }

        return dados

    except Exception as e:
        print(f"❌ Erro ao carregar bioimpedância {categoria}: {e}")
        return {}