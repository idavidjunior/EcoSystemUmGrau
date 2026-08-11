---
tipo: decisao
tags: [autonomia, clausula-petrea, reindexacao, memoria-semantica, evolver]
data: 2026-08-07
contexto: O usuário pediu que a reindexação semântica seja automática e definiu como ponto central o conceito de autonomia: implementar melhorias detectadas sem pedir permissão, apenas comunicando. Deve servir de regra global e permanente.
decisao: 1) memory_engine.add_memory agora dispara reindexar_semantico() automaticamente (TF-IDF + dense, best-effort, nunca bloqueia o add; flag --no-reindex para lote). 2) Adicionada à Constituição a Cláusula Pétrea de AUTONOMIA INFORMADA: comunicar primeiro, implementar sem pedir permissão quando a mudança for real, consistente e tornar o ecossistema mais efetivo/eficiente/inteligente; registrar aprendizado; nunca quebrar o que funciona (preflight).
impacto: Memória #175 de teste comprovou o ciclo: add -> REINDEX (647 docs) -> busca por significado recuperou a memória nova no topo imediatamente. Constituição com 9 regras, 3 camadas consistentes. Sync deployada OK. Comportamento esperado: evolução cumulativa e informada.
status: operacional
