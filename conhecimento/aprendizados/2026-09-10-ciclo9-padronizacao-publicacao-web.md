---
tipo: episodio
tags: [web, devops, ci, publicacao, runbook, ciclo9]
data: 2026-09-10
contexto: Trilha de capacitação web do ecossistema (bloco K — DevOps). Requisito
  do Ciclo 9: build/run script reproduzível, documentação de operação e deploy
  via GitHub Pages ou pipe existente, com runbook de operação web como entrega.
decisao: Padronizar publicação da trilha web com orquestrador único
  (conhecimento/web/run_suite.py) + runbook (RUNBOOK-OPERACAO-WEB.md) + CI no
  pipe existente (web-ci.yml no GitHub Actions). O orquestrador roda cada lab
  no próprio diretório, sobe/derruba o servidor do Ciclo 6 (teste não
  auto-contido) e grava benchmarks/ciclo-9-run-suite.json. Escopo padrão =
  determinístico (Ciclos 1, 2, 3, 5, 6); --tudo inclui IA/playwright (4, 7, 8).
impacto: Bloco K promovido a VALIDATED/3. CI web reage a mudanças em
  conhecimento/web/**; uma regressão de lab determinístico passa a bloquear
  push/PR. GitHub Pages registrado como opção futura (produto do Ciclo 8 exige
  backend). ADR-009 documenta a decisão.
licoes:
  - O teste do Ciclo 6 (segurança) não é self-contained: precisa de servidor de
    pé; o orquestrador precisa subir/aguardar health/rodar/derrubar.
  - Não confiar no marcador textual "STATUS: OK" da saída dos labs para decidir
    sucesso: o Ciclo 1 valida só por exit code. Critério de sucesso = returncode.
  - Ao filtrar escopo determinístico, excluir por requisito (IA/playwright), não
    por "tem servidor": Ciclo 6 tem servidor mas roda no CI com orquestração.
---