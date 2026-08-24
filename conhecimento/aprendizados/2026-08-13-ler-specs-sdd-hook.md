---
tipo: decisao
tags: [ler, specs, sdd, goal-analyzer, orchestrator, persistencia]
data: 2026-08-13
contexto: A camada de specs (SDD) do LER existia (specs/ com README.md e template.md) mas nao tinha geracao automatica a partir da analise de objetivo. O GoalAnalyzer.analyze() produzia o goal_spec mas nenhum markdown era persistido.
decisao: Fechar o ciclo: GoalAnalyzer.analyze() agora gera analysis['spec_markdown'] = spec.to_spec_markdown(tags=['ler','goal-analysis']) logo apos goal_spec, e o Orchestrator._persist_spec persiste o markdown apos analyze(goal) em _phase_analyze_goal. Destino: config['specs'] = {'enabled': true, 'dir': '../specs'} (relativo resolvido contra base_dir=ler-runtime) com fallback os.path.join(base_dir,'specs'); enabled default true; escrita atomica (tmp + os.replace); id extraido das primeiras 8 linhas (id: spec-...), arquivo = slug sem prefixo 'spec-' + '.spec.md'.
impacto: Toda missao LER agora produz um artefato .spec.md persistido no EcoSystemUmGrau/specs/ com 11 secoes acentuadas (Objetivo, Requisitos, Restricoes, Dependencias, Premissas, Entradas e Saidas, Casos de Borda, Criterios de Aceitacao, Definition of Done, Riscos, Testes Relacionados). Validado com 31 testes unittest (test_ler_v20), smoke de persistencia (sem .tmp residual, enabled=false respeitado, fallback OK) e scripts/valida_specs.py exit 0. Commit f7b3c418.
- criterios gerados aparecem como MANUAL no valida_specs.py (esperado para goal analysis).
- 100% stdlib, fail-soft, sem comentarios novos (regra petrea).

## Conexoes

- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[cluster-hub-ler]]