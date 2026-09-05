---
tags: [bug, constantemente, estava, opencode, subindo, yyyymmdd]
aliases: [Loop infinito de push no Vigilante (emails do GitHub a cada ]
date: 2026-08-08
---

# Loop infinito de push no Vigilante (emails do GitHub a cada minuto)

**Projeto:** opencode

## Causa Raiz
Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente

## Correcao
## Sintoma
Emails de notificação do GitHub chegando a cada ~1 minuto. Push automáticos no repo
`EcoSystemUmGrau` a cada 30-60s, contínuos, sem mudança real de código.

## Causa raiz (loop de auto-alimentação)
1. `scripts/vigilante.ps1` rodava git sync a cada 30s (`$gitTimer`).
2. Após cada push do Eco, chamava `memory_engine.py log "git-sync: EcoSystemUmGrau"`
   (linha 283) — que **faz append de 1 linha** em `conhecimento/memoria/sessions/YYYYMMDD.jsonl`
   (arquivo DENTRO do repositório).
3. Esse append disparava o FileSystemWatcher do próprio repo — que tinha sido
   **auto-descoberto como "projeto"** (bug: `EcoSystemUmGrau` tem git remote + `.git`,
   então o filtro de descoberta o pegou como se fosse um projeto Android).
4. Watcher → novo sync → novo commit + push → novo `log` → **loop infinito**.

Prova: cada commit automático tinha exatamente `sessions/20260808.jsonl | 1 +`; o arquivo
acumulou 353 linhas em um único dia.

## Correção aplicada
1. Removidas as chamadas `memory_eng
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[secrets-guard-no-preflightcheck]]