from flask import Blueprint, request, jsonify
from services.cartoes_service import carregar_cartoes, salvar_cartoes, jogador_suspenso, mapear_nome_para_canonico
from config import Config
from datetime import datetime
import pandas as pd
import os
import glob
import re

bp = Blueprint('cartoes', __name__, url_prefix='/api/cartoes')


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def extrair_data_do_arquivo(caminho):
    nome = os.path.basename(caminho)
    match = re.search(r'(\d{4}-\d{2}-\d{2})', nome)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except:
            pass
    return datetime.fromtimestamp(os.path.getmtime(caminho))


def extrair_id_jogo(caminho):
    nome = os.path.basename(caminho)
    match = re.search(r'jogo_(\d+)_', nome)
    if match:
        return int(match.group(1))
    return None


def jogador_aparece_no_csv(df, nome_canonico):
    """Verifica se um jogador aparece em um CSV (titular, reserva ou com minutos > 0)."""
    for _, row in df.iterrows():
        nome = row.get('jogador')
        if pd.isna(nome) or not str(nome).strip():
            continue
        if mapear_nome_para_canonico(nome) == nome_canonico:
            minutos = row.get('minutos', 0)
            try:
                if int(minutos) > 0:
                    return True
            except:
                return True
    return False


# ============================================================
# FUNÇÃO PRINCIPAL: REPROCESSAR CARTÕES DOS CSVs
# ============================================================

def reprocessar_cartoes_dos_csvs(categoria):
    """
    Lê todos os CSVs de estatísticas da categoria e recria o histórico de cartões.
    Regras:
    - Se não houver CSVs, retorna cartões vazios (zera tudo).
    - Se um jogador tomou vermelho e NÃO jogou a próxima partida, seus cartões são zerados.
    - Suspensão por 3 amarelos: se o jogador NÃO jogar a próxima partida, os cartões são zerados.
    """
    # ===== 1. OBTÉM AS PASTAS DE ESTATÍSTICAS =====
    if categoria == 'profissional':
        pastas = getattr(Config, 'PASTA_ESTATISTICAS_PROFISSIONAL', [])
    elif categoria == 'sub17':
        pastas = getattr(Config, 'PASTA_ESTATISTICAS_SUB17', [])
    elif categoria == 'sub20':
        pastas = getattr(Config, 'PASTA_ESTATISTICAS_SUB20', [])
    else:
        return {}, None  # Categoria sem pastas → zera

    if not pastas:
        return {}, None  # Nenhuma pasta configurada → zera

    # ===== 2. LISTA TODOS OS CSVs EXISTENTES =====
    arquivos_csv = []
    for pasta in pastas:
        if os.path.exists(pasta):
            arquivos_csv.extend(glob.glob(os.path.join(pasta, "*.csv")))

    if not arquivos_csv:
        return {}, None  # Nenhum CSV encontrado → zera

    # ===== 3. ORDENA POR DATA (CRONOLÓGICO) =====
    arquivos_com_data = [(extrair_data_do_arquivo(arq), arq) for arq in arquivos_csv]
    arquivos_com_data.sort(key=lambda x: x[0])
    arquivos_csv_ordenados = [arq for _, arq in arquivos_com_data]

    # ===== 4. PROCESSAMENTO =====
    cartoes = {}
    ids_processados = set()
    competicao_anterior = None
    suspensos_para_proxima = {}  # {nome_canonico: (motivo, data_jogo, adversario)}

    for idx, arq in enumerate(arquivos_csv_ordenados):
        jogo_id = extrair_id_jogo(arq)
        if jogo_id is not None and jogo_id in ids_processados:
            continue
        if jogo_id is not None:
            ids_processados.add(jogo_id)

        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8-sig')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            adversario = df['adversario'].iloc[0] if 'adversario' in df.columns else "Desconhecido"
            competicao = df['competicao'].iloc[0] if 'competicao' in df.columns else "Desconhecida"
            data_str = extrair_data_do_arquivo(arq).strftime("%d/%m/%Y")

            # ===== RESET POR MUDANÇA DE COMPETIÇÃO =====
            if competicao_anterior is not None and competicao != competicao_anterior:
                # Zera todos os cartões (nova competição)
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
                suspensos_para_proxima = {}
            competicao_anterior = competicao

            # ===== VERIFICA SUSPENSOS DA PARTIDA ANTERIOR =====
            # Para cada jogador que estava suspenso, verifica se ele jogou esta partida
            for nome_canonico, (motivo, data_ant, adv_ant) in list(suspensos_para_proxima.items()):
                if not jogador_aparece_no_csv(df, nome_canonico):
                    # Jogador NÃO jogou → cumpriu suspensão → zera cartões
                    if nome_canonico in cartoes:
                        cartoes[nome_canonico]['amarelos'] = 0
                        cartoes[nome_canonico]['vermelho'] = False
                        cartoes[nome_canonico]['suspenso_proxima'] = False
                        # Marca no histórico que a suspensão foi cumprida
                        for ev in cartoes[nome_canonico].get('historico', []):
                            if ev.get('suspenso_causada') and not ev.get('suspenso_cumprida'):
                                ev['suspenso_cumprida'] = True
                        print(f"✅ {nome_canonico} cumpriu suspensão (não jogou) e teve cartões zerados.")
                # Se jogou, mantém a suspensão (vai ser processada novamente)
                # Se aparecer no CSV mas não jogou (minutos=0), consideramos que cumpriu
                # (já tratado acima com jogador_aparece_no_csv que exige minutos > 0)

            # ===== RESETA A LISTA DE SUSPENSOS PARA ESTA PARTIDA =====
            suspensos_para_proxima = {}

            # ===== PROCESSAMENTO DOS CARTÕES DO JOGO =====
            for _, row in df.iterrows():
                jogador_nome = row.get('jogador')
                if pd.isna(jogador_nome) or not str(jogador_nome).strip():
                    continue

                canonico = mapear_nome_para_canonico(jogador_nome)
                if not canonico:
                    continue

                amarelos = int(row.get('cartoes_amarelos', 0))
                vermelhos = int(row.get('cartoes_vermelhos', 0))

                if amarelos == 0 and vermelhos == 0:
                    continue

                if canonico not in cartoes:
                    cartoes[canonico] = {
                        'amarelos': 0,
                        'vermelho': False,
                        'suspenso_proxima': False,
                        'historico': []
                    }

                # ===== AMARELOS =====
                for _ in range(amarelos):
                    cartoes[canonico]['amarelos'] += 1
                    terceiro = cartoes[canonico]['amarelos'] >= 3
                    if terceiro:
                        cartoes[canonico]['suspenso_proxima'] = True
                        suspensos_para_proxima[canonico] = ('3º amarelo', data_str, adversario)
                    cartoes[canonico]['historico'].append({
                        'data': data_str,
                        'adversario': adversario,
                        'competicao': competicao,
                        'cor': 'amarelo',
                        'terceiro_amarelo': terceiro,
                        'suspenso_causada': terceiro,
                        'suspenso_cumprida': False
                    })
                    if terceiro:
                        print(f"🟨 {canonico} recebeu 3º amarelo e está suspenso.")

                # ===== VERMELHOS =====
                for _ in range(vermelhos):
                    cartoes[canonico]['vermelho'] = True
                    cartoes[canonico]['suspenso_proxima'] = True
                    suspensos_para_proxima[canonico] = ('Vermelho', data_str, adversario)
                    cartoes[canonico]['historico'].append({
                        'data': data_str,
                        'adversario': adversario,
                        'competicao': competicao,
                        'cor': 'vermelho',
                        'terceiro_amarelo': False,
                        'suspenso_causada': True,
                        'suspenso_cumprida': False
                    })
                    print(f"🟥 {canonico} recebeu vermelho e está suspenso.")

            # ===== APÓS O JOGO: SE O JOGADOR ESTAVA SUSPENSO E JOGOU, A SUSPENSÃO NÃO FOI CUMPRIDA → MANTÉM =====
            # (já tratado acima)

        except Exception as e:
            print(f"⚠️ Erro ao processar {arq}: {e}")
            continue

    # ===== AO FINAL: SE HOUVER SUSPENSOS PARA A PRÓXIMA PARTIDA, MANTÉM =====
    # (eles já foram adicionados à lista suspensos_para_proxima)

    return cartoes, None


# ============================================================
# ROTAS DA API
# ============================================================

@bp.route('/<categoria>', methods=['GET'])
def get_cartoes(categoria):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400

    try:
        cartoes = carregar_cartoes(categoria)
        return jsonify(cartoes)
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar cartões: {str(e)}'}), 500


@bp.route('/<categoria>', methods=['POST'])
def update_cartoes(categoria):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400

    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Dados inválidos'}), 400

    cartoes = data.get('cartoes')
    if cartoes is None:
        return jsonify({'error': 'Campo "cartoes" é obrigatório'}), 400

    try:
        if salvar_cartoes(categoria, cartoes):
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': 'Falha ao salvar'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar: {str(e)}'}), 500


@bp.route('/<categoria>/jogador/<nome>', methods=['POST'])
def registrar_cartao_individual(categoria, nome):
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    cor = data.get('cor')
    minuto = data.get('minuto', 0)
    adversario = data.get('adversario', 'Desconhecido')
    data_jogo = data.get('data_jogo', datetime.now().strftime("%d/%m/%Y"))

    if cor not in ['amarelo', 'vermelho']:
        return jsonify({'error': 'Cor inválida. Use "amarelo" ou "vermelho"'}), 400

    try:
        cartoes = carregar_cartoes(categoria)
        canonico = mapear_nome_para_canonico(nome)

        if not canonico:
            return jsonify({'error': 'Jogador não identificado'}), 404

        if canonico not in cartoes:
            cartoes[canonico] = {
                'amarelos': 0,
                'vermelho': False,
                'suspenso_proxima': False,
                'historico': []
            }

        terceiro_amarelo = False
        if cor == 'amarelo':
            cartoes[canonico]['amarelos'] += 1
            if cartoes[canonico]['amarelos'] >= 3:
                cartoes[canonico]['suspenso_proxima'] = True
                terceiro_amarelo = True
        else:
            cartoes[canonico]['vermelho'] = True
            cartoes[canonico]['suspenso_proxima'] = True

        cartoes[canonico]['historico'].append({
            'data': data_jogo,
            'adversario': adversario,
            'cor': cor,
            'terceiro_amarelo': terceiro_amarelo,
            'suspenso_causada': (cor == 'vermelho' or terceiro_amarelo),
            'suspenso_cumprida': False
        })

        if salvar_cartoes(categoria, cartoes):
            return jsonify({
                'status': 'ok',
                'suspenso': cartoes[canonico]['suspenso_proxima']
            })
        else:
            return jsonify({'error': 'Falha ao salvar'}), 500

    except Exception as e:
        return jsonify({'error': f'Erro ao registrar cartão: {str(e)}'}), 500


# ============================================================
# REINICIAR CARTÕES (VIA CSV OU ZERANDO)
# ============================================================

@bp.route('/<categoria>/reiniciar', methods=['POST'])
def reiniciar_cartoes(categoria):
    """
    Reinicia o histórico de cartões da categoria.
    - Se houver CSVs: reprocessa a partir deles.
    - Se NÃO houver CSVs: zera os cartões (JSON vazio).
    """
    if categoria not in Config.CATEGORIAS_CARTOES:
        return jsonify({'error': 'Categoria inválida'}), 400

    # Apenas jogadores têm CSVs
    if categoria in Config.CATEGORIAS_JOGADORES:
        novos_cartoes, erro = reprocessar_cartoes_dos_csvs(categoria)
        if erro:
            return jsonify({'error': erro}), 500
        if novos_cartoes is None:
            novos_cartoes = {}  # zera
    else:
        # Comissão: não tem CSVs → zera
        novos_cartoes = {}

    try:
        if salvar_cartoes(categoria, novos_cartoes):
            return jsonify({
                'status': 'ok',
                'mensagem': f'Cartões da categoria "{categoria}" reiniciados.',
                'total_jogadores': len(novos_cartoes)
            })
        else:
            return jsonify({'error': 'Falha ao salvar os cartões'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar: {str(e)}'}), 500