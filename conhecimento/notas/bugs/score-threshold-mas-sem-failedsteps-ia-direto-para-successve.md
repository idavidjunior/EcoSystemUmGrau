---
tags: [bug, lerauditoria, nao, projeto, real, verified]
aliases: [Score < threshold mas sem failed_steps ia direto para SUCCES]
date: 2026-08-09
---

# Score < threshold mas sem failed_steps ia direto para SUCCESS_VERIFIED

**Projeto:** ler_auditoria

## Causa Raiz
_phase_success_eval verificava apenas failed_steps, nao o score real. Se todos steps 'completaram' com bugs, LER considerava sucesso.

## Correcao
Score < threshold sempre vai para REPLANNING. Idem para _phase_final_audit.
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[persistencia-sem-atomicidade-crash-no-meio-do-jsondump-corro]]