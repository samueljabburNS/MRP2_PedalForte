"""Cadastro de itens: PA, SA e MP (RF02, RN01)."""

import persistencia
import utils

ARQUIVO = "itens.json"
UNIDADES = ("un", "m", "L", "kg")
CAMPOS_ALTERAVEIS = {
    "1": ("descricao", "Descricao"),
    "2": ("unidade", "Unidade de medida"),
    "3": ("custo", "Custo unitario"),
    "4": ("lead_time", "Lead time (semanas)"),
    "5": ("estoque_seguranca", "Estoque de seguranca"),
    "6": ("lote_minimo", "Lote minimo"),
}


# ---------- Logica (sem input/print, facil de testar) ----------

def carregar_itens():
    """Carrega o dicionario de itens {codigo: dados} do arquivo."""
    return persistencia.carregar_json(ARQUIVO, {})


def salvar_itens(itens):
    """Grava o dicionario de itens no arquivo."""
    persistencia.salvar_json(ARQUIVO, itens)


def criar_item(itens, codigo, descricao, unidade, custo, lead_time,
               estoque_seguranca, lote_minimo):
    """Adiciona um item ao dicionario, validando RN01. Levanta ValueError."""
    if not utils.codigo_valido(codigo):
        raise ValueError("codigo invalido (use o formato PA-001).")
    if codigo in itens:
        raise ValueError(f"o codigo {codigo} ja esta cadastrado.")
    if not descricao.strip():
        raise ValueError("a descricao nao pode ficar vazia.")
    if min(custo, lead_time, estoque_seguranca, lote_minimo) < 0:
        raise ValueError("valores numericos nao podem ser negativos.")
    itens[codigo] = {
        "descricao": descricao.strip(),
        "tipo": utils.tipo_do_codigo(codigo),
        "unidade": unidade,
        "custo": custo,
        "lead_time": lead_time,
        "estoque_seguranca": estoque_seguranca,
        "lote_minimo": lote_minimo,
    }
    return itens[codigo]


def eh_fabricado(item):
    """PA e SA sao fabricados; MP e comprada (RN01)."""
    return item["tipo"] in ("PA", "SA")


# ---------- Interface em modo texto ----------

def cadastrar_item(itens):
    """Pede os dados ao usuario e cadastra um novo item."""
    print("\n--- Cadastrar item ---")
    codigo = utils.ler_codigo("Codigo (ex.: PA-001): ")
    if codigo in itens:
        print(f"ERRO: o codigo {codigo} ja esta cadastrado.")
        return
    descricao = utils.ler_texto("Descricao: ")
    unidade = utils.ler_opcao(f"Unidade {list(UNIDADES)}: ", UNIDADES).lower()
    if unidade == "l":
        unidade = "L"
    custo = utils.ler_decimal("Custo unitario (R$): ", minimo=0)
    lead_time = utils.ler_inteiro("Lead time (semanas): ", minimo=0)
    estoque_seguranca = utils.ler_decimal("Estoque de seguranca: ", minimo=0)
    lote_minimo = utils.ler_decimal("Lote minimo: ", minimo=0)
    try:
        criar_item(itens, codigo, descricao, unidade, custo, lead_time,
                   estoque_seguranca, lote_minimo)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_itens(itens)
    print(f"Item {codigo} cadastrado com sucesso.")


def listar_itens(itens):
    """Exibe todos os itens em formato de tabela, ordenados por codigo."""
    print("\n--- Itens cadastrados ---")
    if not itens:
        print("Nenhum item cadastrado.")
        return
    print(f"{'Codigo':<8}{'Descricao':<30}{'Un':<4}{'Custo':>10}"
          f"{'LT':>4}{'ES':>8}{'Lote':>8}")
    for codigo in sorted(itens):
        i = itens[codigo]
        print(f"{codigo:<8}{i['descricao'][:28]:<30}{i['unidade']:<4}"
              f"{utils.formatar_numero(i['custo']):>10}{i['lead_time']:>4}"
              f"{utils.formatar_numero(i['estoque_seguranca'], 1):>8}"
              f"{utils.formatar_numero(i['lote_minimo'], 1):>8}")


def alterar_item(itens):
    """Altera um campo de um item ja cadastrado (codigo e tipo sao fixos)."""
    print("\n--- Alterar item ---")
    codigo = utils.ler_codigo("Codigo do item: ")
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    for chave, (_, rotulo) in CAMPOS_ALTERAVEIS.items():
        print(f"{chave}. {rotulo}")
    escolha = utils.ler_opcao("Campo a alterar: ", CAMPOS_ALTERAVEIS)
    campo, rotulo = CAMPOS_ALTERAVEIS[escolha]
    if campo == "descricao":
        itens[codigo][campo] = utils.ler_texto("Nova descricao: ")
    elif campo == "unidade":
        nova = utils.ler_opcao(f"Nova unidade {list(UNIDADES)}: ", UNIDADES)
        itens[codigo][campo] = "L" if nova == "L" else nova.lower()
    elif campo == "lead_time":
        itens[codigo][campo] = utils.ler_inteiro(f"Novo {rotulo}: ", minimo=0)
    else:
        itens[codigo][campo] = utils.ler_decimal(f"Novo {rotulo}: ", minimo=0)
    salvar_itens(itens)
    print(f"Item {codigo} atualizado.")
