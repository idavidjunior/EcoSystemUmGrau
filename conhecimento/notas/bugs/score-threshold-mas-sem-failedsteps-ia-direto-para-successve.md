---
tags: [bug, lerauditoria]
aliases: [Score < threshold mas sem failed_steps ia direto para SUCCES]
date: 2026-07-29
---

# Bug: Score < threshold mas sem failed_steps ia direto para SUCCESS_VERIFIED

**Projeto:** ler_auditoria

## Causa Raiz
_phase_success_eval verificava apenas failed_steps, nao o score real. Se todos steps 'completaram' com bugs, LER considerava sucesso.

## Correcao
Score < threshold sempre vai para REPLANNING. Idem para _phase_final_audit.
