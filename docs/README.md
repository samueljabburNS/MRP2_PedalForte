# MRP II - Pedal Forte Bicicletas

Sistema de Planejamento dos Recursos de Manufatura (MRP II) em modo texto,
feito em Python para a fábrica fictícia Pedal Forte Bicicletas.

- **Disciplina:** Programação em Python (Engenharia de Computação, CEFET-MG
  Divinópolis), prof. Guido Pantuza
- **Trabalho:** 2º trabalho, individual
- **Autor:** Samuel Pereira Jabbur

O sistema responde, a cada execução: o que produzir ou comprar, quanto,
quando e se há capacidade para isso. Ele integra o Plano Mestre de Produção
(MPS), a estrutura de produto (BOM), os estoques, as ordens de produção e de
compra, a carga x capacidade (CRP) e o custo padrão.

## Requisitos e execução

- Python 3.10 ou superior (testado com 3.12)
- matplotlib (somente para os gráficos)

```
cd MRP2_PedalForte
pip install -r requirements.txt
python main.py        # no Linux: python3 main.py
```

Testado em Linux (Ubuntu 24.04, Python 3.12) e em Windows. A pasta `data/` já
vem com a base de demonstração. Se ela estiver vazia, o programa oferece
criar a base ao iniciar.

## Estrutura do projeto

```
MRP2_PedalForte/
  main.py          ponto de entrada
  menu.py          menus e navegação
  itens.py         cadastro de itens
  estrutura.py     BOM e árvore indentada
  estoque.py       movimentações, saldo e kardex
  mps.py           plano mestre de produção
  mrp.py           cálculo MRP
  ordens.py        OPs, OCs e apontamento
  capacidade.py    centros, roteiros e CRP
  custos.py        custo padrão
  relatorios.py    exportação CSV
  graficos.py      gráficos de gestão (matplotlib)
  persistencia.py  leitura e gravação de arquivos
  utils.py         validações e formatação
  base_demo.py     (extra) cria a base de demonstração
  data/            arquivos JSON e CSV
  docs/README.md
```

`base_demo.py` não está na lista do enunciado. Ele existe só para gerar a base
de demonstração usando as mesmas funções de negócio do sistema.

Arquivos em `data/`: `itens.json`, `estrutura.json`, `estoque.json`,
`movimentos.csv` (kardex), `centros.json`, `roteiros.json`, `mps.json`,
`ordens.json`. Os relatórios exportados (`posicao_estoque.csv` e
`lista_ordens.csv`) também são gravados em `data/`, e os gráficos em
`graficos_png/`.

## Como usar (ciclo completo)

1. **Menu 3 (MPS):** veja ou altere a demanda semanal dos produtos acabados.
2. **Menu 4 (MRP), opção 1:** executa o MRP e mostra as ordens planejadas. A
   opção 2 mostra o registro MRP de um item.
3. **Menu 5 (Ordens):** `F` firma, `L` libera, `A` aponta a produção de uma OP
   liberada e `E` encerra (recebe) uma OC liberada.
4. **Menu 2 (Estoque):** confira saldo e kardex; registre entradas, saídas e
   ajustes.
5. **Menu 6 (CRP):** veja a carga x capacidade e as semanas com sobrecarga.
6. **Menu 7 (Custo):** custo padrão de um item fabricado.
7. **Menu 8 (Relatórios):** exporta CSV de estoque e de ordens.
8. **Menu 9 (Gráficos):** gera os 4 gráficos (fechar a janela para voltar).

O registro MRP e o gráfico de estoque projetado dependem de o MRP ter sido
executado na sessão atual.

## Base de demonstração

2 produtos acabados (PA-001 Bicicleta Aro 29 MTB e PA-002 Bicicleta Aro 29
Urbana), 2 semiacabados, 8 matérias-primas e 3 centros de trabalho (o mínimo
exigido é 2). O PA-001 reproduz o mockup 6.7 (custo padrão R$ 792,60) e o
MP-202 reproduz o kardex do mockup 6.3 (saldo 18, abaixo da segurança de 20).

## Requisitos atendidos

| Requisito | Onde está |
|---|---|
| RF01 menu principal | `menu.py` |
| RF02 cadastrar, listar e alterar itens | `itens.py` |
| RF03 BOM em até 3 níveis e explosão indentada | `estrutura.py` |
| RF04 movimentações de estoque | `estoque.py` |
| RF05 saldo, kardex e alerta de segurança | `estoque.py` |
| RF06 centros de trabalho e roteiros | `capacidade.py` |
| RF07 MPS (8 semanas) | `mps.py` |
| RF08 cálculo MRP e registro por item | `mrp.py` |
| RF09 ordens planejadas (OP e OC) | `mrp.py`, `ordens.py` |
| RF10 firmar, liberar e encerrar ordens | `ordens.py` |
| RF11 apontamento de produção | `ordens.py` |
| RF12 carga x capacidade (CRP) | `capacidade.py` |
| RF13 custo padrão | `custos.py` |
| RF14 exportação CSV | `relatorios.py` |
| RF15 persistência e carga automática | `persistencia.py`, `menu.py` |
| RF16 gráficos com matplotlib | `graficos.py` |

| Regra | Onde está |
|---|---|
| RN01 código Tipo-Número, único | `itens.criar_item`, `utils.codigo_valido` |
| RN02 saldo nunca negativo | `estoque.validar_movimento` |
| RN03 BOM em até 3 níveis, sem ciclos | `estrutura.adicionar_componente` |
| RN04 processar PA, SA e MP, nessa ordem | `mrp.executar_mrp` |
| RN05 necessidade líquida | `mrp.calcular_registro` |
| RN06 lote mínimo | `mrp.calcular_registro` |
| RN07 liberação = entrega - lead time; ATRASADA | `mrp.calcular_registro`, `ordens.criar_ordem_planejada` |
| RN08 só FIRMES e LIBERADAS são recebimentos | `ordens.recebimentos_programados`, `ordens.apagar_planejadas` |
| RN09 carga do centro e sobrecarga | `capacidade.calcular_carga` |
| RN10 kardex imutável, correção por ajuste | `persistencia.adicionar_movimento` (só acrescenta) |

Requisitos não funcionais: RNF01 (individual), RNF02 (Python 3.10+), RNF03
(PEP 8: nenhuma linha acima de 79 caracteres, docstrings em todas as
funções), RNF04 (módulos coesos), RNF05 (toda leitura de dados do usuário é
validada e repetida até ser válida), RNF06 (executado em Linux), RNF07 (JSON e
CSV), RNF08 (toda a lógica de MRP, CRP, custos e estoque foi escrita pelo
autor; matplotlib só nos gráficos), RNF09 (base de demonstração), RNF10 (modo
texto). A interface gráfica (RNF11) não foi implementada.

## Decisões de projeto

**Estilo geral**
- Programação estruturada, com funções e dicionários, sem classes.
- Em cada módulo, a lógica (sem `input` nem `print`, que levanta
  `ValueError`) fica separada da interface em modo texto. Isso permite testar
  e explicar cada regra isoladamente.
- `salvar_json` grava num arquivo temporário e depois substitui o original,
  para não corromper os dados se o programa for interrompido.

**Itens, estrutura e estoque**
- Itens em `{codigo: dados}`; o tipo vem do prefixo do código. Código e tipo
  não podem ser alterados depois, para não quebrar a BOM.
- BOM em `{pai: {componente: quantidade}}`. Uma tabela
  (`COMPONENTES_PERMITIDOS`) define que PA aceita SA ou MP, SA aceita só MP e
  MP não tem estrutura. Como PA nunca é componente, ciclos são impossíveis. A
  explosão e a árvore indentada são recursivas.
- Entrada e saída exigem quantidade positiva; o **ajuste** aceita valor
  positivo ou negativo, e é a forma de corrigir sem apagar histórico. O
  documento ou motivo é obrigatório.
- `movimentar` altera o saldo em memória e `gravar_movimento` persiste. A
  separação permite validar tudo antes de gravar, o que o apontamento usa.

**Ordens**
- A numeração é separada por tipo (OP-0001, OC-0001) e **não reinicia** quando
  as planejadas são apagadas, para um número nunca apontar para duas ordens.
- Fluxo: PLANEJADA/ATRASADA, FIRME, LIBERADA, ENCERRADA. Pular etapa é
  recusado. ATRASADA só vale para ordem ainda não firmada.
- **Decisão:** encerrar uma OC liberada significa receber a mercadoria
  (entrada da matéria-prima no estoque). Uma OP só é encerrada pelo
  apontamento.
- O apontamento confere todos os componentes antes de baixar qualquer um. Se
  faltar algum, recusa tudo e o estoque fica intacto.

**MRP**
- As fórmulas das RN05 a RN07 estão em `calcular_registro`, função pura
  validada contra o mockup 6.4 do enunciado.
- **Decisão:** liberação atrasada (antes da semana 1) conta como demanda dos
  componentes na semana 1; senão o material dessa ordem sumiria do plano.
- **Decisão:** ordens FIRMES geram demanda de componentes na semana de
  liberação; ordens LIBERADAS, na semana 1, porque os componentes só saem do
  estoque no apontamento.
- O registro MRP fica em memória após a execução. Executar o MRP de novo é
  seguro, pois as planejadas são apagadas e recalculadas (RN08).

**Capacidade e custos**
- **Decisão:** a RN09 diz "OPs liberadas naquela semana". Foi interpretada
  como a semana de **liberação** da OP (e não o status LIBERADA), para o CRP
  funcionar já na fase de planejamento. Contam OPs planejadas, atrasadas,
  firmes e liberadas; as encerradas não contam. OP atrasada conta na semana 1.
- Sobrecarga significa carga **maior** que a capacidade; carga igual não é
  sobrecarga.
- O custo padrão é recursivo: MP usa o custo cadastrado; PA e SA somam
  quantidade x custo padrão de cada componente mais a mão de obra do próprio
  item (tempo do roteiro x custo-hora). O custo cadastrado de um item
  fabricado não é usado. Item fabricado sem roteiro tem mão de obra zero e o
  sistema avisa.

**Relatórios e gráficos**
- Os CSV usam `;` como separador, vírgula decimal e UTF-8 com BOM, para abrir
  direto no Excel em português.
- O gráfico de ordens por semana conta o **número de ordens**, porque OP e OC
  têm unidades diferentes. Ordens encerradas não entram.
- Se o matplotlib não estiver instalado, o sistema avisa como instalar em vez
  de quebrar.

## Testes realizados

Execução de ponta a ponta pelo menu: entradas inválidas, saída recusada por
saldo insuficiente (sem deixar rastro no kardex), MRP, firmar, liberar,
apontar, recebimento de OC, CRP, custo, CSV e gráficos. Também foi conferido
que, ao fechar e reabrir o programa, o status das ordens e o kardex
permanecem. O cálculo do MRP, o CRP e o custo padrão foram validados contra os
mockups 6.4, 6.6 e 6.7 do enunciado.
