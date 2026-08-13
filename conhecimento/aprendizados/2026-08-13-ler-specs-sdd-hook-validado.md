---
tipo: decisao
tags: [ler, specs, sdd, goal-analyzer, orchestrator, persistencia, validacao]
data: 2026-08-13
contexto: A camada de specs (SDD) do LER existia (specs/ com README.md e template.md) mas a geracao automatica de spec a partir da analise de objetivo nao tinha sido validada ponta a ponta. O GoalAnalyzer.analyze() ja produzia o goal_spec e o hook _persist_spec estava no orchestrator, mas nenhuma missao real tinha confirmado o ciclo completo.
decisao: Validar o ciclo completo sem rodar missao LER autonoma. Razoes: o config.json do LER tem "git": {"auto_commit": true, "commit_prefix": "[LER]"} e base_dir fixo em ler-runtime, entao uma missao real dispararia commits fora do gate (scripts/persistencia.ps1), violando a clausula petrea de ponto unico de persistencia.
impacto: Lacuna 1 VALIDADA com integracao dirigida: kernel real (LERKernel) + Orchestrator real + config specs dir temporario. analyze(goal) gerou spec_markdown com 12 secoes preenchidas (Objetivo, Requisitos, Premissas, Entradas e Saidas, Casos de Borda, Definition of Done, Riscos, Testes Relacionados, etc.) e _persist_spec gravou arquivo real .spec.md no disco com id spec-..., sem placeholders _definir_. Temp dir limpo via shutil.rmtree, nenhum arquivo deixado no repo, nenhum commit disparado.
- Lacuna 2 aplicada e validada: to_spec_markdown agora gera conteudo real (domain auto-detectado, entradas/saidas a partir de constraints Git/Android, casos de borda e testes relacionados) em vez de secoes vazias; 31 testes OK, py_compile OK, valida_specs.py OK.
- Lacuna 3 (commit generico do gate) nao modificavel, apenas documentada.
- Lacuna 4 (reverificacao do hook no codigo) confirmada: _persist_spec (~161-187) resolve dir contra session.base_dir, escrita atomica tmp + os.replace, fail-soft com log.

## Conexoes

- [[cluster-hub-ler]]