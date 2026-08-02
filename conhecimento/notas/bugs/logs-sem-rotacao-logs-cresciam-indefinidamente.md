---
tags: [bug, lerauditoria]
aliases: [Logs sem rotacao — logs cresciam indefinidamente]
date: 2026-08-01
---

# Logs sem rotacao — logs cresciam indefinidamente

**Projeto:** ler_auditoria

## Causa Raiz
Session.log escrevia sempre no mesmo arquivo sem limite de tamanho

## Correcao
_rotate_log() rotaciona em 5 niveis ao atingir 512KB.
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]