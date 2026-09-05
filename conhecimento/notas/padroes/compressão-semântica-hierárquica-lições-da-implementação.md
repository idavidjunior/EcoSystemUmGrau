---
tags: [256, cache, cli, opencode, padrao, sha]
aliases: [Compressão Semântica Hierárquica — lições da implementação]
date: 2026-08-22
---

# Compressão Semântica Hierárquica — lições da implementação

**Fonte:** opencode

## O que foi construído
scripts/hsc.py (~1050 linhas, stdlib puro) implementa os 9 níveis de representação
(source → semantic_core) com extratores determinísticos, detector de redundância,
validador de fidelidade, rastreabilidade por fragmento, gestão de confiança,
detector de conflitos entre fontes, storage versionado com cache SHA-256 e CLI
(compress/text/get/list/stats/multi/recommend).

## Decisões que funcionaram
1. EXTRATIVO por construção: nada é gerado, tudo é seleção/organização do original.
   Anti-alucinação estrutural, não por prompt.
2. Fidelidade = recuperabilidade: um fato crítico está preservado se aparece verbatim
   em qualquer nível consultável OU no core com números/datas conferindo. Medir só
   contra o nível mais comprimido era injusto e dava 0.62 em docs reais.
3. Garantia de críticos no core: fatos com número/data/negação entram no núcleo mesmo
   fora do top-10 de importância (teto total 20). Isso subiu fatos_criticos de 0.68
   para 0.95 sem inflar a prosa.
4.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]