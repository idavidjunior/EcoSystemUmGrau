---
tags: [bug, lerauditoria]
aliases: [Logs sem rotacao — logs cresciam indefinidamente]
date: 2026-08-01
---

# Bug: Logs sem rotacao — logs cresciam indefinidamente

**Projeto:** ler_auditoria

## Causa Raiz
Session.log escrevia sempre no mesmo arquivo sem limite de tamanho

## Correcao
_rotate_log() rotaciona em 5 niveis ao atingir 512KB.
