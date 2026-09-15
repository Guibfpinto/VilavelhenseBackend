# services/dados.py - Versão final com CSV real da Diretoria

import os
import pandas as pd
import numpy as np
from config import Config
from utils.datas import calcular_idade
from services.bioimpedancia import classif_imc, classif_gordura, estado_fisico
from services.cartoes_service import mapear_nome_para_canonico

# ============================================================================
# TRADUÇÃO DE ATRIBUTOS DE STAFF (COMISSÃO)
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
# TRADUÇÃO DE ATRIBUTOS DA DIRETORIA (COLUNAS DO CSV REAL)
# ============================================================================

TRADUCAO_ATRIBUTOS_DIRETORIA = {
    # Gerais
    'ca_diretoria': 'CA',
    'pa_diretoria': 'PA',
    'reputacao_mundial': 'Reputação Mundial',
    'reputacao_atual': 'Reputação Atual',
    'reputacao_local': 'Reputação Local',
    # Presidência
    'habilidade_negocios': 'Habilidade de Negócios',
    'interferencia': 'Interferência',
    'paciencia_diretoria': 'Paciência',
    'recursos_financeiros': 'Recursos Financeiros',
    # Não-Táticos
    'compra_jogadores': 'Compra de Jogadores',
    'intensidade_treino': 'Intensidade do Treino',
    'jogos_mentais': 'Jogos Mentais',
    'rotacao_elenco': 'Rotação do Elenco',
    # Staff Mental
    'adaptabilidade': 'Adaptabilidade',
    'determinacao': 'Determinação',
    'julgamento_jogador': 'Julgamento de Jogador',
    'julgamento_potencial': 'Julgamento de Potencial',
    'julgamento_staff': 'Julgamento de Staff',
    'negociacao': 'Negociação',
    'autoridade': 'Autoridade',
    'motivacao': 'Motivação',
    'conhecimento_tatico': 'Conhecimento Tático',
    # Scouting / Análise
    'analise_dados_jogador': 'Análise de Dados de Jogador',
    'analise_dados_time': 'Análise de Dados de Time',
    'apresentacao_dados': 'Apresentação de Dados',
    # Treinamento
    'gestao_pessoas': 'Gestão de Pessoas',
    'trabalho_jovens': 'Trabalho com Jovens',
    'bolas_paradas': 'Bolas Paradas',
    'tolerancia_sujeira': 'Tolerância à Sujeira',
    'versatilidade': 'Versatilidade',
    # Personalidade
    'ambicao': 'Ambição',
    'lealdade': 'Lealdade',
    'pressao': 'Pressão',
    'profissionalismo': 'Profissionalismo',
    'esportividade': 'Espírito Esportivo',
    'temperamento': 'Temperamento',
    'controversia': 'Controvérsia',
    'personalidade': 'Personalidade',
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
    return pd.to_numeric(
        serie.astype(str).str.replace(',', '.').str.replace('', '0'),
        errors='coerce'
    )


# ============================================================================
# CARREGAMENTO DE JOGADORES
# ============================================================================

def carregar_dados_elenco(categoria):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        return None

    try:
        df_raw = pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig', header=None)
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
            nome_original = cabecalhos_originais[i] if i < len(cabecalhos_originais) else f'col_{i}'
            nome_normalizado = str(nome_original).strip().replace('\ufeff', '').replace(' ', '_').lower()
            df.rename(columns={i: nome_normalizado}, inplace=True)

        colunas_numericas = ['altura_cm', 'peso_kg', 'habilidade_atual', 'habilidade_potencial']
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = parse_numero_coluna(df[col])

        for attr in Config.ATRIBUTOS_FM26_JOGADORES:
            if attr in df.columns:
                df[attr] = parse_numero_coluna(df[attr])
                if df[attr].notna().any():
                    max_val = df[attr].max()
                    if max_val > 100:
                        df[attr] = df[attr] / 100.0
                    elif max_val > 20:
                        df[attr] = df[attr] / 5.0

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
            if altura is None or peso is None or pd.isna(altura) or pd.isna(peso) or altura <= 0:
                return np.nan
            return round(peso / ((altura / 100) ** 2), 1)

        df['IMC'] = df.apply(calc_imc, axis=1)
        df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)
        df['Idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else None)

        def calc_gordura(row):
            imc = row.get('IMC'); idade = row.get('Idade')
            if imc is None or idade is None or pd.isna(imc) or pd.isna(idade):
                return np.nan
            return round((1.20 * imc) + (0.23 * idade) - 16.2, 1)

        df['Gordura_Corporal_%'] = df.apply(calc_gordura, axis=1)

        def calc_massa_magra(row):
            peso = row.get('peso_kg'); gordura = row.get('Gordura_Corporal_%')
            if peso is None or gordura is None or pd.isna(peso) or pd.isna(gordura):
                return np.nan
            return round(peso * (1 - gordura / 100), 1)

        df['Massa_Magra_kg'] = df.apply(calc_massa_magra, axis=1)

        def calc_massa_muscular(row):
            mm = row.get('Massa_Magra_kg')
            if mm is None or pd.isna(mm):
                return np.nan
            return round(mm * 0.55, 1)

        df['Massa_Muscular_Estimada_kg'] = df.apply(calc_massa_muscular, axis=1)

        df['Classificacao_Gordura'] = df.apply(
            lambda x: classif_gordura(x.get('Gordura_Corporal_%'), x.get('Idade')), axis=1
        )
        df['Estado_Fisico'] = df.apply(
            lambda row: estado_fisico(row.get('Classificacao_IMC'), row.get('Classificacao_Gordura')), axis=1
        )

        def cat_pos(pos_str):
            if pd.isna(pos_str): return 'Outros'
            pos = str(pos_str).upper().strip()
            if 'GOLEIRO' in pos: return 'Goleiro'
            if 'ZAGUEIRO' in pos: return 'Zagueiro'
            if 'LATERAL DIREITO' in pos or 'LAT. DIREITO' in pos: return 'Lateral Direito'
            if 'LATERAL ESQUERDO' in pos or 'LAT. ESQUERDO' in pos: return 'Lateral Esquerdo'
            if 'LATERAL' in pos: return 'Lateral'
            if 'VOLANTE' in pos: return 'Volante'
            if 'MEIA-CENTRAL' in pos or 'MEIA CENTRAL' in pos: return 'Meia-Central'
            if 'MEIA-ATACANTE' in pos or 'MEIA ATACANTE' in pos: return 'Meia-Atacante'
            if 'MEIA' in pos or 'MEIO' in pos: return 'Meia'
            if 'PONTA DIREITA' in pos: return 'Ponta Direita'
            if 'PONTA ESQUERDA' in pos: return 'Ponta Esquerda'
            if 'PONTA' in pos: return 'Ponta'
            if 'CENTROAVANTE' in pos: return 'Centroavante'
            if 'SEGUNDO ATACANTE' in pos: return 'Segundo Atacante'
            if 'ATACANTE' in pos: return 'Atacante'
            return 'Outros'

        df['Posicao_Principal'] = df['posicao'].apply(cat_pos)

        if 'habilidade_atual' in df.columns:
            df['Rating_Geral_FM26'] = df['habilidade_atual'].apply(
                lambda x: min(100, x/2) if pd.notna(x) else 50
            )
        else:
            df['Rating_Geral_FM26'] = 50

        df['atributos_fm26'] = df.apply(agrupar_atributos_jogador, axis=1)
        df = df[df['nome_completo'].notna()]

        print(f"✅ Elenco {categoria} carregado com {len(df)} jogadores.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar {categoria}: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================================
# CARREGAMENTO DA COMISSÃO TÉCNICA
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
            lambda r: r['nome_completo'] if r['nome_completo'] else r['nome'], axis=1
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
            'media_cartoes_vermelhos': 'media_cartoes_vermelhos'
        }
        for col, original in estatisticas.items():
            if original in df.columns:
                df[col] = pd.to_numeric(df[original].str.replace(',', '.'), errors='coerce')
                if 'jogos' in col or 'cartoes' in col:
                    df[col] = df[col].fillna(0).astype(int)
            else:
                df[col] = 0

        df['atributos_fm26'] = df.apply(agrupar_atributos_comissao, axis=1)

        print(f"✅ Comissão {categoria} carregada com {len(df)} membros.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar comissão {categoria}: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================================
# CARREGAMENTO DA DIRETORIA (AJUSTADO AO CSV REAL)
# ============================================================================

def carregar_dados_diretoria(categoria='diretoria'):
    """Carrega CSV da diretoria com as colunas em português."""
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        print(f"Arquivo da diretoria não encontrado: {caminho}")
        return None

    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig', dtype=str)
        # Normaliza nomes de colunas (remove BOM, espaços, deixa minúsculo)
        df.columns = (
            df.columns
            .str.replace('\ufeff', '', regex=False)
            .str.strip()
            .str.lower()
            .str.replace(' ', '_')
        )

        # ===== NOME E APELIDO =====
        if 'nome_completo' not in df.columns:
            df['nome_completo'] = ''
        df['nome_completo'] = df['nome_completo'].fillna('').astype(str).str.strip()

        if 'apelido' in df.columns:
            df['nome'] = df['apelido'].fillna('').astype(str).str.strip()
        else:
            df['nome'] = df['nome_completo']

        df['nome_completo'] = df.apply(
            lambda r: r['nome_completo'] if r['nome_completo'] else r['nome'], axis=1
        )
        df['nome'] = df.apply(
            lambda r: r['nome'] if r['nome'] else r['nome_completo'], axis=1
        )

        # ===== CARGO =====
        if 'cargo' not in df.columns:
            df['cargo'] = 'Diretor'

        # ===== IDADE =====
        if 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(
                lambda x: calcular_idade(x) if pd.notna(x) else None
            )
        elif 'idade' in df.columns:
            df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
        else:
            df['idade'] = None

        # ===== NOME CANÔNICO =====
        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)

        # ===== ESTATÍSTICAS (não existem no CSV, mas garantimos 0) =====
        for col in ['jogos_temporada', 'cartoes_amarelos_totais', 'cartoes_vermelhos_totais',
                    'media_cartoes_amarelos', 'media_cartoes_vermelhos']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
                if 'jogos' in col or 'cartoes' in col:
                    df[col] = df[col].fillna(0).astype(int)
            else:
                df[col] = 0

        # ===== ATRIBUTOS =====
        df['atributos_fm26'] = df.apply(agrupar_atributos_diretoria, axis=1)

        print(f"✅ Diretoria carregada com {len(df)} membros.")
        return df

    except Exception as e:
        print(f"❌ Erro ao carregar diretoria: {e}")
        import traceback; traceback.print_exc()
        return None


# ============================================================================
# AGRUPAMENTO DE ATRIBUTOS - JOGADORES
# ============================================================================

def agrupar_atributos_jogador(row):
    atributos = {}
    tecnicos = ['escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
                'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
                'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica']
    atributos['tecnicos'] = {a: row.get(a) for a in tecnicos if a in row and pd.notna(row.get(a))}

    mentais = ['agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
               'decisao', 'determinacao', 'criatividade', 'lideranca', 'movimentacao_sem_bola',
               'posicionamento', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho']
    atributos['mentais'] = {a: row.get(a) for a in mentais if a in row and pd.notna(row.get(a))}

    fisicos = ['aceleracao', 'agilidade', 'equilibrio', 'altura_salto', 'condicao_fisica_natural',
               'velocidade_maxima', 'resistencia', 'forca_fisica']
    atributos['fisicos'] = {a: row.get(a) for a in fisicos if a in row and pd.notna(row.get(a))}

    goleiro = ['reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro', 'comando_area',
               'comunicacao_goleiro', 'chutes_goleiro', 'um_contra_um_goleiro', 'saida_gol',
               'tendencia_socar', 'arremessos_goleiro', 'excentricidade']
    atributos['goleiro'] = {a: row.get(a) for a in goleiro if a in row and pd.notna(row.get(a))}

    ocultos = ['consistencia', 'jogo_sujo', 'jogos_importantes', 'propensao_lesao', 'versatilidade']
    atributos['ocultos'] = {a: row.get(a) for a in ocultos if a in row and pd.notna(row.get(a))}

    personalidade = ['adaptabilidade', 'ambicao', 'lealdade', 'pressao', 'profissionalismo',
                     'esportividade', 'temperamento', 'controversia']
    atributos['personalidade'] = {a: row.get(a) for a in personalidade if a in row and pd.notna(row.get(a))}

    return atributos


# ============================================================================
# AGRUPAMENTO DE ATRIBUTOS - COMISSÃO
# ============================================================================

def agrupar_atributos_comissao(row):
    atributos = {}

    gerais = ['ca', 'pa', 'reputacao_mundial', 'reputacao_atual', 'reputacao_local',
              'qualificacoes_treinador', 'jogos_selecao', 'gols_selecao']
    atributos['gerais'] = {}
    for a in gerais:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.upper() if a in ['ca', 'pa'] else a.replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['gerais'][chave_traduzida] = row.get(a)

    coaching = ['coachingattributes_attacking', 'coachingattributes_defending',
                'coachingattributes_fitness', 'coachingattributes_goalkeeping',
                'coachingattributes_possession', 'coachingattributes_player',
                'coachingattributes_tactical', 'coachingattributes_technical',
                'coachingattributes_peoplemanagement', 'coachingattributes_workingwithyoungsters',
                'coachingattributes_dirtinessallowance', 'coachingattributes_versatility',
                'coachingattributes_setpieces']
    atributos['treinamento'] = {}
    for a in coaching:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('coachingattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['treinamento'][chave_traduzida] = row.get(a)

    staff_mental = ['staffmentalattributes_adaptability', 'staffmentalattributes_determination',
                    'staffmentalattributes_judgingplayerability', 'staffmentalattributes_judgingplayerpotential',
                    'staffmentalattributes_judgingstaffability', 'staffmentalattributes_negotiating',
                    'staffmentalattributes_authority', 'staffmentalattributes_motivating',
                    'staffmentalattributes_physiotherapy', 'staffmentalattributes_tacticalknowledge']
    atributos['staff_mental'] = {}
    for a in staff_mental:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('staffmentalattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['staff_mental'][chave_traduzida] = row.get(a)

    taticas = ['tacticalattributes_attacking', 'tacticalattributes_depth',
               'tacticalattributes_directness', 'tacticalattributes_flamboyancy',
               'tacticalattributes_flexibility', 'tacticalattributes_freeroles',
               'tacticalattributes_marking', 'tacticalattributes_offside',
               'tacticalattributes_pressing', 'tacticalattributes_sittingback',
               'tacticalattributes_tempo', 'tacticalattributes_useofplaymaker',
               'tacticalattributes_useofsubstitutions', 'tacticalattributes_width']
    atributos['taticas'] = {}
    for a in taticas:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('tacticalattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['taticas'][chave_traduzida] = row.get(a)

    scouting = ['scoutingattributes_judgingplayerdata', 'scoutingattributes_judgingteamdata',
                'scoutingattributes_presentingdata']
    atributos['scouting'] = {}
    for a in scouting:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('scoutingattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['scouting'][chave_traduzida] = row.get(a)

    if 'medicalattributes_sportsscience' in row and pd.notna(row.get('medicalattributes_sportsscience')):
        chave = TRADUCAO_ATRIBUTOS_COMISSAO.get('Sports Science', 'Sports Science')
        atributos['medica'] = {chave: row.get('medicalattributes_sportsscience')}

    personalidade = ['personalityattributes_adaptability', 'personalityattributes_ambition',
                     'personalityattributes_loyalty', 'personalityattributes_pressure',
                     'personalityattributes_professional', 'personalityattributes_sportsmanship',
                     'personalityattributes_temperament', 'personalityattributes_controversy']
    atributos['personalidade'] = {}
    for a in personalidade:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('personalityattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['personalidade'][chave_traduzida] = row.get(a)

    roles = ['rolesattributes_assistantmanager', 'rolesattributes_coach',
             'rolesattributes_fitnesscoach', 'rolesattributes_goalkeepingcoach',
             'rolesattributes_manager', 'rolesattributes_physio', 'rolesattributes_scout',
             'rolesattributes_chairman', 'rolesattributes_directoroffootball',
             'rolesattributes_headofyouthdevelopment', 'rolesattributes_dataanalyst',
             'rolesattributes_sportsscientist', 'rolesattributes_loanmanager',
             'rolesattributes_technicaldirector', 'rolesattributes_setpiececoach']
    atributos['funcoes'] = {}
    for a in roles:
        if a in row and pd.notna(row.get(a)):
            chave_original = a.replace('rolesattributes_', '').replace('_', ' ').title()
            chave_traduzida = TRADUCAO_ATRIBUTOS_COMISSAO.get(chave_original, chave_original)
            atributos['funcoes'][chave_traduzida] = row.get(a)

    return {k: v for k, v in atributos.items() if v}


# ============================================================================
# AGRUPAMENTO DE ATRIBUTOS - DIRETORIA (AJUSTADO AO CSV REAL)
# ============================================================================

def agrupar_atributos_diretoria(row):
    """
    Agrupa atributos da Diretoria usando as colunas REAIS do CSV em português.
    """
    atributos = {}

    # ---- Gerais / Reputação ----
    gerais = {
        'ca_diretoria': 'CA',
        'pa_diretoria': 'PA',
        'reputacao_mundial': 'Reputação Mundial',
        'reputacao_atual': 'Reputação Atual',
        'reputacao_local': 'Reputação Local',
    }
    atributos['gerais'] = {}
    for col, label in gerais.items():
        if col in row and pd.notna(row.get(col)):
            atributos['gerais'][label] = row.get(col)

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
            atributos['presidencia'][label] = row.get(col)

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
            atributos['nao_taticos'][label] = row.get(col)

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
            atributos['staff_mental'][label] = row.get(col)

    # ---- Scouting / Análise ----
    scouting = {
        'analise_dados_jogador': 'Análise de Dados de Jogador',
        'analise_dados_time': 'Análise de Dados de Time',
        'apresentacao_dados': 'Apresentação de Dados',
    }
    atributos['scouting'] = {}
    for col, label in scouting.items():
        if col in row and pd.notna(row.get(col)):
            atributos['scouting'][label] = row.get(col)

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
            atributos['treinamento'][label] = row.get(col)

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
            atributos['personalidade'][label] = row.get(col)

    # ---- Informações Pessoais / Clube ----
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
        if col in row and pd.notna(row.get(col)) and str(row.get(col)).strip():
            atributos['informacoes'][label] = row.get(col)

    return {k: v for k, v in atributos.items() if v}


# ============================================================================
# LESÕES E BIOIMPEDÂNCIA
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
            for col in df.columns[11:]:
                valor = row.get(col, '')
                if pd.notna(valor) and str(valor).strip():
                    ocorrencias = str(valor).split(',')
                    ultima = ocorrencias[-1].strip().rstrip(';').strip()
                    separadores = [' / ', ' - ', '–', ' a ']
                    if not any(sep in ultima for sep in separadores):
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
                'data_coleta': row.get('data_bioimpedancia')
            }
        return dados
    except Exception as e:
        print(f"❌ Erro ao carregar bioimpedância {categoria}: {e}")
        return {}