---
tipo: padrao
tags: [integracao, vigilancia, integridade, knowledge_graph, truncamento, restauro]
data: 2026-09-05
contexto: O connaissance_graph.json (ler-runtime/knowledge/) é a fonte de verdade do conhecimento, mas um histórico de sanitização em duas etapas (primeiro --safe/--sanitize dos padrões e depois o separador de arquivos) deixou o arquivo truncado em uma etapa sem que a segunda completasse. Não havia detecção estrutural: o gráfico "faltando listas" não era pego por min_arquivos, e qualquer um que rodar o separador em um arquivo que ainda passa mojibake/truncamento de texto poderia reduzir/truncar o conhecimento silenciosamente.
decisao: Evoluir scripts/integrity_guard.py para ser um guardião estrutural do knowledge_graph, além do guardião textual de mojibake. O motor identifica o schema canônico, contagens mínimas por seção, baseline de contagens, discernimento de intenção (evolução legítima vs truncamento) e autorrestauro com rollback.
implementacao:
  - GRAPH_SCHEMA_KEYS: version, last_updated, projects, patterns, decisions, bug_fixes, cognitive_patterns, heuristics, frameworks, tool_knowledge, skill_references, mission_learnings (extras legítimos: bugs, research, _last_reload)
  - GRAPH_MIN_COUNTS: patterns>=250, decisions>=85, bug_fixes>=40, cognitive_patterns>=60, heuristics>=20, frameworks>=5, skill_references>=2, mission_learnings>=100, projects>=2
  - Baseline aprendido automaticamente em runtime/integrity_guard_state.json (sem flag --prime), apenas de gráficos sãos (estrutura ok) ou após restauro bem-sucedido
  - Discernimento de intenção (_compara_baseline): atual >= 95% do baseline = evolução legítima; abaixo = truncamento suspeito; sem baseline = sem comparação
  - Autorrestauro (_restaura_graph) em --fix: escolhe o melhor backup .bak_* válido no schema da mesma pasta (maior total de contagens), cria backup do estado atual em runtime/backups/integrity_guard/, copia, pós-valida e faz rollback automático se a restauração falhar
  - _scan_graph_estrutura retorna intencao/contagens no relatório; relatório agora relê contagens do arquivo restaurado (não do estado corrupto) para refletir o estado final
  - Integrações mantidas: runtime_boot --check, preflight_check seção [10], jarvis_bridge --check --json
  - Exclusivamente stdlib (only json/shutil/os), sem novas dependências
validacao:
  - --check default: 302 patterns / 103 decisions / 52 bug_fixes / 81 cognitive_patterns / 32 heuristics / 10 frameworks / 3 skill_references / 134 mission_learnings / 4 projects, exit=0
  - Teste sintético (alvo em temp com listas truncadas a 5 itens): --check acusou CORROMPIDO com mensagens de truncamento mínimas; --fix restaurou do backup escolhido, exit=0, arquivo final saudável
  - Rollback testado: estado truncado preservado em backup em runtime/backups/integrity_guard/ antes do restauro
  - Nenhum backup de truncamento real encontrado no repo (bak_truncado_passadas tem contagens saudáveis)
  - preflight_check: TODOS TESTES PASSARAM (12 MCP online, seção [10] integridade)
  - Baseline do gráfico real aprendido; entrada de teste sintético removida do estado
impacto: O conhecimento de longo prazo agora tem um sistema de guarda estrutural: qualquer operação que reduza as listas do gráfico abaixo dos mínimos ou em queda >=95% vs baseline é detectada no boot/preflight, e um --fix restaura a partir do backup mais saudável com rollback seguro. A confiança de que o knowledge_graph jamais será truncado silenciosamente aumenta substancialmente.
