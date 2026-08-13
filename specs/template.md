---
id: spec-<componente>
versao: 0.1.0
status: proposta
componente: <caminho/do/componente>
tags: [<tag1>, <tag2>]
data: <AAAA-MM-DD>
---

# Spec — <Nome do Componente>

> Template para criar novas specs. Copie este arquivo para
> `specs/<componente>.spec.md` e preencha as seções. Remova os blocos `> ...`.
> Cada seção espelha os campos do `GoalSpecification` do LER e os
> `criterios_sucesso` da compreensão de pedidos.

## Objetivo

> Frase única: o que o componente faz. Ex: "O vigilante agrupa commits em
> lotes após período de silêncio no working tree, com teto forçado de 1h."

## Requisitos

> Lista numerada. Fonte: `GoalSpecification.requirements` ou requisitos extraídos
> da compreensão de pedidos.

1. Requisito 1 — descrição observável.
2. Requisito 2 — descrição observável.

## Restrições

> Fonte: `GoalSpecification.constraints`. Ambiente, linguagem, estilo, limites.

- Restrição 1 (ex: "Script 100% stdlib, sem dependências externas").
- Restrição 2 (ex: "Windows PowerShell 5.1").

## Dependências

> Fonte: `GoalSpecification.dependencies`. Arquivos, módulos, serviços.

- Dependência 1 (ex: `scripts/persistencia.ps1` — gate de persistência).
- Dependência 2.

## Premissas

> Fonte: `GoalSpecification.assumptions`.

- Premissa 1 (ex: "Python 3 disponível no PATH").
- Premissa 2.

## Entradas e Saídas

> Contrato observável. O que entra e o que sai.

- Entrada: ...
- Saída: ...
- Efeito colateral: ...

## Casos de Borda

> Comportamento em condições-limite (ver princípio do teste adversarial).

- Trabalho vazio / sem pendências.
- Atividade contínua além do limite.
- Recurso indisponível (rede, serviço, arquivo ausente).

## Critérios de Aceitação

> Fonte: `GoalSpecification.acceptance_criteria` + `criterios_sucesso` da
> compreensão de pedidos. Cada item deve ser verificável pelo validador
> (`scripts/valida_specs.py`). Use prefixos reconhecíveis:
> `[arquivo:<path>]` — o arquivo deve existir;
> `[comando:<cmd>]` — o comando deve retornar exit 0;
> texto livre — verificado manualmente (relatado como "manual").

- [arquivo:<caminho/do/componente>] Componente existe e é o alvo da spec.
- [arquivo:<caminho/do/teste>] Teste relacionado existe.
- [comando:python scripts/valida_specs.py] Validador passa sem erros.
- Critério manual 1 — descrição verificável à mão.

## Definition of Done

> Fonte: `GoalSpecification.definition_of_done`. Lista de DoD.

- [ ] Requisitos implementados conforme a spec.
- [ ] Testes relacionados executados e aprovados.
- [ ] Evidências de funcionamento coletadas.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

> Fonte: `GoalSpecification.risks`. Lista com severidade.

- Risco 1 — severidade (ex: "Atividade contínua gera commits a cada 5 min",
  severidade baixa — mitigado pelo quiet period).
- Risco 2 — severidade.

## Testes Relacionados

> Caminho(s) dos testes que cobrem esta spec. Verificado pelo validador.

- <caminho/do/teste-1>
- <caminho/do/teste-2>
