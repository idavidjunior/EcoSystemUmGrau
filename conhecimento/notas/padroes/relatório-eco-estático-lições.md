---
tags: [agregações, calculadas, opencode, padrao, ram, vazio]
aliases: [Relatório Eco estático — lições]
date: 2026-08-22
---

# Relatório Eco estático — lições

**Fonte:** opencode

## Decisão
PowerBI/Grafana/Metabase seriam delírio para este ecossistema (licença, Docker,
banco, processo residente que o system_guardian mataria em pico de RAM). O mesmo
valor se obtém com um arquivo HTML autocontido: dados embutidos em
window.ECO_DADOS, gráficos canvas vanilla, abre offline via file://.

## Erros cometidos e corrigidos na implementação
1. Placeholder duplicado: template tinha `window.__DADOS__=__DADOS__` e o replace
   do payload corrompia o próprio token. Correção: tokens distintos (%%PAYLOAD%%).
2. Coletor de integridade montava a lista de problemas mas nunca a devolvia
   (variável local). Correção: retornar "_problemas" no dict e pop() no main.
3. Payload embutido precisa escapar "</" → "<\/" ou um "</script>" dentro de
   qualquer texto quebraria a página.

## Padrão estabelecido
Coleção tolerante a ausência (try/except → default vazio), agregações calculadas
em Python, renderização em JS puro. Adversarial validado: sem runtime/hsc e sem
memories.json o relatór
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]