"""Centros de trabalho, roteiros e carga x capacidade (RF06, RF12, RN09)."""

import re

import itens as cadastro
import mps
import persistencia
import utils

ARQUIVO_CENTROS = "centros.json"
ARQUIVO_ROTEIROS = "roteiros.json"
PADRAO_CENTRO = re.compile(r"^CT-\d{2,3}$")
HORIZONTE = mps.HORIZONTE


# ---------- Logica (sem input/print) ----------

def carregar_centros():
    """Carrega os centros: {codigo: {nome, capacidade, custo_hora}}."""
    return persistencia.carregar_json(ARQUIVO_CENTROS, {})


def salvar_centros(centros):
    """Grava os centros de trabalho no arquivo."""
    persistencia.salvar_json(ARQUIVO_CENTROS, centros)


def carregar_roteiros():
    """Carrega os roteiros: {item: {centro, tempo_unitario}}."""
    return persistencia.carregar_json(ARQUIVO_ROTEIROS, {})


def salvar_roteiros(roteiros):
    """Grava os roteiros no arquivo."""
    persistencia.salvar_json(ARQUIVO_ROTEIROS, roteiros)


def criar_centro(centros, codigo, nome, capacidade, custo_hora):
    """Cadastra um centro de trabalho. Levanta ValueError se invalido."""
    if not PADRAO_CENTRO.match(codigo):
        raise ValueError("codigo de centro invalido (use o formato CT-03).")
    if codigo in centros:
        raise ValueError(f"o centro {codigo} ja esta cadastrado.")
    if not nome.strip():
        raise ValueError("o nome do centro nao pode ficar vazio.")
    if capacidade <= 0:
        raise ValueError("a capacidade (horas/semana) deve ser maior que 0.")
    if custo_hora < 0:
        raise ValueError("o custo-hora nao pode ser negativo.")
    centros[codigo] = {
        "nome": nome.strip(),
        "capacidade": capacidade,
        "custo_hora": custo_hora,
    }


def definir_roteiro(roteiros, itens, centros, codigo_item, centro,
                    tempo_unitario):
    """Define o roteiro de operacao unica de um item fabricado."""
    if codigo_item not in itens:
        raise ValueError(f"item {codigo_item} nao encontrado.")
    if not cadastro.eh_fabricado(itens[codigo_item]):
        raise ValueError("so itens fabricados (PA ou SA) tem roteiro.")
    if centro not in centros:
        raise ValueError(f"centro {centro} nao encontrado.")
    if tempo_unitario <= 0:
        raise ValueError("o tempo por unidade (horas) deve ser maior que 0.")
    roteiros[codigo_item] = {"centro": centro,
                             "tempo_unitario": tempo_unitario}


def itens_sem_roteiro(itens, roteiros):
    """Itens fabricados que ainda nao tem roteiro (nao entram na carga)."""
    return [c for c in sorted(itens)
            if cadastro.eh_fabricado(itens[c]) and c not in roteiros]


def calcular_carga(dados_ordens, roteiros, codigo_centro):
    """Carga em horas de um centro, por semana (RN09).

    Soma quantidade x tempo unitario das OPs cuja liberacao cai na semana.
    Contam OPs PLANEJADAS, ATRASADAS, FIRMES e LIBERADAS (nao as ENCERRADAS).
    Liberacao antes da semana 1 (ordem atrasada) conta na semana 1.
    """
    carga = [0.0] * HORIZONTE
    for ordem in dados_ordens["ordens"].values():
        roteiro = roteiros.get(ordem["item"])
        if (ordem["tipo"] != "OP" or ordem["status"] == "ENCERRADA"
                or roteiro is None or roteiro["centro"] != codigo_centro):
            continue
        semana = max(ordem["semana_liberacao"], 1)
        if semana <= HORIZONTE:
            carga[semana - 1] += ordem["quantidade"] * roteiro[
                "tempo_unitario"]
    return [round(horas, 6) for horas in carga]


def analisar_centro(dados_ordens, roteiros, centros, codigo_centro):
    """Lista por semana: (semana, carga, uso_percentual, sobrecarga)."""
    capacidade = centros[codigo_centro]["capacidade"]
    resultado = []
    for semana, carga in enumerate(
            calcular_carga(dados_ordens, roteiros, codigo_centro), start=1):
        uso = carga / capacidade * 100
        resultado.append((semana, carga, uso, carga > capacidade))  # RN09
    return resultado


# ---------- Interface em modo texto ----------

def exibir_crp(dados_ordens, roteiros, centros, codigo_centro):
    """Mostra carga x capacidade de um centro (mockup 6.6)."""
    if codigo_centro not in centros:
        print(f"ERRO: centro {codigo_centro} nao encontrado.")
        return
    centro = centros[codigo_centro]
    capacidade = utils.formatar_numero(centro["capacidade"], 1)
    print(f"\nCARGA x CAPACIDADE - {codigo_centro} {centro['nome']} "
          f"({capacidade} h/semana)")
    print(f"{'Sem':>3}{'Carga(h)':>10}{'Uso(%)':>8}")
    semanas_sobrecarga = []
    for semana, carga, uso, sobrecarga in analisar_centro(
            dados_ordens, roteiros, centros, codigo_centro):
        barra = "#" * round(uso / 10)
        aviso = " SOBRECARGA" if sobrecarga else ""
        print(f"{semana:>3}{utils.formatar_numero(carga, 1):>10}"
              f"{round(uso):>8} {barra}{aviso}")
        if sobrecarga:
            semanas_sobrecarga.append(semana)
    if semanas_sobrecarga:
        lista = " e ".join(", ".join(str(s) for s in semanas_sobrecarga)
                           .rsplit(", ", 1))
        plural = "s" if len(semanas_sobrecarga) > 1 else ""
        print(f"Sugestao: antecipar OPs ou programar hora extra na{plural} "
              f"semana{plural} {lista}.")


def cadastrar_centro_menu(centros):
    """Pede os dados e cadastra um centro de trabalho."""
    print("\n--- Cadastrar centro de trabalho ---")
    while True:
        codigo = utils.ler_texto("Codigo (ex.: CT-03): ").upper()
        if PADRAO_CENTRO.match(codigo):
            break
        print("ERRO: codigo invalido. Use o formato CT-03.")
    if codigo in centros:
        print(f"ERRO: o centro {codigo} ja esta cadastrado.")
        return
    nome = utils.ler_texto("Nome: ")
    capacidade = utils.ler_decimal("Capacidade (horas/semana): ", minimo=0.01)
    custo_hora = utils.ler_decimal("Custo-hora (R$): ", minimo=0)
    try:
        criar_centro(centros, codigo, nome, capacidade, custo_hora)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_centros(centros)
    print(f"Centro {codigo} cadastrado.")


def listar_centros(centros):
    """Lista os centros de trabalho cadastrados."""
    print("\n--- Centros de trabalho ---")
    if not centros:
        print("Nenhum centro cadastrado.")
        return
    print(f"{'Codigo':<8}{'Nome':<24}{'Cap.(h/sem)':>12}{'Custo-hora':>12}")
    for codigo in sorted(centros):
        c = centros[codigo]
        print(f"{codigo:<8}{c['nome'][:22]:<24}"
              f"{utils.formatar_numero(c['capacidade'], 1):>12}"
              f"{utils.formatar_numero(c['custo_hora']):>12}")


def definir_roteiro_menu(roteiros, itens, centros):
    """Pede o item, o centro e o tempo por unidade e grava o roteiro."""
    print("\n--- Roteiro de operacao ---")
    codigo = utils.ler_codigo("Codigo do item fabricado: ")
    centro = utils.ler_texto("Codigo do centro de trabalho: ").upper()
    tempo = utils.ler_decimal("Tempo por unidade (horas): ", minimo=0.0001)
    try:
        definir_roteiro(roteiros, itens, centros, codigo, centro, tempo)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return
    salvar_roteiros(roteiros)
    print(f"Roteiro de {codigo} gravado.")


def listar_roteiros(roteiros, itens):
    """Lista os roteiros e avisa sobre itens fabricados sem roteiro."""
    print("\n--- Roteiros ---")
    if not roteiros:
        print("Nenhum roteiro cadastrado.")
    else:
        print(f"{'Item':<9}{'Descricao':<28}{'Centro':<8}{'h/un':>8}")
        for codigo in sorted(roteiros):
            r = roteiros[codigo]
            print(f"{codigo:<9}{itens[codigo]['descricao'][:26]:<28}"
                  f"{r['centro']:<8}"
                  f"{utils.formatar_numero(r['tempo_unitario'], 2):>8}")
    faltando = itens_sem_roteiro(itens, roteiros)
    if faltando:
        print("AVISO: itens fabricados sem roteiro (fora da carga): "
              + ", ".join(faltando))


def exibir_crp_menu(dados_ordens, roteiros, centros):
    """Pergunta o centro e exibe carga x capacidade."""
    print("\n--- Carga x capacidade (CRP) ---")
    codigo = utils.ler_texto("Codigo do centro: ").upper()
    exibir_crp(dados_ordens, roteiros, centros, codigo)
