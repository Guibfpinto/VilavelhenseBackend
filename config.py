import os

class Config:
    # ============================================================
    # CONFIGURAÇÕES GERAIS DO SERVIDOR
    # ============================================================
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    CORS_ORIGINS = '*'  # Em produção, defina a URL do seu app Expo

    # ============================================================
    # CAMINHOS DAS PASTAS
    # ============================================================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_FOLDER, exist_ok=True)

    # ============================================================
    # ARQUIVOS DE DADOS (CSV, JSON, SQLite)
    # ============================================================
    ARQUIVO_USUARIOS = os.path.join(DATA_FOLDER, 'usuarios.json')

    ARQUIVOS_CSV = {
        'profissional': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_profissional_2027.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_Sub20_2027.csv'),
        'sub17': os.path.join(DATA_FOLDER, 'perfil_completo_jogadores_Sub17_2027.csv'),
        'comissao_profissional': os.path.join(DATA_FOLDER, 'perfil_completo_comissao_2027.csv'),
        'comissao_sub20': os.path.join(DATA_FOLDER, 'perfil_completo_comissao_Sub20_2027.csv'),
        'comissao_sub17': os.path.join(DATA_FOLDER, 'perfil_completo_comissao_Sub17_2027.csv'),
    }

    ARQUIVOS_LESOES = {
        'profissional': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_profissional_lesoes.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub20_lesoes.csv'),
        'sub17': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub17_lesoes.csv'),
    }

    ARQUIVOS_BIO = {
        'profissional': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_profissional_Bioimpedancia.csv'),
        'sub20': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub20_Bioimpedancia.csv'),
        'sub17': os.path.join(DATA_FOLDER, 'jogadores_vilavelhense_Sub17_Bioimpedancia.csv'),
    }

    ARQUIVOS_CARTOES = {
        'profissional': os.path.join(DATA_FOLDER, 'cartoes_acumulados_profissional.json'),
        'sub20': os.path.join(DATA_FOLDER, 'cartoes_acumulados_sub20.json'),
        'sub17': os.path.join(DATA_FOLDER, 'cartoes_acumulados_sub17.json'),
        'comissao_profissional': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_profissional.json'),
        'comissao_sub20': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_sub20.json'),
        'comissao_sub17': os.path.join(DATA_FOLDER, 'cartoes_acumulados_comissao_sub17.json'),
    }

    # ============================================================
    # PASTAS DE ESTATÍSTICAS (CSVs de partidas) – CADA CATEGORIA PODE TER MÚLTIPLAS PASTAS
    # ============================================================
    # Para jogadores
    PASTA_ESTATISTICAS_PROFISSIONAL = [
        os.path.join(DATA_FOLDER, 'estatisticas', 'profissional')
    ]
    PASTA_ESTATISTICAS_SUB20 = [
        os.path.join(DATA_FOLDER, 'estatisticas', 'sub20')
    ]
    PASTA_ESTATISTICAS_SUB17 = [
        os.path.join(DATA_FOLDER, 'estatisticas', 'sub17')
    ]

    # Para comissão técnica
    PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL = [
        os.path.join(DATA_FOLDER, 'estatisticas_comissao', 'profissional')
    ]
    PASTA_ESTATISTICAS_COMISSAO_SUB20 = [
        os.path.join(DATA_FOLDER, 'estatisticas_comissao', 'sub20')
    ]
    PASTA_ESTATISTICAS_COMISSAO_SUB17 = [
        os.path.join(DATA_FOLDER, 'estatisticas_comissao', 'sub17')
    ]

    # ============================================================
    # BANCO SQLITE DE FALLBACK (para partidas)
    # ============================================================
    SQLITE_PATH = os.path.join(DATA_FOLDER, 'meu_futebol.db')

    # ============================================================
    # CATEGORIAS VÁLIDAS
    # ============================================================
    CATEGORIAS_JOGADORES = ['profissional', 'sub20', 'sub17']
    CATEGORIAS_COMISSAO = ['comissao_profissional', 'comissao_sub20', 'comissao_sub17']
    CATEGORIAS_CARTOES = CATEGORIAS_JOGADORES + CATEGORIAS_COMISSAO

    # ============================================================
    # CONFIGURAÇÕES DA API-FOOTBALL
    # ============================================================
    API_KEY = "51e827a67129dbf7e4126c59ac155623"
    BASE_URL = "https://v3.football.api-sports.io"
    TEAM_ID = 15609  # ID do Vilavelhense FC na API
    HEADERS_API = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }

    # ============================================================
    # URL DA FASTAPI (FALLBACK PARA PARTIDAS)
    # ============================================================
    FASTAPI_URL = "http://localhost:8000"  # Altere se a FastAPI estiver em outro IP/porta

    # ============================================================
    # ATRIBUTOS FM26 – JOGADORES
    # ============================================================
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

    # ============================================================
    # ATRIBUTOS FM26 – COMISSÃO TÉCNICA
    # ============================================================
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

    # ============================================================
    # MAPEAMENTO DE ARQUIVOS POR CATEGORIA (para funções auxiliares)
    # ============================================================
    @classmethod
    def get_csv_path(cls, categoria):
        """Retorna o caminho do CSV principal de uma categoria (jogadores ou comissão)."""
        return cls.ARQUIVOS_CSV.get(categoria)

    @classmethod
    def get_lesoes_path(cls, categoria):
        """Retorna o caminho do CSV de lesões de uma categoria."""
        return cls.ARQUIVOS_LESOES.get(categoria)

    @classmethod
    def get_bio_path(cls, categoria):
        """Retorna o caminho do CSV de bioimpedância de uma categoria."""
        return cls.ARQUIVOS_BIO.get(categoria)

    @classmethod
    def get_cartoes_path(cls, categoria):
        """Retorna o caminho do arquivo JSON de cartões de uma categoria."""
        return cls.ARQUIVOS_CARTOES.get(categoria)

    @classmethod
    def get_estatisticas_pastas(cls, categoria):
        """Retorna a lista de pastas de estatísticas (CSVs de partidas) para uma categoria."""
        mapa = {
            'profissional': cls.PASTA_ESTATISTICAS_PROFISSIONAL,
            'sub20': cls.PASTA_ESTATISTICAS_SUB20,
            'sub17': cls.PASTA_ESTATISTICAS_SUB17,
            'comissao_profissional': cls.PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL,
            'comissao_sub20': cls.PASTA_ESTATISTICAS_COMISSAO_SUB20,
            'comissao_sub17': cls.PASTA_ESTATISTICAS_COMISSAO_SUB17,
        }
        return mapa.get(categoria, [])