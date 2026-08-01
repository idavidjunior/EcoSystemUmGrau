---
tags: [bug, lerauditoria]
aliases: [max_iterations hard stop forca parada prematura mesmo sem ob]
date: 2026-08-01
---

# Bug: max_iterations hard stop forca parada prematura mesmo sem objetivo atingido

**Projeto:** ler_auditoria

## Causa Raiz
Loop principal usava while self.iteration < self.max_iterations (100) como criterio de saida, ignorando se o objetivo foi alcancado

## Correcao
Substituido por deteccao de estagnacao: 30 iteracoes sem progresso. max_iterations subiu para 1000 como seguranca.
