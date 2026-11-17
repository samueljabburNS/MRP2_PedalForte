"""Plano Mestre de Producao: demanda dos PA por semana (RF07)."""

import persistencia
import utils

ARQUIVO = "mps.json"
HORIZONTE = 8  # semanas


# ---------- Logica (sem input/print) ----------

def carregar_mps():
    """Carrega o MPS: {codigo_PA: [demanda_s1, ..., demanda_s8]}."""
    return persistencia.carregar_json(ARQUIVO, {})


def salvar_mps(mps):
    """Grava o MPS no arquivo."""
    persistencia.salvar_json(ARQUIVO, mps)


def demanda_item(mps, codigo):
    """Demanda semanal de um item (zeros se ele nao estiver no MPS)."""
    return mps.get(codigo, [0] * HORIZONTE)


def _validar_pa(itens, codigo):
    """Garante que o item existe e e produto acabado. Levanta ValueError."""
    if codigo not in itens:
        raise ValueError(f"item {codigo} nao encontrado.")
    if itens[codigo]["tipo"] != "PA":
        raise ValueError("o MPS aceita apenas produtos acabados (PA).")


def definir_demanda(mps, itens, codigo, demanda):
    """Define a demanda das 8 semanas de um PA. Levanta ValueError."""
    _validar_pa(itens, codigo)
    if len(demanda) != HORIZONTE:
        raise ValueError(f"informe a demanda das {HORIZONTE} semanas.")
    if any(valor < 0 for valor in demanda):
        raise ValueError("a demanda nao pode ser negativa.")
    mps[codigo] = list(demanda)


def alterar_semana(mps, itens, codigo, semana, quantidade):
    """Altera a demanda de uma unica semana (1 a 8). Levanta ValueError."""
    _validar_pa(itens, codigo)
    if not 1 <= semana <= HORIZONTE:
        raise ValueError(f"a semana deve estar entre 1 e {HORIZONTE}.")
    if quantidade < 0:
        raise ValueError("a demanda nao pode ser negativa.")
    demanda = list(demanda_item(mps, codigo))
    demanda[semana - 1] = quantidade
    mps[codigo] = demanda


# ---------- Interface em modo texto ----------

def exibir_mps(mps, itens):
    """Mostra a demanda semanal de todos os PA cadastrados."""
    print("\n--- Plano Mestre de Producao (MPS) ---")
    produtos = [c for c in sorted(itens) if itens[c]["tipo"] == "PA"]
    if not produtos:
        print("Nenhum produto acabado cadastrado.")
        return
    cabecalho = "".join(f"{'S' + str(s):>6}" for s in range(1, HORIZONTE + 1))
    print(f"{'Item':<9}{'Descricao':<26}{cabecalho}")
    for codigo in produtos:
        valores = "".join(f"{utils.formatar_quantidade(v):>6}"
                          for v in demanda_item(mps, codigo))
        print(f"{codigo:<9}{itens[codigo]['descricao'][:24]:<26}{valores}")


def cadastrar_demanda(mps, itens):
    """Pede a demanda das 8 semanas de um PA e grava no MPS."""
    print("\n--- Cadastrar demanda (MPS) ---")
    codigo = utils.ler_codigo("Codigo do produto acabado: ")
    try:
        _validar_pa(itens, codigo)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    demanda = [
        utils.ler_decimal(f"Demanda da semana {semana}: ", minimo=0)
        for semana in range(1, HORIZONTE + 1)
    ]
    definir_demanda(mps, itens, codigo, demanda)
    salvar_mps(mps)
    print(f"Demanda de {codigo} gravada.")


def alterar_demanda(mps, itens):
    """Altera a demanda de uma semana de um PA ja planejado."""
    print("\n--- Alterar demanda (MPS) ---")
    codigo = utils.ler_codigo("Codigo do produto acabado: ")
    try:
        _validar_pa(itens, codigo)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    semana = utils.ler_inteiro(f"Semana (1 a {HORIZONTE}): ",
                               minimo=1, maximo=HORIZONTE)
    atual = utils.formatar_quantidade(demanda_item(mps, codigo)[semana - 1])
    print(f"Demanda atual da semana {semana}: {atual}")
    quantidade = utils.ler_decimal("Nova demanda: ", minimo=0)
    alterar_semana(mps, itens, codigo, semana, quantidade)
    salvar_mps(mps)
    print(f"Semana {semana} de {codigo} atualizada.")
