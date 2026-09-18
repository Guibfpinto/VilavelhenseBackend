# services/atributos_mapper.py
"""
Mapeamento de atributos FM26 → Colunas PT-BR
E classificadores de valores em labels (Muito Bom, Bom, Médio, etc.)

Classificação RELATIVA à moda da liga Capixabão 2026 para
atributos de jogadores. Para comissão/diretoria usa escala fixa.

Suporta 3 categorias:
- Jogadores (FIELDS)
- Comissão (FIELDS_COMISSAO)
- Diretoria (FIELDS_DIRETORIA)
"""

import unicodedata
import re


# ===========================================================================
# MODA DA LIGA CAPIXABÃO 2026 (escala 0-20)
# Chave = nome da coluna CSV (PT-BR) usado em dados.py
# Atributo ausente → fallback para escala fixa (10 = Médio)
# ===========================================================================
MODAS_CAPIXABAO = {
    # ---- Mental ----
    'agressividade':          10,
    'antecipacao':            10,
    'coragem':                 8,
    'composicao':              8,   # Composure
    'concentracao':            9,
    'decisao':                12,
    'determinacao':           13,
    'criatividade':            5,   # Flair
    'lideranca':               9,
    'movimentacao_sem_bola':  11,   # OffTheBall
    'posicionamento':          7,
    'trabalho_equipe':         8,
    'visao_jogo':              7,   # Vision
    'intensidade_trabalho':    8,   # Workrate

    # ---- Físico ----
    'aceleracao':             13,
    'agilidade':              13,
    'equilibrio':              7,
    'altura_salto':            9,   # Jumping
    'condicao_fisica_natural':12,
    'velocidade_maxima':      13,   # Pace
    'resistencia':            12,   # Stamina
    'forca_fisica':            5,

    # ---- Oculto ----
    'consistencia':           12,
    'jogo_sujo':              11,   # Dirtiness
    'jogos_importantes':      12,
    'propensao_lesao':        10,
    'versatilidade':          12,

    # ---- Técnico ----
    'escanteios':              6,   # Corners
    'cruzamentos':            10,   # Crossing
    'drible':                 11,
    'finalizacao':             7,
    'primeiro_controle':      10,   # FirstTouch
    'cobranca_faltas':         7,   # Freekicks
    'cabecada':                8,   # Heading
    'chutes_longe':            7,   # LongShots
    'arremessos_laterais':     1,   # Longthrows
    'marcacao':                6,   # Marking
    'passe':                   9,   # Passing
    'cobranca_penaltis':       6,   # PenaltyTaking
    'desarme':                13,   # Tackling
    'tecnica':                10,

    # ---- Personalidade ----
    'adaptabilidade':         13,
    'ambicao':                11,
    'lealdade':               12,
    'pressao':                11,
    'profissionalismo':       11,
    'esportividade':          11,   # Sportsmanship
    'temperamento':           12,
    'controversia':            5,
}


# ===========================================================================
# MAPEAMENTO JOGADORES (JSON FM26 → coluna PT-BR)
# ===========================================================================
FIELDS = {
    # CA / PA
    ("CA",): ("habilidade_atual",     "ca_pa"),
    ("PA",): ("habilidade_potencial", "ca_pa"),

    # Goleiro
    ("GoalKeeperAttributes", "AerialAbility"):   ("gol_jogo_aereo",     "habilidade"),
    ("GoalKeeperAttributes", "CommandOfArea"):   ("gol_comando_area",   "habilidade"),
    ("GoalKeeperAttributes", "Communication"):   ("gol_comunicacao",    "habilidade"),
    ("GoalKeeperAttributes", "Eccentricity"):    ("gol_excentricidade", "habilidade"),
    ("GoalKeeperAttributes", "Handling"):        ("gol_encaixe",        "habilidade"),
    ("GoalKeeperAttributes", "Kicking"):         ("gol_chute",          "habilidade"),
    ("GoalKeeperAttributes", "OneOnOnes"):       ("gol_um_a_um",        "habilidade"),
    ("GoalKeeperAttributes", "Reflexes"):        ("gol_reflexos",       "habilidade"),
    ("GoalKeeperAttributes", "RushingOut"):      ("gol_saida",          "habilidade"),
    ("GoalKeeperAttributes", "TendencyToPunch"): ("gol_socar",          "habilidade"),
    ("GoalKeeperAttributes", "Throwing"):        ("gol_arremesso",      "habilidade"),

    # Mental
    ("MentalAttributes", "Aggression"):    ("men_agressividade",    "habilidade"),
    ("MentalAttributes", "Anticipation"):  ("men_antecipacao",      "habilidade"),
    ("MentalAttributes", "Bravery"):       ("men_coragem",          "habilidade"),
    ("MentalAttributes", "Composure"):     ("men_sangue_frio",      "habilidade"),
    ("MentalAttributes", "Concentration"): ("men_concentracao",     "habilidade"),
    ("MentalAttributes", "Vision"):        ("men_visao",            "habilidade"),
    ("MentalAttributes", "Decisions"):     ("men_decisoes",         "habilidade"),
    ("MentalAttributes", "Determination"): ("men_determinacao",     "habilidade"),
    ("MentalAttributes", "Flair"):         ("men_criatividade",     "habilidade"),
    ("MentalAttributes", "Leadership"):    ("men_lideranca",        "habilidade"),
    ("MentalAttributes", "OffTheBall"):    ("men_sem_bola",         "habilidade"),
    ("MentalAttributes", "Positioning"):   ("men_posicionamento",   "habilidade"),
    ("MentalAttributes", "Teamwork"):      ("men_trabalho_equipe",  "habilidade"),
    ("MentalAttributes", "Workrate"):      ("men_entrega",          "habilidade"),

    # Físico
    ("PhysicalAttributes", "Acceleration"):   ("fis_aceleracao",        "habilidade"),
    ("PhysicalAttributes", "Agility"):        ("fis_agilidade",         "habilidade"),
    ("PhysicalAttributes", "Balance"):        ("fis_equilibrio",        "habilidade"),
    ("PhysicalAttributes", "Jumping"):        ("fis_impulsao",          "habilidade"),
    ("PhysicalAttributes", "LeftFoot"):       ("fis_pe_esquerdo",       "perna"),
    ("PhysicalAttributes", "NaturalFitness"): ("fis_condicao_natural",  "habilidade"),
    ("PhysicalAttributes", "Pace"):           ("fis_velocidade",        "habilidade"),
    ("PhysicalAttributes", "RightFoot"):      ("fis_pe_direito",        "perna"),
    ("PhysicalAttributes", "Stamina"):        ("fis_resistencia",       "habilidade"),
    ("PhysicalAttributes", "Strength"):       ("fis_forca",             "habilidade"),

    # Oculto
    ("HiddenAttributes", "Consistency"):      ("ocu_regularidade",    "habilidade"),
    ("HiddenAttributes", "Dirtiness"):        ("ocu_sujeira",         "habilidade"),
    ("HiddenAttributes", "ImportantMatches"): ("ocu_grandes_jogos",   "habilidade"),
    ("HiddenAttributes", "InjuryProness"):    ("ocu_propensao_lesao", "habilidade"),
    ("HiddenAttributes", "Versatility"):      ("ocu_versatilidade",   "habilidade"),

    # Técnico
    ("TechnicalAttributes", "Corners"):       ("tec_cantos",          "habilidade"),
    ("TechnicalAttributes", "Crossing"):      ("tec_cruzamento",      "habilidade"),
    ("TechnicalAttributes", "Dribbling"):     ("tec_drible",          "habilidade"),
    ("TechnicalAttributes", "Finishing"):     ("tec_finalizacao",     "habilidade"),
    ("TechnicalAttributes", "FirstTouch"):    ("tec_dominio",         "habilidade"),
    ("TechnicalAttributes", "Freekicks"):     ("tec_faltas",          "habilidade"),
    ("TechnicalAttributes", "Heading"):       ("tec_cabecada",        "habilidade"),
    ("TechnicalAttributes", "LongShots"):     ("tec_chutes_longe",    "habilidade"),
    ("TechnicalAttributes", "Longthrows"):    ("tec_laterais_longos", "habilidade"),
    ("TechnicalAttributes", "Marking"):       ("tec_marcacao",        "habilidade"),
    ("TechnicalAttributes", "Passing"):       ("tec_passe",           "habilidade"),
    ("TechnicalAttributes", "PenaltyTaking"): ("tec_penalties",       "habilidade"),
    ("TechnicalAttributes", "Tackling"):      ("tec_desarme",         "habilidade"),
    ("TechnicalAttributes", "Technique"):     ("tec_tecnica",         "habilidade"),

    # Personalidade
    ("PersonalityAttributes", "Adaptability"):  ("per_adaptabilidade",     "habilidade"),
    ("PersonalityAttributes", "Ambition"):      ("per_ambicao",            "habilidade"),
    ("PersonalityAttributes", "Loyalty"):       ("per_lealdade",           "habilidade"),
    ("PersonalityAttributes", "Pressure"):      ("per_pressao",            "habilidade"),
    ("PersonalityAttributes", "Professional"):  ("per_profissionalismo",   "habilidade"),
    ("PersonalityAttributes", "Sportsmanship"): ("per_espirito_esportivo", "habilidade"),
    ("PersonalityAttributes", "Temperament"):   ("per_temperamento",       "habilidade"),
    ("PersonalityAttributes", "Controversy"):   ("per_controversia",       "habilidade"),
}


# ===========================================================================
# MAPEAMENTO COMISSÃO (CSV → coluna PT-BR)
# ===========================================================================
FIELDS_COMISSAO = {
    ("ca",): ("ca", "ca_pa"),
    ("pa",): ("pa", "ca_pa"),

    ("reputacao_mundial",): ("reputacao_mundial", "reputacao"),
    ("reputacao_atual",):   ("reputacao_atual",   "reputacao"),
    ("reputacao_local",):   ("reputacao_local",   "reputacao"),

    ("qualificacoes_treinador",): ("qualificacoes_treinador", "habilidade"),
    ("jogos_selecao",):           ("jogos_selecao",           "habilidade"),
    ("gols_selecao",):            ("gols_selecao",            "habilidade"),

    ("coachingattributes_attacking",):            ("coachingattributes_attacking",            "habilidade"),
    ("coachingattributes_defending",):            ("coachingattributes_defending",            "habilidade"),
    ("coachingattributes_fitness",):              ("coachingattributes_fitness",              "habilidade"),
    ("coachingattributes_goalkeeping",):          ("coachingattributes_goalkeeping",          "habilidade"),
    ("coachingattributes_possession",):           ("coachingattributes_possession",           "habilidade"),
    ("coachingattributes_player",):               ("coachingattributes_player",               "habilidade"),
    ("coachingattributes_tactical",):             ("coachingattributes_tactical",             "habilidade"),
    ("coachingattributes_technical",):            ("coachingattributes_technical",            "habilidade"),
    ("coachingattributes_peoplemanagement",):     ("coachingattributes_peoplemanagement",     "habilidade"),
    ("coachingattributes_workingwithyoungsters",):("coachingattributes_workingwithyoungsters","habilidade"),
    ("coachingattributes_dirtinessallowance",):   ("coachingattributes_dirtinessallowance",   "habilidade"),
    ("coachingattributes_versatility",):          ("coachingattributes_versatility",          "habilidade"),
    ("coachingattributes_setpieces",):            ("coachingattributes_setpieces",            "habilidade"),

    ("staffmentalattributes_adaptability",):            ("staffmentalattributes_adaptability",            "habilidade"),
    ("staffmentalattributes_determination",):           ("staffmentalattributes_determination",           "habilidade"),
    ("staffmentalattributes_judgingplayerability",):    ("staffmentalattributes_judgingplayerability",    "habilidade"),
    ("staffmentalattributes_judgingplayerpotential",):  ("staffmentalattributes_judgingplayerpotential",  "habilidade"),
    ("staffmentalattributes_judgingstaffability",):     ("staffmentalattributes_judgingstaffability",     "habilidade"),
    ("staffmentalattributes_negotiating",):             ("staffmentalattributes_negotiating",             "habilidade"),
    ("staffmentalattributes_authority",):               ("staffmentalattributes_authority",               "habilidade"),
    ("staffmentalattributes_motivating",):              ("staffmentalattributes_motivating",              "habilidade"),
    ("staffmentalattributes_physiotherapy",):           ("staffmentalattributes_physiotherapy",           "habilidade"),
    ("staffmentalattributes_tacticalknowledge",):       ("staffmentalattributes_tacticalknowledge",       "habilidade"),

    ("tacticalattributes_attacking",):            ("tacticalattributes_attacking",            "habilidade"),
    ("tacticalattributes_depth",):                ("tacticalattributes_depth",                "habilidade"),
    ("tacticalattributes_directness",):           ("tacticalattributes_directness",           "habilidade"),
    ("tacticalattributes_flamboyancy",):          ("tacticalattributes_flamboyancy",          "habilidade"),
    ("tacticalattributes_flexibility",):          ("tacticalattributes_flexibility",          "habilidade"),
    ("tacticalattributes_freeroles",):            ("tacticalattributes_freeroles",            "habilidade"),
    ("tacticalattributes_marking",):              ("tacticalattributes_marking",              "habilidade"),
    ("tacticalattributes_offside",):              ("tacticalattributes_offside",              "habilidade"),
    ("tacticalattributes_pressing",):             ("tacticalattributes_pressing",             "habilidade"),
    ("tacticalattributes_sittingback",):          ("tacticalattributes_sittingback",          "habilidade"),
    ("tacticalattributes_tempo",):                ("tacticalattributes_tempo",                "habilidade"),
    ("tacticalattributes_useofplaymaker",):       ("tacticalattributes_useofplaymaker",       "habilidade"),
    ("tacticalattributes_useofsubstitutions",):   ("tacticalattributes_useofsubstitutions",   "habilidade"),
    ("tacticalattributes_width",):                ("tacticalattributes_width",                "habilidade"),

    ("nontacticalattributes_buyingplayers",):        ("nontacticalattributes_buyingplayers",        "habilidade"),
    ("nontacticalattributes_hardnessoftraining",):   ("nontacticalattributes_hardnessoftraining",   "habilidade"),
    ("nontacticalattributes_mindgames",):            ("nontacticalattributes_mindgames",            "habilidade"),
    ("nontacticalattributes_squadrotation",):        ("nontacticalattributes_squadrotation",        "habilidade"),

    ("scoutingattributes_judgingplayerdata",):    ("scoutingattributes_judgingplayerdata",    "habilidade"),
    ("scoutingattributes_judgingteamdata",):      ("scoutingattributes_judgingteamdata",      "habilidade"),
    ("scoutingattributes_presentingdata",):       ("scoutingattributes_presentingdata",       "habilidade"),

    ("medicalattributes_sportsscience",):  ("medicalattributes_sportsscience", "habilidade"),

    ("personalityattributes_adaptability",):   ("personalityattributes_adaptability",   "habilidade"),
    ("personalityattributes_ambition",):       ("personalityattributes_ambition",       "habilidade"),
    ("personalityattributes_loyalty",):        ("personalityattributes_loyalty",        "habilidade"),
    ("personalityattributes_pressure",):       ("personalityattributes_pressure",       "habilidade"),
    ("personalityattributes_professional",):   ("personalityattributes_professional",   "habilidade"),
    ("personalityattributes_sportsmanship",):  ("personalityattributes_sportsmanship",  "habilidade"),
    ("personalityattributes_temperament",):    ("personalityattributes_temperament",    "habilidade"),
    ("personalityattributes_controversy",):    ("personalityattributes_controversy",    "habilidade"),

    ("rolesattributes_assistantmanager",):        ("rolesattributes_assistantmanager",        "habilidade"),
    ("rolesattributes_coach",):                   ("rolesattributes_coach",                   "habilidade"),
    ("rolesattributes_fitnesscoach",):            ("rolesattributes_fitnesscoach",            "habilidade"),
    ("rolesattributes_goalkeepingcoach",):        ("rolesattributes_goalkeepingcoach",        "habilidade"),
    ("rolesattributes_manager",):                 ("rolesattributes_manager",                 "habilidade"),
    ("rolesattributes_physio",):                  ("rolesattributes_physio",                  "habilidade"),
    ("rolesattributes_scout",):                   ("rolesattributes_scout",                   "habilidade"),
    ("rolesattributes_chairman",):                ("rolesattributes_chairman",                "habilidade"),
    ("rolesattributes_directoroffootball",):      ("rolesattributes_directoroffootball",      "habilidade"),
    ("rolesattributes_headofyouthdevelopment",):  ("rolesattributes_headofyouthdevelopment",  "habilidade"),
    ("rolesattributes_dataanalyst",):             ("rolesattributes_dataanalyst",             "habilidade"),
    ("rolesattributes_sportsscientist",):         ("rolesattributes_sportsscientist",         "habilidade"),
    ("rolesattributes_loanmanager",):             ("rolesattributes_loanmanager",             "habilidade"),
    ("rolesattributes_technicaldirector",):       ("rolesattributes_technicaldirector",       "habilidade"),
    ("rolesattributes_setpiececoach",):           ("rolesattributes_setpiececoach",           "habilidade"),
}


# ===========================================================================
# MAPEAMENTO DIRETORIA (CSV → coluna PT-BR)
# ===========================================================================
FIELDS_DIRETORIA = {
    ("ca_diretoria",): ("ca_diretoria", "ca_pa"),
    ("pa_diretoria",): ("pa_diretoria", "ca_pa"),

    ("reputacao_mundial",): ("reputacao_mundial", "reputacao"),
    ("reputacao_atual",):   ("reputacao_atual",   "reputacao"),
    ("reputacao_local",):   ("reputacao_local",   "reputacao"),

    ("habilidade_negocios",):   ("habilidade_negocios",   "habilidade"),
    ("interferencia",):         ("interferencia",         "habilidade"),
    ("paciencia_diretoria",):   ("paciencia_diretoria",   "habilidade"),
    ("recursos_financeiros",):  ("recursos_financeiros",  "habilidade"),

    ("compra_jogadores",):    ("compra_jogadores",    "habilidade"),
    ("intensidade_treino",):  ("intensidade_treino",  "habilidade"),
    ("jogos_mentais",):       ("jogos_mentais",       "habilidade"),
    ("rotacao_elenco",):      ("rotacao_elenco",      "habilidade"),

    ("adaptabilidade",):         ("adaptabilidade",         "habilidade"),
    ("determinacao",):           ("determinacao",           "habilidade"),
    ("julgamento_jogador",):     ("julgamento_jogador",     "habilidade"),
    ("julgamento_potencial",):   ("julgamento_potencial",   "habilidade"),
    ("julgamento_staff",):       ("julgamento_staff",       "habilidade"),
    ("negociacao",):             ("negociacao",             "habilidade"),
    ("autoridade",):             ("autoridade",             "habilidade"),
    ("motivacao",):              ("motivacao",              "habilidade"),
    ("conhecimento_tatico",):    ("conhecimento_tatico",    "habilidade"),

    ("analise_dados_jogador",):  ("analise_dados_jogador",  "habilidade"),
    ("analise_dados_time",):     ("analise_dados_time",     "habilidade"),
    ("apresentacao_dados",):     ("apresentacao_dados",     "habilidade"),

    ("gestao_pessoas",):         ("gestao_pessoas",         "habilidade"),
    ("trabalho_jovens",):        ("trabalho_jovens",        "habilidade"),
    ("bolas_paradas",):          ("bolas_paradas",          "habilidade"),
    ("tolerancia_sujeira",):     ("tolerancia_sujeira",     "habilidade"),
    ("versatilidade",):          ("versatilidade",          "habilidade"),

    ("ambicao",):         ("ambicao",         "habilidade"),
    ("lealdade",):        ("lealdade",        "habilidade"),
    ("pressao",):         ("pressao",         "habilidade"),
    ("profissionalismo",):("profissionalismo","habilidade"),
    ("esportividade",):   ("esportividade",   "habilidade"),
    ("temperamento",):    ("temperamento",    "habilidade"),
    ("controversia",):    ("controversia",    "habilidade"),
    ("personalidade",):   ("personalidade",   "habilidade"),
}


# ===========================================================================
#  Normalização
# ===========================================================================

def norm_key(s) -> str:
    """minúsculas, sem acento, só a-z0-9."""
    if s is None:
        return ""
    s = str(s).replace("_", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get_value(data, path):
    """Navega no JSON seguindo o caminho."""
    cur = data
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur


def normalizar_valor_atributo(valor):
    """
    Apenas converte para número INTEIRO (sem divisão, sem corte).
    O CSV já tem valores na escala 0-20.
    Retorna o valor original caso não seja numérico.
    """
    if valor is None:
        return None
    try:
        return int(float(str(valor).replace(',', '.')))
    except (ValueError, TypeError):
        return valor


def _is_nan(valor) -> bool:
    """Verifica NaN/None sem depender do pandas."""
    if valor is None:
        return True
    try:
        return valor != valor
    except Exception:
        return False


# ===========================================================================
#  Classificadores (número → label)
# ===========================================================================

def classificar_ca_pa(v):
    """CA/PA — escala 0-200."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    if v <= 40:   return "Muito Baixo"
    if v <= 80:   return "Baixo"
    if v <= 120:  return "Médio"
    if v <= 160:  return "Alto"
    return "Muito Alto"


def classificar_perna(v):
    """Pé esquerdo/direito — escala 0-20."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    if v <= 4:   return "Muito Fraco"
    if v <= 8:   return "Fraco"
    if v <= 12:  return "Razoável"
    if v <= 16:  return "Forte"
    return "Muito Forte"


def classificar_habilidade(v, attr=None):
    """
    Atributos de habilidade — escala 0-20.

    Se `attr` for fornecido e estiver em MODAS_CAPIXABAO:
      → classifica RELATIVO à moda da liga Capixabão 2026
        (diferença contra a moda define o label)

    Caso contrário:
      → usa escala fixa (10 = Médio)
    """
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None

    # ---- Modo relativo à liga ----
    mode = MODAS_CAPIXABAO.get(attr) if attr else None

    if mode is not None:
        diff = v - mode
        if diff <= -5:  return "Muito Ruim"
        if diff <= -2:  return "Ruim"
        if diff <= 1:   return "Médio"
        if diff <= 4:   return "Bom"
        return "Muito Bom"

    # ---- Fallback: escala fixa 0-20 ----
    if v <= 4:   return "Muito Ruim"
    if v <= 8:   return "Ruim"
    if v <= 12:  return "Médio"
    if v <= 16:  return "Bom"
    return "Muito Bom"


def classificar_reputacao(v):
    """Reputação — escala 0-10000."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    if v <= 100:   return "Muito Baixa"
    if v <= 250:   return "Baixa"
    if v <= 500:   return "Média"
    if v <= 1000:  return "Alta"
    if v <= 5000:  return "Muito Alta"
    return "Lendária"


CLASSIFICADORES = {
    "ca_pa":      classificar_ca_pa,
    "perna":      classificar_perna,
    "reputacao":  classificar_reputacao,
    # "habilidade" é tratada separadamente em classificar_por_tipo
    # porque aceita o parâmetro opcional `attr`.
}


# ===========================================================================
#  Funções públicas
# ===========================================================================

def classificar_por_tipo(valor, tipo, attr=None):
    """
    Aplica o classificador correto com base no tipo.
    `attr` (opcional) é o nome da coluna CSV — usado para classificar
    'habilidade' relativo à moda da liga.
    """
    if _is_nan(valor):
        return None

    if tipo == "habilidade":
        return classificar_habilidade(valor, attr=attr)

    classificador = CLASSIFICADORES.get(tipo)
    if classificador:
        return classificador(valor)
    return None


def classificar_valor(valor, tipo, attr=None):
    """
    Normaliza o valor e devolve o rótulo classificado.
    Fluxo: normalizar_valor_atributo → classificar_por_tipo.
    """
    valor_norm = normalizar_valor_atributo(valor)
    if _is_nan(valor_norm):
        return None
    return classificar_por_tipo(valor_norm, tipo, attr=attr)


def extrair_atributos_do_json(json_data):
    """Extrai todos os atributos de um JSON de jogador (FM26)."""
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS.items():
        valor = get_value(json_data, path)
        if valor is not None:
            resultado[coluna_ptbr] = valor
    return resultado


def extrair_atributos_comissao(row):
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS_COMISSAO.items():
        chave_csv = path[0]
        if chave_csv in row:
            valor = row[chave_csv]
            if not _is_nan(valor):
                resultado[coluna_ptbr] = valor
    return resultado


def extrair_atributos_diretoria(row):
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS_DIRETORIA.items():
        chave_csv = path[0]
        if chave_csv in row:
            valor = row[chave_csv]
            if not _is_nan(valor):
                resultado[coluna_ptbr] = valor
    return resultado


def classificar_atributo(valor, tipo, attr=None):
    """Normaliza o valor e retorna (valor_normalizado, label)."""
    valor_norm = normalizar_valor_atributo(valor)
    if _is_nan(valor_norm):
        return None, None
    label = classificar_por_tipo(valor_norm, tipo, attr=attr)
    return valor_norm, label


def formatar_atributo_com_label(valor, tipo, attr=None):
    """Retorna string no formato 'valor (label)'."""
    v, label = classificar_atributo(valor, tipo, attr=attr)
    if v is None:
        return "N/I"
    if label:
        return f"{v} ({label})"
    return str(v)


def listar_tipos_disponiveis():
    """Retorna os tipos de classificação disponíveis."""
    return list(CLASSIFICADORES.keys()) + ["habilidade"]