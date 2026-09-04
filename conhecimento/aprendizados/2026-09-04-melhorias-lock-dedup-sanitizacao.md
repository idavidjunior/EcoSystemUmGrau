---
tipo: padrao
tags: [melhoria, lock, sanitizacao, dedup, memoria, resiliencia]
data: 2026-09-04
contexto: Durante a consolidação do Cluster A de memórias ADB, três melhorias reais foram detectadas e implementadas com aviso ao usuário (que autorizou implementar melhorias avisando sempre).
decisao:
  1. Lock órfão de memória: memories.json.lock ficava retido e operações falhavam por timeout de 10min até o stale_after de 600s expirar. Reduzido stale_after para 120s em memory_engine.py `_memory_lock(timeout=10, stale_after=120)`. Teste funcional validou: lock antigo (>120s) é removido e adquirido; lock recente bloqueia corretamente.
  2. Hardcoded path em memórias: 98218 e 98233 (idênticas) continham `C:\Users\David Jr\Documents\...` no summary, quebrando test_json_sanitization.py e bloqueando o preflight. Substituído por caminho relativo concluído com sucesso.
  3. Deduplicação geral do acervo: 12 grupos de duplicatas exatas (45 registros), a maioria de rotinas automáticas (preflight ético aprovado etc.). Consolidado 688→644 memórias, mantendo o melhor registro por grupo (maior confidence/access, unificando tags/access_count). Com backup e reindex.
impacto: Acervo mais limpo (menos ruído na recuperação); preflight técnico 100% verde; operações de memória deixaram de falhar por lock órfão; sem hardcoded paths absolutos na base de memória.
notas: Backup temporário .bak-* removido após validação (rede de segurança = git/branch pre-cleanup-voxumgrau). Reindex TF-IDF reexecutado. Preflight Etico aprovado.
