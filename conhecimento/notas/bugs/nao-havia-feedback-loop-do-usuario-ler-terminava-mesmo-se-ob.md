---
tags: [bug, lerauditoria]
aliases: [Nao havia feedback loop do usuario — LER terminava mesmo se ]
date: 2026-07-29
---

# Bug: Nao havia feedback loop do usuario — LER terminava mesmo se objetivo nao fosse atingido

**Projeto:** ler_auditoria

## Causa Raiz
COMPLETED -> _finalize direto, sem perguntar ao usuario se o resultado foi satisfatorio

## Correcao
Adicionado _ask_user_feedback() em _finalize e _handle_complete. Se usuario rejeita, registra failed_pattern e chama _restart_mission().
