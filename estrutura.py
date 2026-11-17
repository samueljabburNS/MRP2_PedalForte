"""Estrutura de produto (BOM) em ate 3 niveis e arvore (RF03, RN03)."""

import persistencia
import utils

ARQUIVO = "estrutura.json"
LARGURA_PONTOS = 40

# Tipos de componente aceitos para cada tipo de pai (RN03).
# MP nao aparece como chave: materia-prima nao possui estrutura.
COMPONENTES_PERMITIDOS = {
    "PA": ("SA", "MP"),
    "SA": ("MP",),
}


# ---------- Logica (sem input/print) ----------

def carregar_estrutura():
    """Carrega a BOM: {pai: {componente: quantidade_por_unidade}}."""
    return persistencia.carregar_json(ARQUIVO, {})


def salvar_estrutura(estrutura):
    """Grava a BOM no arquivo."""
    persistencia.salvar_json(ARQUIVO, estrutura)


def adicionar_componente(estrutura, itens, pai, filho, quantidade):
    """Inclui (ou atualiza) um componente no pai. Levanta ValueError (RN03)."""
    if pai not in itens:
        raise ValueError(f"item pai {pai} nao esta cadastrado.")
    if filho not in itens:
        raise ValueError(f"componente {filho} nao esta cadastrado.")
    tipo_pai = itens[pai]["tipo"]
    tipo_filho = itens[filho]["tipo"]
    if tipo_pai == "MP":
        raise ValueError("materia-prima (MP) nao possui estrutura.")
    if tipo_filho not in COMPONENTES_PERMITIDOS[tipo_pai]:
        permitidos = " ou ".join(COMPONENTES_PERMITIDOS[tipo_pai])
        raise ValueError(
            f"um {tipo_pai} so pode ter componentes do tipo {permitidos} "
            f"({filho} e {tipo_filho})."
        )
    if quantidade <= 0:
        raise ValueError("a quantidade por unidade deve ser maior que zero.")
    estrutura.setdefault(pai, {})[filho] = quantidade


def remover_componente(estrutura, pai, filho):
    """Remove um componente do pai. Levanta ValueError se nao existir."""
    if filho not in estrutura.get(pai, {}):
        raise ValueError(f"{filho} nao e componente de {pai}.")
    del estrutura[pai][filho]
    if not estrutura[pai]:
        del estrutura[pai]


def componentes(estrutura, pai):
    """Devolve {componente: quantidade} do pai (vazio se nao tiver)."""
    return estrutura.get(pai, {})


def explodir(estrutura, codigo, nivel=0, multiplicador=1):
    """Explosao recursiva da BOM.

    Devolve lista de tuplas (nivel, codigo, quantidade_acumulada) em ordem
    de arvore (pre-ordem). A quantidade acumulada e quanto do item e
    necessario para o multiplicador informado do item raiz.
    """
    resultado = [(nivel, codigo, multiplicador)]
    for filho, qtd in componentes(estrutura, codigo).items():
        resultado.extend(explodir(estrutura, filho, nivel + 1,
                                  multiplicador * qtd))
    return resultado


# ---------- Exibicao ----------

def _linha_componente(itens, estrutura, pai, filho, prefixo, ultimo):
    """Monta e imprime uma linha da arvore e desce para os filhos."""
    ramo = "└── " if ultimo else "├── "
    rotulo = f"{filho} {itens[filho]['descricao']} "
    pontos = "." * max(2, LARGURA_PONTOS - len(rotulo))
    qtd = utils.formatar_quantidade(estrutura[pai][filho])
    print(f"{prefixo}{ramo}{rotulo}{pontos} {qtd} {itens[filho]['unidade']}")
    _imprimir_filhos(itens, estrutura, filho,
                     prefixo + ("    " if ultimo else "│   "))


def _imprimir_filhos(itens, estrutura, pai, prefixo=""):
    """Imprime recursivamente os componentes de um pai."""
    filhos = list(componentes(estrutura, pai))
    for posicao, filho in enumerate(filhos):
        _linha_componente(itens, estrutura, pai, filho, prefixo,
                          posicao == len(filhos) - 1)


def resumo_niveis(estrutura, codigo):
    """Texto 'Niveis: 0 = PA-001 | 1 = SA-010, SA-020 | 2 = demais'."""
    por_nivel = {}
    for nivel, cod, _ in explodir(estrutura, codigo):
        por_nivel.setdefault(nivel, [])
        if cod not in por_nivel[nivel]:
            por_nivel[nivel].append(cod)
    partes = []
    for nivel in sorted(por_nivel):
        lista = por_nivel[nivel]
        if nivel >= 2 and len(por_nivel) > 2 and nivel == max(por_nivel):
            partes.append(f"{nivel} = demais")
        else:
            partes.append(f"{nivel} = {', '.join(lista)}")
    return "Niveis: " + " | ".join(partes)


def exibir_arvore(itens, estrutura, codigo):
    """Mostra a explosao indentada da BOM de um item (mockup 6.2)."""
    if codigo not in itens:
        print(f"ERRO: item {codigo} nao encontrado.")
        return
    print(f"\n{codigo} {itens[codigo]['descricao']}")
    _imprimir_filhos(itens, estrutura, codigo)
    if not componentes(estrutura, codigo):
        print("(sem componentes cadastrados)")
    else:
        print(f"\n{resumo_niveis(estrutura, codigo)}")


# ---------- Interface em modo texto ----------

def cadastrar_componentes(itens, estrutura):
    """Cadastra componentes de um item pai, um por vez, ate Enter vazio."""
    print("\n--- Cadastrar estrutura de produto ---")
    pai = utils.ler_codigo("Codigo do item pai: ")
    if pai not in itens:
        print(f"ERRO: item {pai} nao encontrado.")
        return
    if itens[pai]["tipo"] == "MP":
        print("ERRO: materia-prima (MP) nao possui estrutura.")
        return
    while True:
        filho = utils.ler_texto(
            "Codigo do componente (Enter para terminar): ",
            obrigatorio=False).upper()
        if not filho:
            break
        if not utils.codigo_valido(filho):
            print("ERRO: codigo invalido. Use o formato SA-010, MP-201.")
            continue
        quantidade = utils.ler_decimal("Quantidade por unidade: ")
        try:
            adicionar_componente(estrutura, itens, pai, filho, quantidade)
        except ValueError as erro:
            print(f"ERRO: {erro}")
            continue
        salvar_estrutura(estrutura)
        print(f"{filho} adicionado a {pai}.")


def remover_componente_menu(estrutura):
    """Remove um componente de um item pai."""
    print("\n--- Remover componente ---")
    pai = utils.ler_codigo("Codigo do item pai: ")
    filho = utils.ler_codigo("Codigo do componente: ")
    try:
        remover_componente(estrutura, pai, filho)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_estrutura(estrutura)
    print(f"{filho} removido de {pai}.")


def consultar_arvore(itens, estrutura):
    """Pergunta o produto e exibe a arvore indentada."""
    print("\n--- Explosao da BOM ---")
    codigo = utils.ler_codigo("Codigo do produto: ")
    exibir_arvore(itens, estrutura, codigo)
