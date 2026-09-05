---
tags: [alto, bloqueando, che, fazendo, opencodeopencode, padrao]
aliases: [deduplicacao memoria semantica]
date: 2026-09-02
---

# deduplicacao memoria semantica

**Fonte:** opencode+opencode

Tipo: padrao

Tags: [memoria, dedup, semantica, melhoria, memory_engine]

Data: 2026-09-02

Contexto: O usuário pediu que o auto-evolution aprendesse sozinho sem depender de alguém lembrar, e que o registro de memórias evitasse lixo/redundância: antes de criar memória nova, verificar por similaridade semântica e, se houver referência pré-existente, apenas atualizá-la em vez de duplicar.

Decisão: (1) Deduplicação global por similaridade no memory_engine.add_memory, mesclando conteúdo na memória existente quando o score cosseno (índice semântico memory_semantic) >= 0.80. Criar nova memória apenas quando não há referência. Desligável via env MEMORY_DEDUP=0 ou flag --no-dedup. (2) AUTO-EVOLUTION TIMER no scripts/vigilante.ps1 (padrão do LEARN TIMER, gate diário por data): roda auto_evolution.py evolve a cada 24h — dry-run sempre (assessment + detecção de gaps, inerte) + apply curado de 1 plano de baixo risco quando há executor (opencode/ler), com o motor bloqueando risco alto, fazendo che
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]