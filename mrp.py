"""Calculo MRP: necessidades, ordens planejadas e registro por item.

Formulas (RN05 e RN06), para a semana t:
    NL(t)  = max(0, NB(t) + ES - (EP(t-1) + RP(t)))
    RPl(t) = max(NL(t), lote minimo)   se NL(t) > 0
    EP(t)  = EP(t-1) + RP(t) + RPl(t) - NB(t)
    liberacao = semana do recebimento planejado - lead time   (RN07)
"""

import itens as cadastro
import mps
import ordens
import estrutura as bom
import utils

ORDEM_DE_PROCESSAMENTO = ("PA", "SA", "MP")  # RN04
HORIZONTE = mps.HORIZONTE


# ---------- Calculo de um item (funcao pura) ----------

def calcular_registro(item, necessidade_bruta, receb_programados,
                      estoque_inicial):
    """Calcula o registro MRP de um item para as semanas do horizonte.

    Devolve um dicionario com as linhas do registro (listas por semana) e
    a lista `planejados` de tuplas (semana_entrega, semana_liberacao, qtd).
    """
    seguranca = item["estoque_seguranca"]
    lote_minimo = item["lote_minimo"]
    lead_time = item["lead_time"]

    registro = {
        "estoque_inicial": estoque_inicial,
        "nb": list(necessidade_bruta),
        "rp": list(receb_programados),
        "ep": [], "nl": [], "rpl": [], "lib": [0] * HORIZONTE,
        "planejados": [],
    }
    ep_anterior = estoque_inicial
    for semana in range(1, HORIZONTE + 1):
        nb = necessidade_bruta[semana - 1]
        rp = receb_programados[semana - 1]
        nl = round(max(0, nb + seguranca - (ep_anterior + rp)), 6)  # RN05
        rpl = round(max(nl, lote_minimo), 6) if nl > 0 else 0       # RN06
        ep = round(ep_anterior + rp + rpl - nb, 6)
        if rpl > 0:
            liberacao = semana - lead_time                          # RN07
            registro["planejados"].append((semana, liberacao, rpl))
            if 1 <= liberacao <= HORIZONTE:
                registro["lib"][liberacao - 1] += rpl
        registro["nl"].append(nl)
        registro["rpl"].append(rpl)
        registro["ep"].append(ep)
        ep_anterior = ep
    return registro


# ---------- Execucao para todos os itens ----------

def _acumular_demanda_dependente(demanda, estrutura, pai, quantidade,
                                 semana):
    """Soma nos componentes do pai a demanda gerada por uma liberacao.

    Liberacoes atrasadas (semana < 1) contam na semana 1: os componentes
    sao necessarios o quanto antes. Liberacoes alem do horizonte sao
    ignoradas.
    """
    if semana > HORIZONTE:
        return
    semana = max(semana, 1)
    for componente, por_unidade in bom.componentes(estrutura, pai).items():
        linha = demanda.setdefault(componente, [0] * HORIZONTE)
        linha[semana - 1] = round(
            linha[semana - 1] + por_unidade * quantidade, 6)


def _demanda_de_ordens_abertas(demanda, estrutura, dados_ordens, codigo):
    """Demanda de componentes das ordens FIRMES e LIBERADAS do item.

    Os componentes so saem do estoque no apontamento (RF11); por isso uma
    OP LIBERADA ainda nao apontada continua demandando componentes.
    """
    for ordem in dados_ordens["ordens"].values():
        if ordem["item"] != codigo or ordem["tipo"] != "OP":
            continue
        if ordem["status"] == "FIRME":
            semana = ordem["semana_liberacao"]
        elif ordem["status"] == "LIBERADA":
            semana = 1
        else:
            continue
        _acumular_demanda_dependente(demanda, estrutura, codigo,
                                     ordem["quantidade"], semana)


def executar_mrp(itens, estrutura, mps_dados, saldos, dados_ordens):
    """Executa o MRP para todos os itens, na ordem PA -> SA -> MP (RN04).

    Apaga as ordens PLANEJADAS antes (RN08), calcula os registros e cria as
    novas ordens planejadas em `dados_ordens`. Devolve {codigo: registro}.
    """
    ordens.apagar_planejadas(dados_ordens)
    demanda_dependente = {}
    registros = {}

    for tipo in ORDEM_DE_PROCESSAMENTO:
        for codigo in sorted(c for c in itens if itens[c]["tipo"] == tipo):
            item = itens[codigo]
            if tipo == "PA":
                bruta = list(mps.demanda_item(mps_dados, codigo))
            else:
                bruta = demanda_dependente.get(codigo, [0] * HORIZONTE)
            registro = calcular_registro(
                item, bruta,
                ordens.recebimentos_programados(dados_ordens, codigo),
                estoque_inicial=saldos.get(codigo, 0))

            tipo_ordem = "OP" if cadastro.eh_fabricado(item) else "OC"
            registro["ordens"] = []
            for entrega, liberacao, qtd in registro["planejados"]:
                nova = ordens.criar_ordem_planejada(
                    dados_ordens, tipo_ordem, codigo, qtd, liberacao, entrega)
                registro["ordens"].append(nova)
                if tipo_ordem == "OP":
                    _acumular_demanda_dependente(
                        demanda_dependente, estrutura, codigo, qtd, liberacao)
            if tipo_ordem == "OP":
                _demanda_de_ordens_abertas(
                    demanda_dependente, estrutura, dados_ordens, codigo)
            registros[codigo] = registro
    return registros


# ---------- Exibicao ----------

def _linha(rotulo, valores):
    """Formata uma linha do registro com colunas de largura fixa."""
    celulas = "".join(f"{utils.formatar_quantidade(v):>6}" for v in valores)
    return f"{rotulo:<20}{celulas}"


def exibir_registro(itens, registros, codigo):
    """Mostra o registro MRP de um item (mockup 6.4)."""
    if codigo not in registros:
        print(f"ERRO: nao ha registro MRP para {codigo}. "
              "Execute o MRP e informe um item cadastrado.")
        return
    item = itens[codigo]
    registro = registros[codigo]
    print(f"\nREGISTRO MRP - {codigo} {item['descricao']}")
    seguranca = utils.formatar_quantidade(item["estoque_seguranca"])
    lote = utils.formatar_quantidade(item["lote_minimo"])
    estoque = utils.formatar_quantidade(registro["estoque_inicial"])
    print(f"Lead time: {item['lead_time']} sem | Est. seguranca: "
          f"{seguranca} | Lote min.: {lote} | Estoque: {estoque}")
    print(_linha("Semana", range(1, HORIZONTE + 1)))
    print(_linha("Necessidade bruta", registro["nb"]))
    print(_linha("Receb. programados", registro["rp"]))
    print(_linha("Estoque projetado", registro["ep"]))
    print(_linha("Necessidade liquida", registro["nl"]))
    print(_linha("Receb. planejados", registro["rpl"]))
    print(_linha("Liberacao planejada", registro["lib"]))


def executar_mrp_menu(itens, estrutura, mps_dados, saldos, dados_ordens):
    """Executa o MRP, grava as ordens e mostra o resultado."""
    print("\n--- Executar MRP ---")
    if not mps_dados:
        print("AVISO: o MPS esta vazio; so havera necessidade se houver "
              "ordens ou estoque abaixo da seguranca.")
    registros = executar_mrp(itens, estrutura, mps_dados, saldos,
                             dados_ordens)
    ordens.salvar_ordens(dados_ordens)
    ordens.exibir_ordens(
        dados_ordens,
        f"ORDENS PLANEJADAS - execucao do MRP em {utils.data_hoje()}")
    return registros


def consultar_registro_menu(itens, registros):
    """Pergunta o item e exibe seu registro MRP."""
    print("\n--- Registro MRP de um item ---")
    if not registros:
        print("ERRO: execute o MRP primeiro (opcao 4 do menu).")
        return
    codigo = utils.ler_codigo("Codigo do item: ")
    exibir_registro(itens, registros, codigo)
