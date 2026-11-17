"""Base de demonstracao da fabrica ficticia Pedal Forte (RNF09).

Cria 2 PA, 2 SA, 8 MP, 3 centros de trabalho, estrutura, roteiros, estoque
inicial (com kardex) e um MPS de 8 semanas. Tudo passa pelas funcoes de
negocio dos modulos, entao os dados respeitam as mesmas regras (RN01 a RN10).
"""

import capacidade
import estoque
import estrutura as bom
import itens as cadastro
import mps
import persistencia

# codigo: (descricao, unidade, custo, lead_time, seguranca, lote_minimo)
ITENS = {
    "PA-001": ("Bicicleta Aro 29 MTB", "un", 0, 1, 0, 10),
    "PA-002": ("Bicicleta Aro 29 Urbana", "un", 0, 1, 0, 10),
    "SA-010": ("Quadro aro 29 soldado", "un", 0, 1, 5, 20),
    "SA-020": ("Roda aro 29 montada", "un", 0, 1, 10, 80),
    "MP-100": ("Tubo de aco carbono", "m", 28, 2, 30, 300),
    "MP-101": ("Tinta epoxi", "L", 20, 1, 5, 20),
    "MP-200": ("Aro 29 aluminio", "un", 45, 2, 20, 100),
    "MP-201": ("Raio inox", "un", 0.5, 2, 200, 2000),
    "MP-202": ("Pneu 29 x 2.20", "un", 62.8, 1, 20, 100),
    "MP-300": ("Guidao", "un", 45, 1, 10, 50),
    "MP-301": ("Kit transmissao 12v", "un", 320, 2, 10, 50),
    "MP-302": ("Selim", "un", 38, 1, 10, 50),
}

# (pai, componente, quantidade por unidade)
ESTRUTURA = [
    ("PA-001", "SA-010", 1), ("PA-001", "SA-020", 2),
    ("PA-001", "MP-300", 1), ("PA-001", "MP-301", 1),
    ("PA-002", "SA-010", 1), ("PA-002", "SA-020", 2),
    ("PA-002", "MP-300", 1), ("PA-002", "MP-302", 1),
    ("SA-010", "MP-100", 3), ("SA-010", "MP-101", 0.5),
    ("SA-020", "MP-200", 1), ("SA-020", "MP-201", 36),
    ("SA-020", "MP-202", 1),
]

# codigo: (nome, capacidade h/semana, custo-hora)
CENTROS = {
    "CT-01": ("Soldagem de quadros", 40, 34),
    "CT-02": ("Montagem de rodas", 30, 28),
    "CT-03": ("Montagem final", 16, 40),
}

# item fabricado: (centro, horas por unidade)
ROTEIROS = {
    "SA-010": ("CT-01", 1.0),
    "SA-020": ("CT-02", 0.5),
    "PA-001": ("CT-03", 0.5),
    "PA-002": ("CT-03", 0.4),
}

# (item, tipo, quantidade, data, documento): saldo inicial e historico
MOVIMENTOS = [
    ("MP-202", "ENTRADA", 60, "01/10/2026", "NF 4521 - Pneus Minas"),
    ("MP-202", "SAIDA", 40, "05/10/2026", "OP-0003 (SA-020)"),
    ("MP-202", "AJUSTE", -2, "07/10/2026", "Inventario mensal"),
    ("PA-001", "ENTRADA", 5, "01/10/2026", "Saldo inicial"),
    ("SA-010", "ENTRADA", 40, "01/10/2026", "Saldo inicial"),
    ("SA-020", "ENTRADA", 40, "01/10/2026", "Saldo inicial"),
    ("MP-100", "ENTRADA", 600, "01/10/2026", "Saldo inicial"),
    ("MP-101", "ENTRADA", 60, "01/10/2026", "Saldo inicial"),
    ("MP-200", "ENTRADA", 300, "01/10/2026", "Saldo inicial"),
    ("MP-201", "ENTRADA", 6000, "01/10/2026", "Saldo inicial"),
    ("MP-300", "ENTRADA", 120, "01/10/2026", "Saldo inicial"),
    ("MP-301", "ENTRADA", 120, "01/10/2026", "Saldo inicial"),
    ("MP-302", "ENTRADA", 60, "01/10/2026", "Saldo inicial"),
]

# produto acabado: demanda das semanas 1 a 8
DEMANDA = {
    "PA-001": [10, 20, 30, 0, 25, 15, 20, 10],
    "PA-002": [0, 10, 0, 15, 0, 10, 0, 10],
}


def criar_base_demo():
    """Gera e grava todos os arquivos da base de demonstracao em data/."""
    dados_itens = {}
    for codigo, (desc, un, custo, lt, es, lote) in ITENS.items():
        cadastro.criar_item(dados_itens, codigo, desc, un, custo, lt, es,
                            lote)
    cadastro.salvar_itens(dados_itens)

    dados_bom = {}
    for pai, filho, qtd in ESTRUTURA:
        bom.adicionar_componente(dados_bom, dados_itens, pai, filho, qtd)
    bom.salvar_estrutura(dados_bom)

    centros = {}
    for codigo, (nome, cap, custo_hora) in CENTROS.items():
        capacidade.criar_centro(centros, codigo, nome, cap, custo_hora)
    capacidade.salvar_centros(centros)

    roteiros = {}
    for codigo, (centro, horas) in ROTEIROS.items():
        capacidade.definir_roteiro(roteiros, dados_itens, centros, codigo,
                                   centro, horas)
    capacidade.salvar_roteiros(roteiros)

    saldos = {}
    for codigo, tipo, qtd, data, documento in MOVIMENTOS:
        movimento = estoque.movimentar(saldos, dados_itens, codigo, tipo,
                                       qtd, data, documento)
        estoque.gravar_movimento(saldos, movimento)

    dados_mps = {}
    for codigo, demanda in DEMANDA.items():
        mps.definir_demanda(dados_mps, dados_itens, codigo, demanda)
    mps.salvar_mps(dados_mps)

    persistencia.salvar_json("ordens.json", {
        "contadores": {"OP": 0, "OC": 0}, "ordens": {}})
