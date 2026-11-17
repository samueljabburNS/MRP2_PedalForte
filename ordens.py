"""Ordens de producao (OP) e de compra (OC) e apontamento (RF09 a RF11)."""

import re

import estoque
import estrutura as bom
import mps
import persistencia
import utils

ARQUIVO = "ordens.json"
STATUS_ABERTOS_PLANEJADOS = ("PLANEJADA", "ATRASADA")
STATUS_CONFIRMADOS = ("FIRME", "LIBERADA")  # entram como recebimento (RN08)
PADRAO_NUMERO = re.compile(r"^(OP|OC)-(\d+)$")


# ---------- Logica (sem input/print) ----------

def carregar_ordens():
    """Carrega o arquivo de ordens: contadores por tipo e dict de ordens."""
    padrao = {"contadores": {"OP": 0, "OC": 0}, "ordens": {}}
    dados = persistencia.carregar_json(ARQUIVO, padrao)
    dados.setdefault("contadores", {"OP": 0, "OC": 0})
    dados.setdefault("ordens", {})
    return dados


def salvar_ordens(dados):
    """Grava as ordens no arquivo."""
    persistencia.salvar_json(ARQUIVO, dados)


def normalizar_numero(texto):
    """Converte 'op-3' ou 'OP-0003' no formato padrao 'OP-0003'."""
    encontrado = PADRAO_NUMERO.match(texto.strip().upper())
    if not encontrado:
        raise ValueError("numero de ordem invalido (use OP-0001 ou OC-0001).")
    return f"{encontrado.group(1)}-{int(encontrado.group(2)):04d}"


def obter_ordem(dados, numero):
    """Devolve a ordem pelo numero. Levanta ValueError se nao existir."""
    numero = normalizar_numero(numero)
    if numero not in dados["ordens"]:
        raise ValueError(f"ordem {numero} nao encontrada.")
    return dados["ordens"][numero]


def criar_ordem_planejada(dados, tipo, item, quantidade,
                          semana_liberacao, semana_entrega):
    """Cria uma ordem PLANEJADA (ou ATRASADA, se liberar antes da semana 1).

    Regra RN07: liberacao antes da semana 1 marca a ordem como ATRASADA.
    """
    dados["contadores"][tipo] += 1
    numero = f"{tipo}-{dados['contadores'][tipo]:04d}"
    status = "ATRASADA" if semana_liberacao < 1 else "PLANEJADA"
    dados["ordens"][numero] = {
        "numero": numero,
        "tipo": tipo,
        "item": item,
        "quantidade": quantidade,
        "semana_liberacao": semana_liberacao,
        "semana_entrega": semana_entrega,
        "status": status,
    }
    return dados["ordens"][numero]


def apagar_planejadas(dados):
    """Remove as ordens PLANEJADAS/ATRASADAS antes de recalcular (RN08)."""
    dados["ordens"] = {
        numero: ordem for numero, ordem in dados["ordens"].items()
        if ordem["status"] not in STATUS_ABERTOS_PLANEJADOS
    }


def listar_ordens_ordenadas(dados, status=None):
    """Lista as ordens ordenadas por numero, com filtro opcional de status."""
    ordens = [dados["ordens"][n] for n in sorted(dados["ordens"])]
    if status is not None:
        ordens = [o for o in ordens if o["status"] in status]
    return ordens


def recebimentos_programados(dados, codigo, horizonte=mps.HORIZONTE):
    """Recebimentos por semana de um item, vindos de ordens FIRMES ou
    LIBERADAS (RN08). Devolve lista com `horizonte` posicoes."""
    recebimentos = [0] * horizonte
    for ordem in dados["ordens"].values():
        semana = ordem["semana_entrega"]
        if (ordem["item"] == codigo
                and ordem["status"] in STATUS_CONFIRMADOS
                and 1 <= semana <= horizonte):
            recebimentos[semana - 1] += ordem["quantidade"]
    return recebimentos


def firmar_ordem(dados, numero):
    """PLANEJADA (ou ATRASADA) -> FIRME."""
    ordem = obter_ordem(dados, numero)
    if ordem["status"] not in STATUS_ABERTOS_PLANEJADOS:
        raise ValueError(
            f"{ordem['numero']} esta {ordem['status']}; so e possivel firmar "
            "ordens PLANEJADAS.")
    ordem["status"] = "FIRME"
    return ordem


def liberar_ordem(dados, numero):
    """FIRME -> LIBERADA."""
    ordem = obter_ordem(dados, numero)
    if ordem["status"] != "FIRME":
        raise ValueError(
            f"{ordem['numero']} esta {ordem['status']}; so e possivel "
            "liberar ordens FIRMES.")
    ordem["status"] = "LIBERADA"
    return ordem


def encerrar_oc(dados, itens, saldos, numero, data):
    """Encerra uma OC LIBERADA: da entrada da materia-prima no estoque.

    Devolve o movimento de estoque (o chamador persiste com
    estoque.gravar_movimento). OP so e encerrada pelo apontamento.
    """
    ordem = obter_ordem(dados, numero)
    if ordem["tipo"] != "OC":
        raise ValueError("OP so e encerrada pelo apontamento de producao.")
    if ordem["status"] != "LIBERADA":
        raise ValueError(
            f"{ordem['numero']} esta {ordem['status']}; so e possivel "
            "encerrar ordens LIBERADAS.")
    movimento = estoque.movimentar(
        saldos, itens, ordem["item"], "ENTRADA", ordem["quantidade"], data,
        f"{ordem['numero']} - recebimento")
    ordem["status"] = "ENCERRADA"
    return movimento


def faltas_de_componentes(estrutura, itens, saldos, ordem):
    """Componentes sem saldo para a OP: lista de (cod, preciso, saldo)."""
    faltas = []
    for componente, por_unidade in bom.componentes(
            estrutura, ordem["item"]).items():
        preciso = round(por_unidade * ordem["quantidade"], 6)
        saldo = estoque.saldo_item(saldos, componente)
        if saldo < preciso:
            faltas.append((componente, preciso, saldo))
    return faltas


def apontar_producao(dados, itens, estrutura, saldos, numero, data):
    """Aponta a producao total de uma OP LIBERADA (RF11).

    Baixa os componentes, da entrada do item produzido e encerra a OP.
    Se faltar qualquer componente, rejeita tudo sem alterar nada.
    Devolve a lista de movimentos (o chamador persiste cada um).
    """
    ordem = obter_ordem(dados, numero)
    if ordem["tipo"] != "OP":
        raise ValueError("apontamento so vale para ordens de producao (OP).")
    if ordem["status"] != "LIBERADA":
        raise ValueError(
            f"{ordem['numero']} esta {ordem['status']}; so e possivel "
            "apontar OP LIBERADA.")
    if not bom.componentes(estrutura, ordem["item"]):
        raise ValueError(f"{ordem['item']} nao tem estrutura cadastrada.")
    faltas = faltas_de_componentes(estrutura, itens, saldos, ordem)
    if faltas:
        detalhes = "; ".join(
            f"{cod} (preciso {utils.formatar_quantidade(preciso)}, saldo "
            f"{utils.formatar_quantidade(saldo)})"
            for cod, preciso, saldo in faltas)
        raise ValueError(f"faltam componentes: {detalhes}.")

    movimentos = []
    for componente, por_unidade in bom.componentes(
            estrutura, ordem["item"]).items():
        movimentos.append(estoque.movimentar(
            saldos, itens, componente, "SAIDA",
            round(por_unidade * ordem["quantidade"], 6), data,
            f"{ordem['numero']} ({ordem['item']})"))
    movimentos.append(estoque.movimentar(
        saldos, itens, ordem["item"], "ENTRADA", ordem["quantidade"], data,
        f"{ordem['numero']} - producao"))
    ordem["status"] = "ENCERRADA"
    return movimentos


def contar_excecoes(dados):
    """Quantidade de ordens ATRASADAS (mensagens de excecao, RN07)."""
    return len(listar_ordens_ordenadas(dados, ("ATRASADA",)))


# ---------- Interface em modo texto ----------

def exibir_ordens(dados, titulo="ORDENS DE PRODUCAO E DE COMPRA"):
    """Mostra a lista de ordens (mockup 6.5)."""
    print(f"\n{titulo}")
    ordens = listar_ordens_ordenadas(dados)
    if not ordens:
        print("Nenhuma ordem cadastrada.")
        return
    print(f"{'Ordem':<9}{'Tipo':<5}{'Item':<8}{'Qtde':>7}"
          f"{'Liberar':>9}{'Entregar':>10}  Status")
    for o in ordens:
        print(f"{o['numero']:<9}{o['tipo']:<5}{o['item']:<8}"
              f"{utils.formatar_quantidade(o['quantidade']):>7}"
              f"{'S' + str(o['semana_liberacao']):>9}"
              f"{'S' + str(o['semana_entrega']):>10}  {o['status']}")
    excecoes = contar_excecoes(dados)
    if excecoes:
        print(f"\n{excecoes} mensagens de excecao: ordens com liberacao "
              "antes da semana 1.")


def _pedir_numero():
    """Le o numero da ordem; repete se o formato for invalido."""
    while True:
        try:
            return normalizar_numero(utils.ler_texto("Numero da ordem: "))
        except ValueError as erro:
            print(f"ERRO: {erro}")


def firmar_menu(dados):
    """Firma uma ordem planejada."""
    try:
        ordem = firmar_ordem(dados, _pedir_numero())
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_ordens(dados)
    print(f"{ordem['numero']} firmada.")


def liberar_menu(dados):
    """Libera uma ordem firme."""
    try:
        ordem = liberar_ordem(dados, _pedir_numero())
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_ordens(dados)
    print(f"{ordem['numero']} liberada.")


def apontar_menu(dados, itens, estrutura, saldos):
    """Aponta a producao de uma OP liberada."""
    numero = _pedir_numero()
    data = utils.ler_data("Data do apontamento (Enter = hoje): ")
    try:
        movimentos = apontar_producao(dados, itens, estrutura, saldos,
                                      numero, data)
    except ValueError as erro:
        print(f"ERRO: {erro} Apontamento cancelado.")
        return
    for movimento in movimentos:
        estoque.gravar_movimento(saldos, movimento)
    salvar_ordens(dados)
    print(f"{numero} apontada e encerrada. Estoque atualizado "
          f"({len(movimentos)} movimentacoes).")


def encerrar_oc_menu(dados, itens, saldos):
    """Encerra (recebe) uma ordem de compra liberada."""
    numero = _pedir_numero()
    data = utils.ler_data("Data do recebimento (Enter = hoje): ")
    try:
        movimento = encerrar_oc(dados, itens, saldos, numero, data)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    estoque.gravar_movimento(saldos, movimento)
    salvar_ordens(dados)
    print(f"{numero} encerrada. Entrada registrada no estoque.")
