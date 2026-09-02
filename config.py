import os

class Config:
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    CORS_ORIGINS = '*'  # Em produção, coloque a URL do seu app Expo

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_FOLDER, exist_ok=True)

    # Arquivos
    ARQUIVO_USUARIOS = os.path.join(DATA_FOLDER, 'usuarios.json')
    ARQUIVOS_CSV = {
        'profissional': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_profissional_2027.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_Sub20_2027.csv'),
        'sub17': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_Sub17_2027.csv'),
        'comissao_profissional': os.path.join(DATA_FOLDER, 'perfil_completo_comissao_2027.csv'),
        'comissao_sub20': os.path.join(DATA_FOLDER, 'perfil_completo_comissao_Sub20_2027.csv'),
    }
    ARQUIVOS_LESOES = {
        'profissional': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_profissional_lesoes.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub20_lesoes.csv'),
    }
    ARQUIVOS_BIO = {
        'profissional': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_profissional_Bioimpedancia.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub20_Bioimpedancia.csv'),
    }
    ARQUIVOS_CARTOES = {
        'profissional': os.path.join(DATA_FOLDER, 'cartoes_acumulados_profissional.json'),
        'sub20': os.path.join(DATA_FOLDER, 'cartoes_acumulados_sub20.json'),
        'sub17': os.path.join(DATA_FOLDER, 'cartoes_acumulados_sub17.json'),
        'comissao_profissional': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_profissional.json'),
        'comissao_sub20': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_sub20.json'),
        'comissao_sub17': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_sub17.json'),
    }

    CATEGORIAS_JOGADORES = ['profissional', 'sub20', 'sub17']
    CATEGORIAS_COMISSAO = ['comissao_profissional', 'comissao_sub20', 'comissao_sub17']
    CATEGORIAS_CARTOES = CATEGORIAS_JOGADORES + CATEGORIAS_COMISSAO

    # Atributos FM26 - Jogadores
    ATRIBUTOS_FM26_JOGADORES = [
        # Técnicos
        'escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
        'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
        'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica',
        # Mentais
        'agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
        'decisao', 'determinacao', 'criatividade', 'lideranca', 'movimentacao_sem_bola',
        'posicionamento', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho',
        # Físicos
        'aceleracao', 'agilidade', 'equilibrio', 'altura_salto', 'condicao_fisica_natural',
        'velocidade_maxima', 'resistencia', 'forca_fisica',
        # Goleiro
        'reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro', 'comando_area',
        'comunicacao_goleiro', 'chutes_goleiro', 'um_contra_um_goleiro', 'saida_gol',
        'tendencia_socar', 'arremessos_goleiro', 'excentricidade',
        # Ocultos
        'consistencia', 'jogo_sujo', 'jogos_importantes', 'propensao_lesao', 'versatilidade',
        # Personalidade
        'adaptabilidade', 'ambicao', 'lealdade', 'pressao', 'profissionalismo',
        'esportividade', 'temperamento', 'controversia'
    ]

    # Atributos FM26 - Comissão
    ATRIBUTOS_FM26_COMISSAO = [
        'CA', 'PA', 'reputacao_mundial', 'reputacao_atual', 'reputacao_local',
        'qualificacoes_treinador', 'jogos_selecao', 'gols_selecao',
        'treinamento_ataque', 'treinamento_defesa', 'treinamento_condicionamento',
        'treinamento_goleiros', 'treinamento_posse', 'treinamento_tatica',
        'treinamento_tecnico', 'treinamento_gestao_pessoas', 'treinamento_trabalho_jovens',
        'treinamento_bolas_paradas',
        'adaptabilidade_staff', 'determinacao_staff', 'avaliacao_habilidade_jogador',
        'avaliacao_potencial_jogador', 'avaliacao_habilidade_staff', 'negociacao',
        'autoridade', 'motivacao', 'fisioterapia', 'conhecimento_tatico',
        'tatica_ataque', 'profundidade', 'direcao', 'espetacularidade', 'flexibilidade',
        'funcoes_livres', 'marcacao', 'impedimento', 'pressao', 'recuar',
        'ritmo', 'uso_armador', 'uso_substituicoes', 'largura',
        'ambicao', 'lealdade', 'pressao', 'profissionalismo', 'espirito_esportivo',
        'temperamento', 'controversia', 'adaptabilidade_personalidade'
    ]