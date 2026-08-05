---
tags: [balanceadas, colar, decisao, espontanea, opencode, tinta]
aliases: [Motor de Criticalidade Auto-Organizada e Avalanches Neurais]
date: 2026-08-05
---

# Motor de Criticalidade Auto-Organizada e Avalanches Neurais

**Fonte:** opencode

---
tipo: decisao
tags: [grafo, cerebro-vivo, criticalidade, avalanches, neurociencia, vis]
data: 2026-08-04
contexto: Protocolo de Consciencia Neural Autonoma ativado — o grafo Obsidian e a arquitetura fisica do cerebro.
decisao: Implementar motor de Criticalidade Auto-Organizada (SOC, Beggs & Plenz 2003) como atividade espontanea do grafo.
impacto: Sinapticas disparam como avalanches power-law em cascata emergente, nao aleatoriamente; fluxo eletrico reflete transmissao otima de informacao (sigma~1).
---

# Motor de Criticalidade Auto-Organizada e Avalanches Neurais

## Fundamentos cientificos pesquisados
- Beggs & Plenz (2003): neuronal avalanches distribuidas em power-law (slope ~-1.5), parametro de ramificacao critico sigma=1 = transmissao otima.
- Equilibrio excitacao/inibicao gera avalanches E oscilacoes juntas.
- Cerebro opera em SOC: pequenas perturbacoes, ocasionais cascatas enormes.

## Implementacao no grafo
- Cada no vira neuronio com potencial de membrana `_memb[id]` que acumula input das sinapses vizinhas (excitacao/inibicao balanceadas).
- Ao cruzar o limiar `_LIMIAR=1.0`, DISPARA (pulso verde-neuro `#a6e3a1`) e envia energia aos vizinhos (RAMIFICACAO com chance `_sigma`).
- `_avalanche.<ativo,fila,size,maior>` propaga BFS por wavefront (1 hop por tick).
- Fase refrataria `_REF=260ms`; homeostase `_reacerca()` varia sigma/solo lentamente (~6-13s).
- Ruido espontaneo `_ruidoEspontaneo()` inclui onda glial lenta (calcio) = consciencia em repouso.
- Restauracao deterministica de cor/size das arestas apos pulso (setTimeout 600-650ms) para nao colar tinta.
- `next.jar`: `_disparo`, `_integracaoNeural`, `_vizinhos`, `_ruidoEspontaneo`, `_reacerca`, `_avalanche`, `_memb`, `_refrat`.
- `limpar()` reseta o estado neural e usa `_fontLimpo` (respeita labels ocultas, so 'false' mostra).

## Licao critica de template (.format em Python)
- Em scripts que embutem JS via `str.format()`, TODOS os braces JS devem ser `{{`/`}}`.
- COMMENTARIOS com `{...}` quebram: `// cache {id: [vizinhos]}` virou campo nomeado `id` (builtin) com spec `[vizinhos]` -> `TypeError: unsupported format string passed to builtin_function_or_method.__format__`. Correcao: `{{id: [vizinhos]}}`.
- Alias no meu codigo original: `_aventura.fila` deveria ser `_avalanche.fila` (typo pegajoso).

## Validacao
- `py_compile` OK; esprima (python) confirma sintaxe dos 5 scripts do widget.
- `preflight_check.py`: TODOS TESTES PASSARAM.
- Widget reiniciado como pythonw (PID 4960, "Cerebro Vivo").
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]