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
  LLM_MODEL, inexistente no ambiente.
  Correcao aplicada: reverter template para "{{LLM_MODEL}}" (consistente com o
  setup-auto.ps1) e renderizar o deployed config com o modelo salvo em
  config/.llm-choice.json (opencode/big-pickle), com backup .bak.
impacto: >
  Preflight voltou a passar (13/13 MCPs, secrets OK, etico OK). Padrao a manter:
  todo placeholder de template deve usar {{VAR}} (renderizado pelo setup-auto.ps1),
  nunca {env:VAR}, a menos que a env var exista de fato no ambiente.
  Tambem foi descoberto que o commit b27dc11 reportado da Biblia nao existia:
  o trabalho da pesquisa biblia estava na working tree sem commit; commitado como
  ef256c4 e publicado em origin/master (o remote NAO tem branch main).
