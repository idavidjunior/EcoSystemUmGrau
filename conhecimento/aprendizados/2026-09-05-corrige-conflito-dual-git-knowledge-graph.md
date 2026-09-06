---
tipo: erro
tags: [git, persistencia, knowledge-graph, double-tracking, vigia]
data: 2026-09-05
contexto: knowledge_graph.json era versionado simultaneamente por dois repositorios (repo filho ler-runtime com .git proprio e repo pai EcoSystemUmGrau). O repo filho teve o graph truncado (722KB) commitado no HEAD local e no remote; o vigilante rodava git pull --ff-only e merges que recomitavam o estado truncado por cima de qualquer restauracao.
decisao: Restaurar o graph da fonte saudavel .bak_sanitize (6.49MB, contagens 301/103/52/81), zerar debounce_minutos do gate temporariamente (config/persistencia.json), commitar+push via scripts/persistencia.ps1 nos dois repos, restaurar debounce para 30, regenerar notas Obsidian (687 notas), registrar a memoria e criar este aprendizado.
impacto: Conflito resolvido; filho e pai alinhados no estado saudavel; vigilante nao revertera mais o graph; push do filho atualizou origin/master do ler-runtime.
licao: Antes de commit de conhecimento, verificar contagens do graph. Nunca presumir que git pull de repo filho preserva o estado saudavel quando o HEAD do proprio filho contem dados truncados. O gate e o unico ponto de commit: usar persistencia.ps1, nunca git direto. Debounce pode ser zerado temporariamente para commits manuais urgentes, desde que restaurado.

## Conexoes

- [[cluster-hub-programacao]]
- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]