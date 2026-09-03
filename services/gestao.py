import os
import csv
from datetime import datetime

def ler_csv(arquivo, separador=';'):
    if not os.path.exists(arquivo):
        return []
    with open(arquivo, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=separador)
        return list(reader)

def escrever_csv(arquivo, dados, fieldnames, separador=';'):
    with open(arquivo, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=separador)
        writer.writeheader()
        writer.writerows(dados)

def proximo_id(arquivo, separador=';'):
    dados = ler_csv(arquivo, separador)
    if not dados:
        return 1
    ids = [int(r['id']) for r in dados if r['id'].isdigit()]
    return max(ids) + 1 if ids else 1

def data_atual_str():
    return datetime.now().strftime('%Y-%m-%d')