---
tags: [decisao, diretamente, nada, opencode, tocam, vai]
aliases: [Ponto único de persistência (gate)]
date: 2026-08-10
---

# Ponto único de persistência (gate)

**Fonte:** opencode

## Comandos
- `persistencia.ps1 status` → modo atual (AUTO/MANUAL), HEAD e pendências por repo.
- `persistencia.ps1 manual` → pausa TODOS os commits automáticos (serviços continuam consolidando, nada vai ao git).
- `persistencia.ps1 auto` → reativa os commits automáticos.
- `persistencia.ps1 commit -Repo eco -Mensagem "..." -Push` → commit manual em qualquer modo.
- `persistencia.ps1 sync -Push` → commit manual de eco + ler + projetos Android.

## Configuração
- `config/persistencia.json` → `modo` ("auto"/"manual") e `excluir` (paths que ficam fora dos commits do gate).
- Log do gate: `%USERPROFILE%\.persistencia.log`.
- Locks por repositório em `%TEMP%\persistencia-<hash>.lock` (TTL 120s).

## Arquitetura
- `vigilante.ps1` → `Sync-GitRepo`/`Sync-ProjectRepo` agora chamam `persistencia.ps1 run-sync` (pull → add → commit → push) e NÃO tocam o git diretamente.
- `ecosystem.ps1` → bloco de commit substituído pela chamada ao gate.
- Nenhum script/agente executa `git commit`/`git push` dire
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]