"""Validacoes de entrada e formatacao (RNF05, RN01)."""

import re
from datetime import date, datetime

PADRAO_CODIGO = re.compile(r"^(PA|SA|MP)-\d{3}$")
TIPOS_VALIDOS = ("PA", "SA", "MP")
FORMATO_DATA = "%d/%m/%Y"


def codigo_valido(codigo):
    """Retorna True se o codigo segue o formato Tipo-Numero (ex.: PA-001)."""
    return bool(PADRAO_CODIGO.match(codigo))


def tipo_do_codigo(codigo):
    """Retorna o tipo (PA, SA ou MP) a partir do codigo do item."""
    return codigo.split("-")[0]


def ler_texto(mensagem, obrigatorio=True):
    """Le um texto; repete enquanto vazio se for obrigatorio."""
    while True:
        valor = input(mensagem).strip()
        if valor or not obrigatorio:
            return valor
        print("ERRO: o campo nao pode ficar vazio.")


def ler_inteiro(mensagem, minimo=None, maximo=None):
    """Le um inteiro dentro de limites opcionais."""
    while True:
        try:
            valor = int(input(mensagem).strip())
        except ValueError:
            print("ERRO: digite um numero inteiro.")
            continue
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor minimo e {minimo}.")
        elif maximo is not None and valor > maximo:
            print(f"ERRO: o valor maximo e {maximo}.")
        else:
            return valor


def ler_decimal(mensagem, minimo=None):
    """Le um numero decimal (aceita virgula ou ponto)."""
    while True:
        texto = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("ERRO: digite um numero valido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor minimo e {minimo}.")
        else:
            return valor


def ler_opcao(mensagem, opcoes):
    """Le uma opcao dentre as permitidas (sem diferenciar maiusculas)."""
    opcoes = [o.upper() for o in opcoes]
    while True:
        valor = input(mensagem).strip().upper()
        if valor in opcoes:
            return valor
        print(f"ERRO: opcao invalida. Use: {', '.join(opcoes)}.")


def ler_codigo(mensagem):
    """Le um codigo de item no formato Tipo-Numero."""
    while True:
        codigo = input(mensagem).strip().upper()
        if codigo_valido(codigo):
            return codigo
        print("ERRO: codigo invalido. Use o formato PA-001, SA-010, MP-201.")


def ler_data(mensagem):
    """Le uma data dd/mm/aaaa; Enter usa a data de hoje."""
    while True:
        texto = input(mensagem).strip()
        if not texto:
            return data_hoje()
        try:
            datetime.strptime(texto, FORMATO_DATA)
            return texto
        except ValueError:
            print("ERRO: data invalida. Use dd/mm/aaaa.")


def data_hoje():
    """Data atual no formato dd/mm/aaaa."""
    return date.today().strftime(FORMATO_DATA)


def formatar_numero(valor, casas=2):
    """Formata numero com virgula decimal (ex.: 1234.5 -> 1.234,50)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_quantidade(valor, com_sinal=False):
    """Quantidade sem zeros desnecessarios: 3 -> '3'; 0.5 -> '0,5'."""
    if float(valor).is_integer():
        texto = str(int(valor))
    else:
        texto = str(round(valor, 3)).replace(".", ",")
    if com_sinal and valor > 0:
        texto = "+" + texto
    return texto


def formatar_moeda(valor):
    """Formata valor em reais (ex.: R$ 792,60)."""
    return f"R$ {formatar_numero(valor)}"


def pausar():
    """Aguarda o usuario pressionar Enter."""
    input("\nPressione Enter para continuar...")
