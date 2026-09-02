import os
import pandas as pd
import numpy as np
from config import Config
from utils.datas import calcular_idade
from services.bioimpedancia import classif_imc, classif_gordura, estado_fisico

# ============================================================================
# Funções de carregamento de dados (CSV, lesões, bioimpedância)
# ============================================================================

def carregar_dados_elenco(categoria):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
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

        for col in ['altura_cm', 'peso_kg']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['IMC'] = df.apply(
            lambda x: x['peso_kg'] / ((x['altura_cm']/100)**2)
            if pd.notna(x['altura_cm']) and pd.notna(x['peso_kg']) and x['altura_cm'] > 0
            else np.nan, axis=1
        ).round(1)
        df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)

        df['Idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x))

        df['Gordura_Corporal_%'] = df.apply(
            lambda row: round((1.20*row['IMC']) + (0.23*row['Idade']) - 16.2, 1)
            if pd.notna(row['IMC']) and pd.notna(row['Idade']) else np.nan, axis=1
        )

        df['Massa_Magra_kg'] = df.apply(
            lambda row: round(row['peso_kg'] * (1 - row['Gordura_Corporal_%']/100), 1)
            if pd.notna(row['peso_kg']) and pd.notna(row['Gordura_Corporal_%']) else np.nan,
            axis=1
        )
        df['Massa_Muscular_Estimada_kg'] = df.apply(
            lambda row: round(row['Massa_Magra_kg'] * 0.55, 1)
            if pd.notna(row['Massa_Magra_kg']) else np.nan,
            axis=1
        )

        df['Classificacao_Gordura'] = df.apply(
            lambda x: classif_gordura(x['Gordura_Corporal_%'], x['Idade']), axis=1
        )
        df['Estado_Fisico'] = df.apply(
            lambda row: estado_fisico(row['Classificacao_IMC'], row['Classificacao_Gordura']), axis=1
        )

        def cat_pos(pos_str):
            if pd.isna(pos_str):
                return 'Outros'
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

        df['Rating_Geral_FM26'] = df.apply(
            lambda row: min(100, row.get('habilidade_atual', 0)/2) if pd.notna(row.get('habilidade_atual')) else 50,
            axis=1
        )

        df = df[df['nome_completo'].notna()]
        return df
    except Exception as e:
        print(f"Erro ao carregar {categoria}: {e}")
        return None

def carregar_dados_comissao(categoria):
    caminho = Config.ARQUIVOS_CSV.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        if 'apelido' in df.columns:
            df['nome'] = df['apelido'].fillna('')
        elif 'nome_completo' in df.columns:
            df['nome'] = df['nome_completo'].fillna('')
        if 'cargo' not in df.columns:
            df['cargo'] = 'Técnico'
        if 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(calcular_idade)
        else:
            df['idade'] = None
        from services.cartoes_service import mapear_nome_para_canonico
        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)
        return df
    except Exception as e:
        print(f"Erro ao carregar comissão {categoria}: {e}")
        return None

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
                    ultima = ocorrencias[-1].strip()
                    if '/' not in ultima and '-' not in ultima:
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
    except:
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
            dados[nome] = {
                'peso': safe_float(row.get('peso_kg')),
                'altura': safe_float(row.get('altura_cm')) / 100.0 if safe_float(row.get('altura_cm')) else None,
                'gordura': safe_float(row.get('gordura_corporal')),
                'massa_magra': safe_float(row.get('massa_magra')),
                'massa_muscular': safe_float(row.get('massa_muscular')),
                'data_coleta': row.get('data_bioimpedancia')
            }
        return dados
    except:
        return {}

def safe_float(valor):
    try:
        return float(str(valor).replace(',', '.'))
    except:
        return None

# ============================================================================
# Funções de agrupamento de atributos FM26
# ============================================================================

def agrupar_atributos_jogador(row):
    atributos = {}
    # Técnicos
    tecnicos = ['escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
                'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
                'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica']
    atributos['tecnicos'] = {a: row.get(a) for a in tecnicos if a in row and pd.notna(row.get(a))}
    # Mentais
    mentais = ['agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
               'decisao', 'determinacao', 'criatividade', 'lideranca', 'movimentacao_sem_bola',
               'posicionamento', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho']
    atributos['mentais'] = {a: row.get(a) for a in mentais if a in row and pd.notna(row.get(a))}
    # Físicos
    fisicos = ['aceleracao', 'agilidade', 'equilibrio', 'altura_salto', 'condicao_fisica_natural',
               'velocidade_maxima', 'resistencia', 'forca_fisica']
    atributos['fisicos'] = {a: row.get(a) for a in fisicos if a in row and pd.notna(row.get(a))}
    # Goleiro
    goleiro = ['reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro', 'comando_area',
               'comunicacao_goleiro', 'chutes_goleiro', 'um_contra_um_goleiro', 'saida_gol',
               'tendencia_socar', 'arremessos_goleiro', 'excentricidade']
    atributos['goleiro'] = {a: row.get(a) for a in goleiro if a in row and pd.notna(row.get(a))}
    # Ocultos
    ocultos = ['consistencia', 'jogo_sujo', 'jogos_importantes', 'propensao_lesao', 'versatilidade']
    atributos['ocultos'] = {a: row.get(a) for a in ocultos if a in row and pd.notna(row.get(a))}
    # Personalidade
    personalidade = ['adaptabilidade', 'ambicao', 'lealdade', 'pressao', 'profissionalismo',
                     'esportividade', 'temperamento', 'controversia']
    atributos['personalidade'] = {a: row.get(a) for a in personalidade if a in row and pd.notna(row.get(a))}
    return atributos

def agrupar_atributos_comissao(row):
    atributos = {}
    # Gerais
    gerais = ['CA', 'PA', 'reputacao_mundial', 'reputacao_atual', 'reputacao_local',
              'qualificacoes_treinador', 'jogos_selecao', 'gols_selecao']
    atributos['gerais'] = {a: row.get(a) for a in gerais if a in row and pd.notna(row.get(a))}
    # Treinamento
    treinamento = ['treinamento_ataque', 'treinamento_defesa', 'treinamento_condicionamento',
                   'treinamento_goleiros', 'treinamento_posse', 'treinamento_tatica',
                   'treinamento_tecnico', 'treinamento_gestao_pessoas', 'treinamento_trabalho_jovens',
                   'treinamento_bolas_paradas']
    atributos['treinamento'] = {a: row.get(a) for a in treinamento if a in row and pd.notna(row.get(a))}
    # Staff Mental
    staff_mental = ['adaptabilidade_staff', 'determinacao_staff', 'avaliacao_habilidade_jogador',
                    'avaliacao_potencial_jogador', 'avaliacao_habilidade_staff', 'negociacao',
                    'autoridade', 'motivacao', 'fisioterapia', 'conhecimento_tatico']
    atributos['staff_mental'] = {a: row.get(a) for a in staff_mental if a in row and pd.notna(row.get(a))}
    # Táticas
    taticas = ['tatica_ataque', 'profundidade', 'direcao', 'espetacularidade', 'flexibilidade',
               'funcoes_livres', 'marcacao', 'impedimento', 'pressao', 'recuar',
               'ritmo', 'uso_armador', 'uso_substituicoes', 'largura']
    atributos['taticas'] = {a: row.get(a) for a in taticas if a in row and pd.notna(row.get(a))}
    # Personalidade
    personalidade = ['ambicao', 'lealdade', 'pressao', 'profissionalismo', 'espirito_esportivo',
                     'temperamento', 'controversia', 'adaptabilidade_personalidade']
    atributos['personalidade'] = {a: row.get(a) for a in personalidade if a in row and pd.notna(row.get(a))}
    return atributos