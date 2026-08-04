---
tags: [atingido, bug, lerauditoria, objetivo, prematura, projeto]
aliases: [max_iterations hard stop forca parada prematura mesmo sem ob]
date: 2026-08-04
---

# max_iterations hard stop forca parada prematura mesmo sem objetivo atingido

**Projeto:** ler_auditoria

## Causa Raiz
Loop principal usava while self.iteration < self.max_iterations (100) como criterio de saida, ignorando se o objetivo foi alcancado

## Correcao
Substituido por deteccao de estagnacao: 30 iteracoes sem progresso. max_iterations subiu para 1000 como seguranca.
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ler]]
- [[executor-nao-validava-resultado-real-da-implementacao]]
- [[nao-havia-feedback-loop-do-usuario-ler-terminava-mesmo-se-ob]]
- [[persistencia-sem-atomicidade-crash-no-meio-do-jsondump-corro]]
- [[score-threshold-mas-sem-failedsteps-ia-direto-para-successve]]