---
tipo: padrao
tags: [aegis, rust, progresso, cli, tokio, broadcast]
data: 2026-08-13
contexto: Feature de barra de progresso em tempo real nas varreduras do Aegis
decisao: EventBus reescrito com tokio::sync::broadcast (canal 256) com evento Progress { percent, message }. SDK exporta ProgressFn = &dyn Fn(f64, &str). Cada scanner ganhou scan_with_progress com marcos por fase. Orchestrator computa percentual global por modulo e passa callback. CLI usa ProgressUI (thread + mpsc + broadcast) renderizando barra Windows com █/░ e \r. Ctrl+C durante o scan pergunta via interactive::confirm antes de encerrar.
impacto: Varredura agora mostra progresso real em tempo real; testes de EventBus para Progress adicionados. Compilou e passou 11 testes (7 core + 4 sdk). Commit 1440126 no repo Aegis.
erros_encontrados:
  - unresolved import aegis_plugin_sdk::ProgressFn -> faltava exportar no lib.rs do SDK
  - E0502 borrow do orchestrator -> future detinha borrow mutavel; envolver em bloco aninhado para dropar antes de collect_findings
  - loop infinito no draina de eventos -> faltavam breaks explicitos no match de try_recv

## Conexoes

- [[rust-ownership-borrow-checker-e-o-modelo-de-memória]]