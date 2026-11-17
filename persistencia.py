"""Leitura e gravacao de arquivos na pasta data/ (RF15, RNF07)."""

import csv
import json
import os

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CAMPOS_MOVIMENTO = ["item", "data", "tipo", "quantidade", "saldo", "documento"]


def _caminho(nome_arquivo):
    """Monta o caminho completo de um arquivo dentro de data/."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    return os.path.join(PASTA_DADOS, nome_arquivo)


def carregar_json(nome_arquivo, padrao=None):
    """Carrega um JSON; se faltar ou estiver corrompido, devolve o padrao."""
    if padrao is None:
        padrao = {}
    caminho = _caminho(nome_arquivo)
    if not os.path.exists(caminho):
        return padrao
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"AVISO: nao foi possivel ler {nome_arquivo} ({erro}).")
        return padrao


def salvar_json(nome_arquivo, dados):
    """Grava um JSON de forma segura (arquivo temporario + substituicao)."""
    caminho = _caminho(nome_arquivo)
    temporario = caminho + ".tmp"
    try:
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)
    except OSError as erro:
        print(f"ERRO: falha ao gravar {nome_arquivo} ({erro}).")


def carregar_movimentos(nome_arquivo="movimentos.csv"):
    """Carrega o historico de movimentacoes (kardex) como lista de dicts."""
    caminho = _caminho(nome_arquivo)
    if not os.path.exists(caminho):
        return []
    movimentos = []
    try:
        with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                linha["quantidade"] = float(linha["quantidade"])
                linha["saldo"] = float(linha["saldo"])
                movimentos.append(linha)
    except (OSError, ValueError, KeyError) as erro:
        print(f"AVISO: nao foi possivel ler {nome_arquivo} ({erro}).")
    return movimentos


def adicionar_movimento(movimento, nome_arquivo="movimentos.csv"):
    """Acrescenta uma linha ao kardex (RN10: nunca se apaga nem reescreve)."""
    caminho = _caminho(nome_arquivo)
    novo = not os.path.exists(caminho)
    try:
        with open(caminho, "a", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_MOVIMENTO)
            if novo:
                escritor.writeheader()
            escritor.writerow(movimento)
    except OSError as erro:
        print(f"ERRO: falha ao gravar {nome_arquivo} ({erro}).")


def exportar_csv(nome_arquivo, campos, linhas):
    """Exporta uma lista de dicts para CSV (usado em relatorios, RF14).

    Usa ';' como separador e UTF-8 com BOM, para abrir direto no Excel.
    """
    caminho = _caminho(nome_arquivo)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho
