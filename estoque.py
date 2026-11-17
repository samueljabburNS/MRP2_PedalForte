"""Movimentacoes de estoque, saldo e kardex (RF04, RF05, RN02, RN10)."""

import persistencia
import utils

ARQUIVO_SALDOS = "estoque.json"
TIPOS_MOVIMENTO = {"E": "ENTRADA", "S": "SAIDA", "A": "AJUSTE"}


# ---------- Logica (sem input/print) ----------

def carregar_saldos():
    """Carrega os saldos atuais: {codigo: saldo}."""
    return persistencia.carregar_json(ARQUIVO_SALDOS, {})


def salvar_saldos(saldos):
    """Grava os saldos atuais no arquivo."""
    persistencia.salvar_json(ARQUIVO_SALDOS, saldos)


def saldo_item(saldos, codigo):
    """Saldo atual de um item (zero se nunca teve movimentacao)."""
    return saldos.get(codigo, 0)


def validar_movimento(saldos, itens, codigo, tipo, quantidade, documento):
    """Valida uma movimentacao sem altera-la. Levanta ValueError."""
    if codigo not in itens:
        raise ValueError(f"item {codigo} nao encontrado.")
    if tipo not in TIPOS_MOVIMENTO.values():
        raise ValueError(f"tipo de movimentacao invalido: {tipo}.")
    if not documento.strip():
        raise ValueError("informe o documento ou motivo (obrigatorio).")
    if quantidade == 0:
        raise ValueError("a quantidade nao pode ser zero.")
    if tipo in ("ENTRADA", "SAIDA") and quantidade < 0:
        raise ValueError("para entrada/saida informe quantidade positiva.")
    delta = -quantidade if tipo == "SAIDA" else quantidade
    saldo_atual = saldo_item(saldos, codigo)
    if saldo_atual + delta < 0:  # RN02
        unidade = itens[codigo]["unidade"]
        raise ValueError(
            f"saldo insuficiente (saldo atual: "
            f"{utils.formatar_quantidade(saldo_atual)} {unidade})."
        )


def movimentar(saldos, itens, codigo, tipo, quantidade, data, documento):
    """Aplica uma movimentacao ao saldo e devolve o registro do kardex.

    Entrada soma, saida subtrai e ajuste soma a quantidade informada (que
    pode ser negativa). O saldo nunca fica negativo (RN02).
    """
    validar_movimento(saldos, itens, codigo, tipo, quantidade, documento)
    delta = -quantidade if tipo == "SAIDA" else quantidade
    novo_saldo = round(saldo_item(saldos, codigo) + delta, 6)
    saldos[codigo] = novo_saldo
    return {
        "item": codigo,
        "data": data,
        "tipo": tipo,
        "quantidade": delta,
        "saldo": novo_saldo,
        "documento": documento.strip(),
    }


def gravar_movimento(saldos, movimento):
    """Persiste o novo saldo e acrescenta a linha ao kardex (RN10)."""
    salvar_saldos(saldos)
    persistencia.adicionar_movimento(movimento)


def kardex_item(movimentos, codigo):
    """Filtra o historico de movimentacoes de um item (ordem de registro)."""
    return [m for m in movimentos if m["item"] == codigo]


def abaixo_do_seguranca(saldos, itens, codigo):
    """True se o saldo estiver abaixo do estoque de seguranca (RF05)."""
    return saldo_item(saldos, codigo) < itens[codigo]["estoque_seguranca"]


def posicao_estoque(saldos, itens):
    """Lista a posicao de todos os itens (usada em CSV e graficos)."""
    posicao = []
    for codigo in sorted(itens):
        item = itens[codigo]
        saldo = saldo_item(saldos, codigo)
        posicao.append({
            "item": codigo,
            "descricao": item["descricao"],
            "unidade": item["unidade"],
            "saldo": saldo,
            "estoque_seguranca": item["estoque_seguranca"],
            "abaixo_seguranca": saldo < item["estoque_seguranca"],
        })
    return posicao


# ---------- Interface em modo texto ----------

def registrar_movimento_menu(saldos, itens):
    """Pede os dados e registra uma movimentacao de estoque."""
    print("\n--- Movimentar estoque ---")
    codigo = utils.ler_codigo("Codigo do item: ")
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    letra = utils.ler_opcao("Tipo [E]ntrada [S]aida [A]juste: ",
                            TIPOS_MOVIMENTO)
    tipo = TIPOS_MOVIMENTO[letra]
    if tipo == "AJUSTE":
        quantidade = utils.ler_decimal(
            "Quantidade do ajuste (negativa para reduzir): ")
    else:
        quantidade = utils.ler_decimal("Quantidade: ", minimo=0)
    data = utils.ler_data("Data (dd/mm/aaaa, Enter = hoje): ")
    documento = utils.ler_texto("Documento/motivo: ")
    try:
        movimento = movimentar(saldos, itens, codigo, tipo, quantidade,
                               data, documento)
    except ValueError as erro:
        print(f"ERRO: {erro} Operacao cancelada.")
        return
    gravar_movimento(saldos, movimento)
    unidade = itens[codigo]["unidade"]
    print(f"{tipo} registrada. Novo saldo: "
          f"{utils.formatar_quantidade(movimento['saldo'])} {unidade}.")
    if abaixo_do_seguranca(saldos, itens, codigo):
        seguranca = utils.formatar_quantidade(
            itens[codigo]["estoque_seguranca"])
        print("ALERTA: saldo abaixo do estoque de seguranca "
              f"({seguranca} {unidade}).")


def consultar_saldo(saldos, itens):
    """Mostra o saldo atual de um item e o alerta de seguranca."""
    print("\n--- Consultar saldo ---")
    codigo = utils.ler_codigo("Codigo do item: ")
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    item = itens[codigo]
    saldo = utils.formatar_quantidade(saldo_item(saldos, codigo))
    print(f"{codigo} {item['descricao']}: saldo {saldo} {item['unidade']}")
    if abaixo_do_seguranca(saldos, itens, codigo):
        print(f"ALERTA: saldo ({saldo} {item['unidade']}) abaixo do estoque "
              f"de seguranca "
              f"({utils.formatar_quantidade(item['estoque_seguranca'])} "
              f"{item['unidade']}).")


def exibir_kardex(saldos, itens):
    """Mostra o kardex de um item (mockup 6.3)."""
    print("\n--- Kardex ---")
    codigo = utils.ler_codigo("Codigo do item: ")
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    item = itens[codigo]
    historico = kardex_item(persistencia.carregar_movimentos(), codigo)
    print(f"\nKARDEX - {codigo} {item['descricao']} ({item['unidade']})")
    print(f"{'Data':<12}{'Tipo':<9}{'Qtde':>8}{'Saldo':>8}  Documento")
    if not historico:
        print("(sem movimentacoes)")
    for mov in historico:
        print(f"{mov['data']:<12}{mov['tipo']:<9}"
              f"{utils.formatar_quantidade(mov['quantidade'], True):>8}"
              f"{utils.formatar_quantidade(mov['saldo']):>8}  "
              f"{mov['documento']}")
    if abaixo_do_seguranca(saldos, itens, codigo):
        saldo = utils.formatar_quantidade(saldo_item(saldos, codigo))
        seguranca = utils.formatar_quantidade(item["estoque_seguranca"])
        print(f"ALERTA: saldo ({saldo} {item['unidade']}) abaixo do estoque "
              f"de seguranca ({seguranca} {item['unidade']}).")
