---
tags: [atingido, bug, lerauditoria, objetivo, projeto, terminava]
aliases: [Nao havia feedback loop do usuario — LER terminava mesmo se ]
date: 2026-08-08
---

# Nao havia feedback loop do usuario — LER terminava mesmo se objetivo nao fosse atingido

**Projeto:** ler_auditoria

## Causa Raiz
COMPLETED -> _finalize direto, sem perguntar ao usuario se o resultado foi satisfatorio

## Correcao
Adicionado _ask_user_feedback() em _finalize e _handle_complete. Se usuario rejeita, registra failed_pattern e chama _restart_mission().
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[persistencia-sem-atomicidade-crash-no-meio-do-jsondump-corro]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]