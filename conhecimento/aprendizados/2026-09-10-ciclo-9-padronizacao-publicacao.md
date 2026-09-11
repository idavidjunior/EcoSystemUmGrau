---
tipo: padrao
tags: [ciclo-9, web, padronizacao, publicacao, ci, runbook]
data: 2026-09-10
contexto: Ciclo 9 do roadmap de engenharia web — Padronização e publicação (bloco K). Entrega: run script reproduzível (run_suite.py), runbook de operação (RUNBOOK-OPERACAO-WEB.md), CI no pipe existente (GitHub Actions web-ci.yml), ADR-009.
decisao: Padronizar a validação da trilha web em três camadas: (1) orquestrador único `run_suite.py` que roda os labs determinísticos (Ciclos 1, 2, 3, 5, 6) em sequência, sobe/derruba servidor do Ciclo 6, agrega PASS/FAIL e grava `benchmarks/ciclo-9-run-suite.json`; (2) runbook documentando stack, comandos por lab, produto Ciclo 8, CWV e troubleshooting; (3) CI em `.github/workflows/web-ci.yml` rodando a suíte determinística em todo push/PR com Python 3.12 + httpx + websockets. GitHub Pages registrado como opção futura (produto exige backend).
impacto: Suíte determinística validada localmente (5 labs OK, 0 falhas); suíte completa (--tudo) validada (8 labs OK, 0 falhas). Evidência em benchmarks/ciclo-9-run-suite.json. Bloco K promovido a VALIDATED/3 no mapa de competências. CI pronto para proteger a trilha web contra regressão.
lihoes: (1) O Ciclo 6 não é auto-contido (precisa servidor de pé) — o orquestrador resolve subindo/derrubando com health check. (2) Labs de IA/playwright (--tudo) precisam secrets/browser; CI não roda eles para estabilidade — validação local cobre. (3) Um workflow único concentrado (KISS) evita duplicação de 8 workflows paralelos.

## Conexoes

- [[treinamento-especializado-em-navegacao-multi-plataforma-reco]]