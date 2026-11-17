"""Custo padrao dos itens fabricados: materiais + mao de obra (RF13)."""

import estrutura as bom
import utils


# ---------- Logica (sem input/print) ----------

def mao_de_obra(roteiros, centros, codigo):
    """Custo de mao de obra de uma unidade do item (zero sem roteiro).

    Devolve (centro, horas_por_unidade, custo_hora, custo) ou None.
    """
    roteiro = roteiros.get(codigo)
    if roteiro is None or roteiro["centro"] not in centros:
        return None
    custo_hora = centros[roteiro["centro"]]["custo_hora"]
    horas = roteiro["tempo_unitario"]
    return roteiro["centro"], horas, custo_hora, round(horas * custo_hora, 6)


def custo_unitario(codigo, itens, estrutura, roteiros, centros,
                   avisos=None, _caminho=()):
    """Custo padrao de uma unidade do item, de forma recursiva.

    - MP: custo unitario cadastrado.
    - PA/SA: soma (quantidade x custo padrao do componente) de todos os
      componentes + mao de obra do proprio item (tempo x custo-hora).
    `avisos` recebe os codigos de itens fabricados sem roteiro.
    """
    if codigo in _caminho:
        raise ValueError(f"ciclo detectado na estrutura em {codigo}.")
    item = itens[codigo]
    if item["tipo"] == "MP":
        return item["custo"]
    total = 0.0
    for filho, quantidade in bom.componentes(estrutura, codigo).items():
        total += quantidade * custo_unitario(
            filho, itens, estrutura, roteiros, centros, avisos,
            _caminho + (codigo,))
    detalhe_mo = mao_de_obra(roteiros, centros, codigo)
    if detalhe_mo is None:
        if avisos is not None and codigo not in avisos:
            avisos.append(codigo)
    else:
        total += detalhe_mo[3]
    return round(total, 6)


def detalhar_custo(codigo, itens, estrutura, roteiros, centros):
    """Monta o detalhamento do custo padrao de um item fabricado.

    Devolve dict com: linhas de componentes (codigo, descricao, quantidade,
    custo unitario, total), mao de obra (ou None), total e avisos.
    """
    avisos = []
    linhas = []
    for filho, quantidade in bom.componentes(estrutura, codigo).items():
        custo_un = custo_unitario(filho, itens, estrutura, roteiros,
                                  centros, avisos)
        linhas.append((filho, itens[filho]["descricao"], quantidade,
                       custo_un, round(quantidade * custo_un, 6)))
    total = custo_unitario(codigo, itens, estrutura, roteiros, centros,
                           avisos)
    return {
        "linhas": linhas,
        "mao_de_obra": mao_de_obra(roteiros, centros, codigo),
        "total": total,
        "avisos": avisos,
    }


# ---------- Exibicao ----------

def exibir_custo(codigo, itens, estrutura, roteiros, centros):
    """Mostra o custo padrao de um item (mockup 6.7)."""
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    if itens[codigo]["tipo"] == "MP":
        custo = utils.formatar_moeda(itens[codigo]["custo"])
        print(f"{codigo} e materia-prima: custo unitario cadastrado "
              f"{custo}.")
        return
    if not bom.componentes(estrutura, codigo):
        print(f"ERRO: {codigo} nao tem estrutura cadastrada.")
        return
    detalhe = detalhar_custo(codigo, itens, estrutura, roteiros, centros)
    print(f"\nCUSTO PADRAO - {codigo} {itens[codigo]['descricao']}")
    print(f"{'Item':<8}{'Descricao':<28}{'Qtde':>6}{'Custo un.':>11}"
          f"{'Total':>11}")
    for cod, descricao, qtd, custo_un, total in detalhe["linhas"]:
        print(f"{cod:<8}{descricao[:26]:<28}"
              f"{utils.formatar_quantidade(qtd):>6}"
              f"{utils.formatar_numero(custo_un):>11}"
              f"{utils.formatar_numero(total):>11}")
    if detalhe["mao_de_obra"] is not None:
        centro, horas, custo_hora, custo = detalhe["mao_de_obra"]
        rotulo = f"Mao de obra {centro}"
        print(f"{rotulo:<36}{utils.formatar_quantidade(horas) + ' h':>6}"
              f"{utils.formatar_numero(custo_hora):>11}"
              f"{utils.formatar_numero(custo):>11}")
    print("-" * 64)
    print(f"CUSTO PADRAO TOTAL {utils.formatar_moeda(detalhe['total'])}")
    for aviso in detalhe["avisos"]:
        print(f"AVISO: {aviso} nao tem roteiro; mao de obra nao incluida.")


def consultar_custo_menu(itens, estrutura, roteiros, centros):
    """Pergunta o item e exibe o custo padrao."""
    print("\n--- Custo padrao ---")
    codigo = utils.ler_codigo("Codigo do produto: ")
    exibir_custo(codigo, itens, estrutura, roteiros, centros)
