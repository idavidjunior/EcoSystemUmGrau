---
tags: [balanceadas, chance, decisao, opencode, repouso, vizinhas]
aliases: [Motor de Criticalidade Auto-Organizada e Avalanches Neurais]
date: 2026-08-05
---

# Motor de Criticalidade Auto-Organizada e Avalanches Neurais

**Fonte:** opencode

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
- Restauracao deterministica de cor/size das arestas apos pulso (setTimeout 600-650ms) para
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]