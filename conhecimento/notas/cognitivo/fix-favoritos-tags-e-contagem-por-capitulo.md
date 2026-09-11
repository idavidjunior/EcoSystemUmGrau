---
tags: [boot, cognitivo, fallback, general, quebrava, vigor]
aliases: [fix favoritos tags e contagem por capitulo]
date: 2026-08-09
---

# fix favoritos tags e contagem por capitulo

**Dominio:** general

---
tipo: erro
tags: [biblia, favoritos, sqlite, schema, migracao, contagem, capitulo]
data: 2026-08-09
contexto: Bug de favoritos reportado pelo usuário + pedido de contagem de favoritos/notas por capítulo
decisao: Renomear coluna `tag` para `tags` no banco pré-populado e adicionar migração defensiva; reativar spinner de capítulos com contagens; marcar versículo favoritado com ★
impacto: Favoritos voltaram a funcionar; capítulos mostram quantos versículos estão favoritados e quantas notas exist

---
tipo: erro
tags: [opencode, config, llm, placeholder, model_not_found, eco-system, sync]
data: 2026-08-09
contexto: Ao trocar de LLM, contextos, tarefas e projetos deixaram de ser reconhecidos em sessoes novas. Investigacao revelou que o placeholder {{LLM_MODEL}} no config de opencode NAO e substituido pelo opencode, gerando model_not_found que quebrava o boot das sessoes novas (sem fallback em vigor).
decisao: Substituir o placeholder nao-resolvivel por {env:LLM_MODEL} (mecanismo nativo de 

---
tipo: erro
tags: [config, opencode, preflight, llm_model, template]
data: 2026-08-09
contexto: "@sync - preflight falhou com 'Secrets: env LLM_MODEL AUSENTE'"
decisao: >
  O commit 323a3879 trocou o placeholder "{{LLM_MODEL}}" por "{env:LLM_MODEL}"
  no template config/opencode.jsonc, MAS o setup-auto.ps1 continua renderizando
  "{{LLM_MODEL}}" (Replace com chaves duplas). Como nunca houve match, o deployed
  manteve "{env:LLM_MODEL}" literal e o preflight passou a exigir a env var
  LLM_MOD

---
tipo: erro
tags: [preflight, gate, etica, performance, scan-repo]
data: 2026-09-09
contexto: O gate de persistencia (persistencia.ps1) quedava preso sem commit/sem push durante horas. O preflight técnico (preflight_check.py) rodava mas o bloco [7] Preflight Etico estourava timeout de 240s, bloqueando cada commit.
decisao: Adicionar 'Projetos' (apps Android externos, ~29k arquivos) aos skip_dirs dos scans scan_repo() e data_inventory() de scripts/preflight_etica.py. Projetos é código de APP, 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]