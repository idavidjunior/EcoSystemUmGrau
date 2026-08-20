---
tipo: padrao
tags: [etapa21, memoria, aprendizagem, consolidacao, confianca, evidencia, epistemic, poisoning]
data: 2026-08-18
contexto: Implementação da Etapa 21 — Memory + Learning Consolidation no EcoSystemUmGrau, sobre o memory_engine e learning_engine existentes, integrada com Mission Loop (Etapa 20) e Cognitive Core (Etapa 18)
decisao: Criar camada memory_consolidation.py que transforma experiência em memória confiável com status epistêmico, confiança computada, evidências (support/contradict), proveniência, sanitização de segredos, proteção anti-poisoning, deduplicação, importância, retrieval híbrido, Learning Candidate (PENDING→SUPPORTED→VALIDATED/REJECTED), decay não-destrutivo e migração aditiva das 338 memórias existentes.
impacto: Toda memória agora carrega grau de certeza e origem; generalização exige evidência; segredos são redigidos antes de persistir; fontes não confiáveis não injetam instruções; memórias críticas (segurança/arquitetura) nunca são esquecidas. Cognitive Core consome contexto híbrido com fail-soft.
```

## Aprendizado

1. Memória ≠ verdade: sem `epistemic_status` + `confidence` + evidências, uma memória consolidada é apenas uma string. O salto qualitativo da Etapa 21 foi adicionar o grau de certeza e a origem a cada registro, sem apagar nada do que existia (migração aditiva).

2. Confiança é função da FONTE, não do conteúdo: EXPLICIT_USER (0.95) ≠ MISSION (0.7) ≠ WEB (0.5) ≠ HYPOTHESIS (0.25). Ajustes por quantidade de evidências e contradições. Um único episódio de sucesso não valida um padrão.

3. Aprendizado exige evidência acumulada: 1 evidência = PENDING, 2 = SUPPORTED, 3 = VALIDATED. Contradições ≥ suportes = REJECTED. A inferência de `relation` (support/contradict) é heurística; declaração explícita é mais robusta.

4. Sanitização de segredos e anti-poisoning são gates OBRIGATÓRIOS antes de persistir: redigir sk-*/ghp_*/senhas/Bearer/JWT e rejeitar instruções imperativas de fontes não confiáveis. Memória NUNCA pode conceder permissão — autorização é da Etapa 19.

5. Decay deve ser não-destrutivo: reduzir `retrieval_priority` antes de arquivar, nunca apagar. Conhecimento crítico (segurança, arquitetura, regras) é protegido por classificação de kind/source/tags.

6. Fail-soft na integração: Cognitive Core usa `_get_memory_context` que tenta a camada híbrida (ETAPA 21) e cai de volta para `get_context` (ETAPA 18) em qualquer exceção. Regressões 18/19/20 passaram após a integração.

7. Deduplicação por normalização de texto evita cópias; em duplicidade, reforçar a memória existente (strength) em vez de criar novo registro.
