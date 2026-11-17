"""Menus e navegacao do sistema (RF01)."""

import base_demo
import capacidade
import custos
import estoque
import estrutura
import graficos
import itens
import mps
import mrp
import ordens
import relatorios
import utils

LARGURA = 50


# ---------- Estado do sistema ----------

def carregar_estado():
    """Carrega todos os dados de data/ (RF15) em um unico dicionario."""
    return {
        "itens": itens.carregar_itens(),
        "estrutura": estrutura.carregar_estrutura(),
        "saldos": estoque.carregar_saldos(),
        "mps": mps.carregar_mps(),
        "ordens": ordens.carregar_ordens(),
        "centros": capacidade.carregar_centros(),
        "roteiros": capacidade.carregar_roteiros(),
        "registros": {},  # registros MRP da ultima execucao (em memoria)
    }


# ---------- Apoio de navegacao ----------

def _titulo(texto):
    """Imprime um titulo entre linhas de '='."""
    print("\n" + "=" * LARGURA)
    print(texto)
    print("=" * LARGURA)


def _executar_acao(acao):
    """Executa uma acao de menu sem deixar um erro inesperado derrubar o
    sistema. Interrupcoes do usuario (Ctrl+C / fim da entrada) sobem."""
    try:
        acao()
    except EOFError:
        raise
    except Exception as erro:  # ultima barreira da interface (RNF05)
        print(f"ERRO inesperado: {erro}")


def _rodar_submenu(titulo, opcoes):
    """Exibe um submenu numerado e executa a opcao escolhida em laco.

    `opcoes` e uma lista de (rotulo, funcao_sem_argumentos).
    """
    while True:
        _titulo(titulo)
        for numero, (rotulo, _) in enumerate(opcoes, start=1):
            print(f"{numero}. {rotulo}")
        print("0. Voltar")
        print("-" * LARGURA)
        escolha = utils.ler_inteiro("Escolha uma opcao: ", 0, len(opcoes))
        if escolha == 0:
            return
        _executar_acao(opcoes[escolha - 1][1])
        utils.pausar()


# ---------- Submenus ----------

def menu_cadastros(e):
    """1. Cadastros: itens, estrutura, centros e roteiros."""
    _rodar_submenu("CADASTROS", [
        ("Cadastrar item", lambda: itens.cadastrar_item(e["itens"])),
        ("Listar itens", lambda: itens.listar_itens(e["itens"])),
        ("Alterar item", lambda: itens.alterar_item(e["itens"])),
        ("Cadastrar estrutura de produto (BOM)",
         lambda: estrutura.cadastrar_componentes(e["itens"],
                                                 e["estrutura"])),
        ("Remover componente da estrutura",
         lambda: estrutura.remover_componente_menu(e["estrutura"])),
        ("Exibir estrutura indentada (explosao da BOM)",
         lambda: estrutura.consultar_arvore(e["itens"], e["estrutura"])),
        ("Cadastrar centro de trabalho",
         lambda: capacidade.cadastrar_centro_menu(e["centros"])),
        ("Listar centros de trabalho",
         lambda: capacidade.listar_centros(e["centros"])),
        ("Definir roteiro de operacao",
         lambda: capacidade.definir_roteiro_menu(
             e["roteiros"], e["itens"], e["centros"])),
        ("Listar roteiros",
         lambda: capacidade.listar_roteiros(e["roteiros"], e["itens"])),
    ])


def menu_estoque(e):
    """2. Estoque: movimentar, saldo e kardex."""
    _rodar_submenu("ESTOQUE", [
        ("Movimentar estoque (entrada, saida, ajuste)",
         lambda: estoque.registrar_movimento_menu(e["saldos"], e["itens"])),
        ("Consultar saldo",
         lambda: estoque.consultar_saldo(e["saldos"], e["itens"])),
        ("Kardex de um item",
         lambda: estoque.exibir_kardex(e["saldos"], e["itens"])),
    ])


def menu_mps(e):
    """3. Plano Mestre de Producao."""
    _rodar_submenu("PLANO MESTRE DE PRODUCAO (MPS)", [
        ("Exibir MPS", lambda: mps.exibir_mps(e["mps"], e["itens"])),
        ("Cadastrar demanda de um produto (8 semanas)",
         lambda: mps.cadastrar_demanda(e["mps"], e["itens"])),
        ("Alterar demanda de uma semana",
         lambda: mps.alterar_demanda(e["mps"], e["itens"])),
    ])


def _executar_mrp(e):
    """Executa o MRP e guarda os registros calculados em memoria."""
    if not e["itens"]:
        print("ERRO: nao ha itens cadastrados.")
        return
    e["registros"] = mrp.executar_mrp_menu(
        e["itens"], e["estrutura"], e["mps"], e["saldos"], e["ordens"])


def _consultar_registro(e):
    """Mostra o registro MRP de um item da ultima execucao."""
    if e["registros"]:
        print("(registro da ultima execucao do MRP; execute de novo apos "
              "alterar dados)")
    mrp.consultar_registro_menu(e["itens"], e["registros"])


def menu_mrp(e):
    """4. Executar MRP e consultar registros."""
    _rodar_submenu("MRP", [
        ("Executar MRP (recalcula as ordens planejadas)",
         lambda: _executar_mrp(e)),
        ("Registro MRP de um item", lambda: _consultar_registro(e)),
    ])


def menu_ordens(e):
    """5. Ordens de producao e de compra: firmar, liberar, apontar."""
    while True:
        ordens.exibir_ordens(e["ordens"])
        print("\n[F] Firmar [L] Liberar [A] Apontar producao "
              "[E] Encerrar OC [V] Voltar")
        escolha = utils.ler_opcao("Escolha: ", ["F", "L", "A", "E", "V"])
        if escolha == "V":
            return
        acoes = {
            "F": lambda: ordens.firmar_menu(e["ordens"]),
            "L": lambda: ordens.liberar_menu(e["ordens"]),
            "A": lambda: ordens.apontar_menu(
                e["ordens"], e["itens"], e["estrutura"], e["saldos"]),
            "E": lambda: ordens.encerrar_oc_menu(
                e["ordens"], e["itens"], e["saldos"]),
        }
        _executar_acao(acoes[escolha])
        utils.pausar()


def menu_crp(e):
    """6. Carga x capacidade."""
    _rodar_submenu("CARGA x CAPACIDADE (CRP)", [
        ("Exibir carga x capacidade de um centro",
         lambda: capacidade.exibir_crp_menu(
             e["ordens"], e["roteiros"], e["centros"])),
    ])


def menu_custos(e):
    """7. Custo padrao dos produtos."""
    _rodar_submenu("CUSTO PADRAO", [
        ("Consultar custo padrao de um item",
         lambda: custos.consultar_custo_menu(
             e["itens"], e["estrutura"], e["roteiros"], e["centros"])),
    ])


def menu_relatorios(e):
    """8. Relatorios em CSV."""
    _rodar_submenu("RELATORIOS (EXPORTAR CSV)", [
        ("Exportar posicao de estoque",
         lambda: relatorios.exportar_estoque_menu(e["saldos"], e["itens"])),
        ("Exportar lista de ordens",
         lambda: relatorios.exportar_ordens_menu(e["ordens"], e["itens"])),
    ])


def menu_graficos(e):
    """9. Graficos de gestao (matplotlib)."""
    _rodar_submenu("GRAFICOS DE GESTAO", [
        ("Posicao de estoque (saldo x seguranca)",
         lambda: graficos.grafico_estoque_menu(e["saldos"], e["itens"])),
        ("Estoque projetado de um item (8 semanas)",
         lambda: graficos.grafico_projetado_menu(
             e["registros"], e["itens"])),
        ("Ordens por semana de entrega (OP x OC)",
         lambda: graficos.grafico_ordens_menu(e["ordens"])),
        ("Carga x capacidade de um centro",
         lambda: graficos.grafico_crp_menu(
             e["ordens"], e["roteiros"], e["centros"])),
    ])


# ---------- Menu principal ----------

def exibir_menu_principal():
    """Imprime o menu principal (mockup 6.1)."""
    print("\n" + "=" * LARGURA)
    print("MRP II - PEDAL FORTE BICICLETAS")
    print("=" * LARGURA)
    print("1. Cadastros (itens, estrutura, centros, roteiros)")
    print("2. Estoque (movimentar, saldo, kardex)")
    print("3. Plano Mestre de Producao (MPS)")
    print("4. Executar MRP")
    print("5. Ordens de producao e de compra")
    print("6. Carga x capacidade (CRP)")
    print("7. Custo padrao dos produtos")
    print("8. Relatorios (exportar CSV)")
    print("9. Graficos de gestao (matplotlib)")
    print("0. Sair")
    print("-" * LARGURA)


def menu_principal(estado):
    """Laco do menu principal ate o usuario escolher sair."""
    opcoes = {
        1: menu_cadastros, 2: menu_estoque, 3: menu_mps, 4: menu_mrp,
        5: menu_ordens, 6: menu_crp, 7: menu_custos, 8: menu_relatorios,
        9: menu_graficos,
    }
    while True:
        exibir_menu_principal()
        escolha = utils.ler_inteiro("Escolha uma opcao: ", 0, 9)
        if escolha == 0:
            return
        opcoes[escolha](estado)


def iniciar():
    """Carrega os dados e abre o menu principal."""
    estado = carregar_estado()
    if not estado["itens"]:
        print("Nenhum dado encontrado na pasta data/.")
        resposta = utils.ler_opcao(
            "Carregar a base de demonstracao da Pedal Forte? [S/N]: ",
            ["S", "N"])
        if resposta == "S":
            base_demo.criar_base_demo()
            estado = carregar_estado()
            print("Base de demonstracao criada.")
    menu_principal(estado)
    print("\nSistema encerrado.")
