---
tags: [countbyfolder, countchildren, locais, opencode, padrao, real]
aliases: [contagem subpastas arquivos pastas]
date: 2026-08-09
---

# contagem subpastas arquivos pastas

**Fonte:** opencode

Tipo: padrao

Tags: [bibliaestudocompleta, recursos, ui, contagem]

Data: 2026-08-09

Contexto: Usuario pediu para mostrar a quantidade de subpastas e arquivos dentro das pastas na tela Meus Recursos.

Decisão: ResourceListAdapter recebe UserResourceDao e mostra detalhe "N subpastas • M arquivos" no subtitulo das pastas (referenciadas via countChildren, locais via countByFolder). Na raiz, pastas referenciadas sem filhos persistidos sao materializadas em background (importChildrenForFolder) para exibir contagem real.

Impacto: Usuario ve quantos itens ha dentro de cada pasta sem abrir; contagens corretas mesmo para pastas importadas antes da arvore.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]