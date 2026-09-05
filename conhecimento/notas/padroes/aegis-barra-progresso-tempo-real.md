---
tags: [message, mpsc, opencodeopencode, padrao, renderizando, windows]
aliases: [aegis barra progresso tempo real]
date: 2026-08-13
---

# aegis barra progresso tempo real

**Fonte:** opencode+opencode

Tipo: padrao

Tags: [aegis, rust, progresso, cli, tokio, broadcast]

Data: 2026-08-13

Contexto: Feature de barra de progresso em tempo real nas varreduras do Aegis

Decisão: EventBus reescrito com tokio::sync::broadcast (canal 256) com evento Progress { percent, message }. SDK exporta ProgressFn = &dyn Fn(f64, &str). Cada scanner ganhou scan_with_progress com marcos por fase. Orchestrator computa percentual global por modulo e passa callback. CLI usa ProgressUI (thread + mpsc + broadcast) renderizando barra Windows com █/░ e \r. Ctrl+C durante o scan pergunta via interactive::confirm antes de encerrar.

Impacto: Varredura agora mostra progresso real em tempo real; testes de EventBus para Progress adicionados. Compilou e passou 11 testes (7 core + 4 sdk). Commit 1440126 no repo Aegis.
## Conexoes

- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[fase2-limpeza-git-artefatos-rastreados]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]