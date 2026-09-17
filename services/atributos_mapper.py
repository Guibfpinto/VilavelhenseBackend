# services/atributos_mapper.py
"""
Mapeamento de atributos FM26 → Colunas PT-BR
E classificadores de valores em labels (Muito Bom, Bom, Médio, etc.)

Suporta 3 categorias:
- Jogadores (FIELDS)
- Comissão (FIELDS_COMISSAO)
- Diretoria (FIELDS_DIRETORIA)
"""

import unicodedata
import re


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
    # CA / PA
    ("ca",): ("ca", "ca_pa"),
    ("pa",): ("pa", "ca_pa"),

    # Reputação
    ("reputacao_mundial",): ("reputacao_mundial", "reputacao"),
    ("reputacao_atual",):   ("reputacao_atual",   "reputacao"),
    ("reputacao_local",):   ("reputacao_local",   "reputacao"),

    # Gerais
    ("qualificacoes_treinador",): ("qualificacoes_treinador", "habilidade"),
    ("jogos_selecao",):           ("jogos_selecao",           "habilidade"),
    ("gols_selecao",):            ("gols_selecao",            "habilidade"),

    # Coaching
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

    # Staff Mental
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

    # Táticas
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

    # Não-Táticos
    ("nontacticalattributes_buyingplayers",):        ("nontacticalattributes_buyingplayers",        "habilidade"),
    ("nontacticalattributes_hardnessoftraining",):   ("nontacticalattributes_hardnessoftraining",   "habilidade"),
    ("nontacticalattributes_mindgames",):            ("nontacticalattributes_mindgames",            "habilidade"),
    ("nontacticalattributes_squadrotation",):        ("nontacticalattributes_squadrotation",        "habilidade"),

    # Scouting
    ("scoutingattributes_judgingplayerdata",):    ("scoutingattributes_judgingplayerdata",    "habilidade"),
    ("scoutingattributes_judgingteamdata",):      ("scoutingattributes_judgingteamdata",      "habilidade"),
    ("scoutingattributes_presentingdata",):       ("scoutingattributes_presentingdata",       "habilidade"),

    # Médica
    ("medicalattributes_sportsscience",):  ("medicalattributes_sportsscience", "habilidade"),

    # Personalidade
    ("personalityattributes_adaptability",):   ("personalityattributes_adaptability",   "habilidade"),
    ("personalityattributes_ambition",):       ("personalityattributes_ambition",       "habilidade"),
    ("personalityattributes_loyalty",):        ("personalityattributes_loyalty",        "habilidade"),
    ("personalityattributes_pressure",):       ("personalityattributes_pressure",       "habilidade"),
    ("personalityattributes_professional",):   ("personalityattributes_professional",   "habilidade"),
    ("personalityattributes_sportsmanship",):  ("personalityattributes_sportsmanship",  "habilidade"),
    ("personalityattributes_temperament",):    ("personalityattributes_temperament",    "habilidade"),
    ("personalityattributes_controversy",):    ("personalityattributes_controversy",    "habilidade"),

    # Roles
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
    # CA / PA
    ("ca_diretoria",): ("ca_diretoria", "ca_pa"),
    ("pa_diretoria",): ("pa_diretoria", "ca_pa"),

    # Reputação
    ("reputacao_mundial",): ("reputacao_mundial", "reputacao"),
    ("reputacao_atual",):   ("reputacao_atual",   "reputacao"),
    ("reputacao_local",):   ("reputacao_local",   "reputacao"),

    # Presidência
    ("habilidade_negocios",):   ("habilidade_negocios",   "habilidade"),
    ("interferencia",):         ("interferencia",         "habilidade"),
    ("paciencia_diretoria",):   ("paciencia_diretoria",   "habilidade"),
    ("recursos_financeiros",):  ("recursos_financeiros",  "habilidade"),

    # Não-Táticos
    ("compra_jogadores",):    ("compra_jogadores",    "habilidade"),
    ("intensidade_treino",):  ("intensidade_treino",  "habilidade"),
    ("jogos_mentais",):       ("jogos_mentais",       "habilidade"),
    ("rotacao_elenco",):      ("rotacao_elenco",      "habilidade"),

    # Staff Mental
    ("adaptabilidade",):         ("adaptabilidade",         "habilidade"),
    ("determinacao",):           ("determinacao",           "habilidade"),
    ("julgamento_jogador",):     ("julgamento_jogador",     "habilidade"),
    ("julgamento_potencial",):   ("julgamento_potencial",   "habilidade"),
    ("julgamento_staff",):       ("julgamento_staff",       "habilidade"),
    ("negociacao",):             ("negociacao",             "habilidade"),
    ("autoridade",):             ("autoridade",             "habilidade"),
    ("motivacao",):              ("motivacao",              "habilidade"),
    ("conhecimento_tatico",):    ("conhecimento_tatico",    "habilidade"),

    # Scouting / Análise
    ("analise_dados_jogador",):  ("analise_dados_jogador",  "habilidade"),
    ("analise_dados_time",):     ("analise_dados_time",     "habilidade"),
    ("apresentacao_dados",):     ("apresentacao_dados",     "habilidade"),

    # Treinamento
    ("gestao_pessoas",):         ("gestao_pessoas",         "habilidade"),
    ("trabalho_jovens",):        ("trabalho_jovens",        "habilidade"),
    ("bolas_paradas",):          ("bolas_paradas",          "habilidade"),
    ("tolerancia_sujeira",):     ("tolerancia_sujeira",     "habilidade"),
    ("versatilidade",):          ("versatilidade",          "habilidade"),

    # Personalidade
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


def classificar_habilidade(v):
    """Atributos de habilidade — escala 0-20."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
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
    "ca_pa":       classificar_ca_pa,
    "perna":       classificar_perna,
    "habilidade":  classificar_habilidade,
    "reputacao":   classificar_reputacao,
}


# ===========================================================================
#  Funções públicas
# ===========================================================================

def classificar_por_tipo(valor, tipo):
    """Aplica o classificador correto com base no tipo."""
    if valor is None or (isinstance(valor, float) and str(valor) == 'nan'):
        return None
    classificador = CLASSIFICADORES.get(tipo)
    if classificador:
        return classificador(valor)
    return None


def extrair_atributos_do_json(json_data):
    """Extrai todos os atributos de um JSON de jogador (FM26)."""
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS.items():
        valor = get_value(json_data, path)
        if valor is not None:
            resultado[coluna_ptbr] = valor
    return resultado


def extrair_atributos_comissao(row):
    """
    Extrai atributos da comissão a partir de uma linha (dict ou Series).
    Retorna {coluna_ptbr: valor}.
    """
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS_COMISSAO.items():
        chave_csv = path[0]  # FIELDS_COMISSAO usa apenas 1 nível
        if chave_csv in row:
            valor = row[chave_csv]
            if valor is not None and not (isinstance(valor, float) and str(valor) == 'nan'):
                resultado[coluna_ptbr] = valor
    return resultado


def extrair_atributos_diretoria(row):
    """
    Extrai atributos da diretoria a partir de uma linha (dict ou Series).
    Retorna {coluna_ptbr: valor}.
    """
    resultado = {}
    for path, (coluna_ptbr, tipo) in FIELDS_DIRETORIA.items():
        chave_csv = path[0]
        if chave_csv in row:
            valor = row[chave_csv]
            if valor is not None and not (isinstance(valor, float) and str(valor) == 'nan'):
                resultado[coluna_ptbr] = valor
    return resultado


def classificar_atributo(valor, tipo):
    """Aplica o classificador correto com base no tipo."""
    if valor is None:
        return None, None
    classificador = CLASSIFICADORES.get(tipo)
    if classificador:
        return valor, classificador(valor)
    return valor, None


def formatar_atributo_com_label(valor, tipo):
    """Retorna string no formato 'valor (label)'."""
    v, label = classificar_atributo(valor, tipo)
    if v is None:
        return "N/I"
    if label:
        return f"{v} ({label})"
    return str(v)


def listar_tipos_disponiveis():
    """Retorna os tipos de classificação disponíveis."""
    return list(CLASSIFICADORES.keys())