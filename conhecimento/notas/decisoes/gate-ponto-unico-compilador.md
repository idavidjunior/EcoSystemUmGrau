---
tags: [408, 410, decisao, direto, faziam, opencode]
aliases: [gate ponto unico compilador]
date: 2026-09-02
---

# gate ponto unico compilador

**Fonte:** opencode

Tipo: decisao

Tags: [gate, persistencia, ponto-unico, auditoria, compiladorAPK, ecosystem]

Data: 2026-09-02

contexto: O usuário perguntou se a ordem de commit/push do ecossistema realmente parte de um único lugar (o gate persistencia.ps1) ou se existem vários pontos emitindo ordens. Ao auditar, encontrei desvios reais do gate e precisei decidir como tratá-los sem quebrar fluxos legítimos.

decisao: (1) Corpus no núcleo do EcoSystemUmGrau: scripts/ecosystem.ps1 nas funções repair (linhas 352-353) e learn (linhas 408-410) faziam `git add`/`git commit`/`git push` direto, fora do gate. Isso gerou um commit real fora do gate hoje às 06:43 (`[ecosystem learn] 2026-09-02 06:43`, hash 3173e01eb). A correção aplicada: as duas funções agora delegam ao gate via `& powershell -ExecutionPolicy Bypass -File "$ecoDir\scripts\persistencia.ps1" run-sync -Repo eco -Label "ecosystem repair|learn" -Push`. (2) Projetos/compiladorAPK/scripts/apk-compiler-ui.ps1 possui ~17 pontos de `git add`/`commit`/`pu
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]