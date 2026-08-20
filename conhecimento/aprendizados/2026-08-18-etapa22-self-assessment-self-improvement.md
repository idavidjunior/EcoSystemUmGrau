---
tipo: padrao
tags: [etapa22, self-assessment, self-improvement, metricas, baseline, experimentos, rollback, drift, gaming]
data: 2026-08-18
contexto: Implementação da Etapa 22 — Self-Assessment / Self-Improvement no EcoSystemUmGrau
decisao: Criar dois módulos: self_assessment_engine.py (métricas, baseline, assessment, scorecard, root cause, drift, gaming detection, self-critique, integração fail-soft com ETAPA 18/20/21) e improvement_engine.py (candidates, fila, experimentos A/B, shadow, feature flags, safety gate, rollback, decision records, journal). 70 testes adversariais. Nenhum módulo existente modificado.
impacto: O ecossistema agora pode medir seu desempenho objetivamente, detectar degradação, propor melhorias com evidência, experimentar de forma controlada e reverter se necessário. Métricas são derivadas de eventos reais, não de autoavaliação.
```

## Aprendizado

1. Autoavaliação não é verdade: "Minha resposta foi excelente" não constitui evidência. O sistema deve procurar validação, feedback do usuário, testes e resultado objetivo. O Self-Critique é EXPLÍCITO: "OBSERVATION, not truth."

2. Métricas devem ser derivadas de eventos reais e auditáveis. O MetricGamingDetector detecta oscilação artificial, saltos súbitos e tool avoidance. Critérios de avaliação não podem ser modificados pelo candidato que está sendo avaliado.

3. Correlação não é causalidade: "mais retries + mais falhas" não significa "retries causam falhas". Pode significar que "falhas provocam retries". O diagnóstico deve distinguir.

4. Baseline é pré-condição: sem baseline, não há comparação possível. Toda melhoria exige baseline + experimento + comparação. "Melhorou" sem comparação é opinião.

5. Feature flags são a forma mais segura de rollout: ativação/desativação instantânea, rollback em segundos. Toda melhoria adotada deve ter uma flag.

6. Safety Gate é obrigatório antes de qualquer adoção: risk_assessment + experiment_result + regression_check + security_check + confidence_check. Nenhuma melhoria pula o gate.

7. O Improvement Level máximo é configurável e o sistema NÃO pode auto-elevar seu nível. Isso previne loops de autoaperfeiçoamento infinitos.

8. Failure→Test é especialmente importante: quando um bug é corrigido, o sistema deve gerar um teste de regressão para que o mesmo problema não volte. A falha passada vira proteção futura.
