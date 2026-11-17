"""Graficos de gestao e acompanhamento com matplotlib (RF16).

Cada grafico e exibido na tela e salvo em PNG na pasta graficos_png/.
"""

import os

import capacidade
import estoque
import mps
import utils

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
except ImportError:  # matplotlib e opcional ate o usuario pedir um grafico
    matplotlib = None
    plt = None

PASTA_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "graficos_png")
HORIZONTE = mps.HORIZONTE
AZUL = "#3b78b8"
VERMELHO = "#c0392b"
LARANJA = "#e08a1e"
CINZA = "#7f8c8d"


# ---------- Apoio ----------

def _exigir_matplotlib():
    """Levanta RuntimeError se o matplotlib nao estiver instalado."""
    if plt is None:
        raise RuntimeError(
            "a biblioteca matplotlib nao esta instalada "
            "(use: pip install matplotlib).")


def _finalizar(fig, nome_arquivo, mostrar):
    """Salva o grafico em PNG e, se pedido, exibe. Devolve o caminho."""
    os.makedirs(PASTA_PNG, exist_ok=True)
    caminho = os.path.join(PASTA_PNG, nome_arquivo)
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    if mostrar and matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close(fig)
    return caminho


# ---------- Graficos (recebem dados prontos; nao leem arquivos) ----------

def grafico_posicao_estoque(saldos, itens, mostrar=True):
    """Barras: saldo atual x estoque de seguranca de cada item."""
    _exigir_matplotlib()
    posicao = estoque.posicao_estoque(saldos, itens)
    if not posicao:
        raise ValueError("nao ha itens cadastrados.")
    codigos = [p["item"] for p in posicao]
    posicoes = range(len(codigos))
    largura = 0.4
    fig, ax = plt.subplots(figsize=(max(8, 0.8 * len(codigos)), 5))
    cores = [VERMELHO if p["abaixo_seguranca"] else AZUL for p in posicao]
    ax.bar([x - largura / 2 for x in posicoes],
           [p["saldo"] for p in posicao], largura, color=cores)
    ax.bar([x + largura / 2 for x in posicoes],
           [p["estoque_seguranca"] for p in posicao], largura, color=CINZA)
    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(codigos, rotation=45, ha="right")
    ax.set_ylabel("Quantidade")
    ax.set_title("Posição de estoque: saldo atual x estoque de segurança")
    ax.legend(handles=[Patch(color=AZUL, label="Saldo (acima da segurança)"),
                       Patch(color=VERMELHO,
                             label="Saldo (abaixo da segurança)"),
                       Patch(color=CINZA, label="Estoque de segurança")])
    ax.grid(axis="y", alpha=0.3)
    return _finalizar(fig, "posicao_estoque.png", mostrar)


def grafico_estoque_projetado(registro, item, codigo, mostrar=True):
    """Linha: estoque projetado nas 8 semanas, com a linha da seguranca."""
    _exigir_matplotlib()
    semanas = list(range(1, HORIZONTE + 1))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(semanas, registro["ep"], marker="o", color=AZUL,
            label="Estoque projetado")
    seguranca = utils.formatar_quantidade(item["estoque_seguranca"])
    ax.axhline(item["estoque_seguranca"], linestyle="--", color=VERMELHO,
               label=f"Estoque de segurança ({seguranca})")
    ax.set_xticks(semanas)
    ax.set_xlabel("Semana")
    ax.set_ylabel(f"Quantidade ({item['unidade']})")
    ax.set_title(f"Estoque projetado - {codigo} {item['descricao']}")
    ax.legend()
    ax.grid(alpha=0.3)
    return _finalizar(fig, f"estoque_projetado_{codigo}.png", mostrar)


def contar_ordens_por_semana(dados_ordens):
    """Conta ordens por semana de entrega: devolve (lista_op, lista_oc).

    Considera as ordens ainda nao encerradas com entrega dentro do horizonte.
    """
    op = [0] * HORIZONTE
    oc = [0] * HORIZONTE
    for ordem in dados_ordens["ordens"].values():
        semana = ordem["semana_entrega"]
        if ordem["status"] == "ENCERRADA" or not 1 <= semana <= HORIZONTE:
            continue
        destino = op if ordem["tipo"] == "OP" else oc
        destino[semana - 1] += 1
    return op, oc


def grafico_ordens_por_semana(dados_ordens, mostrar=True):
    """Barras empilhadas: OP e OC por semana de entrega (chegada)."""
    _exigir_matplotlib()
    op, oc = contar_ordens_por_semana(dados_ordens)
    if not any(op) and not any(oc):
        raise ValueError("nao ha ordens abertas no horizonte. "
                         "Execute o MRP antes.")
    semanas = list(range(1, HORIZONTE + 1))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(semanas, op, color=AZUL, label="OP (produção)")
    ax.bar(semanas, oc, bottom=op, color=LARANJA, label="OC (compra)")
    ax.set_xticks(semanas)
    ax.set_xlabel("Semana de entrega")
    ax.set_ylabel("Número de ordens")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_title("Ordens por semana de entrega")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    return _finalizar(fig, "ordens_por_semana.png", mostrar)


def grafico_carga_capacidade(dados_ordens, roteiros, centros, codigo_centro,
                             mostrar=True):
    """Barras: carga semanal de um centro x capacidade, destacando
    as semanas com sobrecarga."""
    _exigir_matplotlib()
    analise = capacidade.analisar_centro(dados_ordens, roteiros, centros,
                                         codigo_centro)
    centro = centros[codigo_centro]
    semanas = [a[0] for a in analise]
    cargas = [a[1] for a in analise]
    cores = [VERMELHO if a[3] else AZUL for a in analise]
    horas = utils.formatar_numero(centro["capacidade"], 1)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(semanas, cargas, color=cores)
    ax.axhline(centro["capacidade"], linestyle="--", color="black")
    ax.set_xticks(semanas)
    ax.set_xlabel("Semana")
    ax.set_ylabel("Horas")
    ax.set_title(f"Carga x capacidade - {codigo_centro} {centro['nome']}")
    ax.legend(handles=[
        Patch(color=AZUL, label="Carga dentro da capacidade"),
        Patch(color=VERMELHO, label="Sobrecarga"),
        plt.Line2D([0], [0], linestyle="--", color="black",
                   label=f"Capacidade ({horas} h)"),
    ])
    ax.grid(axis="y", alpha=0.3)
    return _finalizar(fig, f"carga_{codigo_centro}.png", mostrar)


# ---------- Interface em modo texto ----------

def _executar(gerador, *args):
    """Chama um gerador de grafico tratando os erros esperados."""
    try:
        caminho = gerador(*args)
    except (ValueError, RuntimeError) as erro:
        print(f"ERRO: {erro}")
        return
    print(f"Grafico salvo em: {caminho}")


def grafico_estoque_menu(saldos, itens):
    """Gera o grafico de posicao de estoque."""
    _executar(grafico_posicao_estoque, saldos, itens)


def grafico_projetado_menu(registros, itens):
    """Pergunta o item e gera o grafico de estoque projetado."""
    if not registros:
        print("ERRO: execute o MRP primeiro (opcao 4 do menu).")
        return
    codigo = utils.ler_codigo("Codigo do item: ")
    if codigo not in registros:
        print(f"ERRO: nao ha registro MRP para {codigo}.")
        return
    _executar(grafico_estoque_projetado, registros[codigo], itens[codigo],
              codigo)


def grafico_ordens_menu(dados_ordens):
    """Gera o grafico de ordens por semana de entrega."""
    _executar(grafico_ordens_por_semana, dados_ordens)


def grafico_crp_menu(dados_ordens, roteiros, centros):
    """Pergunta o centro e gera o grafico de carga x capacidade."""
    codigo = utils.ler_texto("Codigo do centro: ").upper()
    if codigo not in centros:
        print(f"ERRO: centro {codigo} nao encontrado.")
        return
    _executar(grafico_carga_capacidade, dados_ordens, roteiros, centros,
              codigo)
