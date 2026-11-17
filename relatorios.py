"""Exportacao de relatorios em CSV: posicao de estoque e ordens (RF14)."""

import estoque
import ordens
import persistencia
import utils

ARQUIVO_ESTOQUE = "posicao_estoque.csv"
ARQUIVO_ORDENS = "lista_ordens.csv"
CAMPOS_ESTOQUE = ["item", "descricao", "unidade", "saldo",
                  "estoque_seguranca", "situacao"]
CAMPOS_ORDENS = ["ordem", "tipo", "item", "descricao", "quantidade",
                 "semana_liberacao", "semana_entrega", "status"]


# ---------- Logica (monta as linhas; nao grava nada) ----------

def linhas_estoque(saldos, itens):
    """Linhas do CSV de posicao de estoque (numeros com virgula decimal)."""
    linhas = []
    for pos in estoque.posicao_estoque(saldos, itens):
        linhas.append({
            "item": pos["item"],
            "descricao": pos["descricao"],
            "unidade": pos["unidade"],
            "saldo": utils.formatar_quantidade(pos["saldo"]),
            "estoque_seguranca": utils.formatar_quantidade(
                pos["estoque_seguranca"]),
            "situacao": ("ABAIXO DA SEGURANCA" if pos["abaixo_seguranca"]
                         else "OK"),
        })
    return linhas


def linhas_ordens(dados_ordens, itens):
    """Linhas do CSV com a lista de ordens (OP e OC)."""
    linhas = []
    for ordem in ordens.listar_ordens_ordenadas(dados_ordens):
        linhas.append({
            "ordem": ordem["numero"],
            "tipo": ordem["tipo"],
            "item": ordem["item"],
            "descricao": itens[ordem["item"]]["descricao"],
            "quantidade": utils.formatar_quantidade(ordem["quantidade"]),
            "semana_liberacao": ordem["semana_liberacao"],
            "semana_entrega": ordem["semana_entrega"],
            "status": ordem["status"],
        })
    return linhas


def exportar_estoque(saldos, itens):
    """Grava a posicao de estoque em CSV e devolve o caminho do arquivo."""
    return persistencia.exportar_csv(
        ARQUIVO_ESTOQUE, CAMPOS_ESTOQUE, linhas_estoque(saldos, itens))


def exportar_ordens(dados_ordens, itens):
    """Grava a lista de ordens em CSV e devolve o caminho do arquivo."""
    return persistencia.exportar_csv(
        ARQUIVO_ORDENS, CAMPOS_ORDENS, linhas_ordens(dados_ordens, itens))


# ---------- Interface em modo texto ----------

def exportar_estoque_menu(saldos, itens):
    """Exporta a posicao de estoque e informa onde o arquivo foi salvo."""
    if not itens:
        print("ERRO: nao ha itens cadastrados para exportar.")
        return
    try:
        caminho = exportar_estoque(saldos, itens)
    except OSError as erro:
        print(f"ERRO: nao foi possivel gravar o arquivo ({erro}).")
        return
    print(f"Posicao de estoque exportada para: {caminho}")


def exportar_ordens_menu(dados_ordens, itens):
    """Exporta a lista de ordens e informa onde o arquivo foi salvo."""
    if not dados_ordens["ordens"]:
        print("ERRO: nao ha ordens para exportar. Execute o MRP antes.")
        return
    try:
        caminho = exportar_ordens(dados_ordens, itens)
    except OSError as erro:
        print(f"ERRO: nao foi possivel gravar o arquivo ({erro}).")
        return
    print(f"Lista de ordens exportada para: {caminho}")
