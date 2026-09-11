# 2026-09-10 - Ciclo 9 - ADR-009: Padronização e Publicação da Trilha Web

**Categoria:** decisao
**Contexto:** O Ciclo 9 do roadmap de capacitação web exige entregar um
"build/run script reproduzível, documentação de operação, deploy via GitHub
Pages ou pipe existente", com runbook de operação web como entrega. Os labs
dos Ciclos 1-8 rodavam cada um pelo seu próprio comando, sem um modo
unificado de validar a trilha inteira; o teste do Ciclo 6 não é auto-contido
(requer servidor de pé, porta 8096). O pipe de CI existente do ecossistema é
GitHub Actions (eco-sync.yml, knowledge-report.yml); Docker não está
instalado no ambiente.
**Projeto:** EcoSystemUmGrau

## Decisão

Padronizar a publicação da trilha web em três camadas: (1) um orquestrador
único e reproduzível (`conhecimento/web/run_suite.py`) que roda cada lab no
próprio diretório, cuida do ciclo de vida do servidor do Ciclo 6 e agrega
PASS/FAIL, gravando `benchmarks/ciclo-9-run-suite.json`; (2) um runbook de
operação (`conhecimento/web/RUNBOOK-OPERACAO-WEB.md`) que documenta stack,
comandos por lab, subida do produto do Ciclo 8, medição CWV e
troubleshooting; (3) CI no pipe existente (`.github/workflows/web-ci.yml`),
executando a suíte determinística (Ciclos 1, 2, 3, 5, 6) em todo push/PR
com Python 3.12. GitHub Pages fica registrado como opção futura, não como
deploy ativo: o produto do Ciclo 8 exige backend (HTTP+WS+sqlite+IA), então
Pages não o comporta.

## Alternativas consideradas

1. **Alternativa A — Deploy ativo em GitHub Pages**: incompatível com o
   produto integrado (backend Python + WS); Pages não roda servidor.
2. **Alternativa B — Docker/container para publicar o produto**: Docker
   ausente no ambiente; adicionaria dependência nova sem necessidade real
   para o requisito do Ciclo 9 (runbook + script reproduzível).
3. **Alternativa C — CI por lab, um workflow por ciclo**: duplicaria 8
   workflows com o mesmo setup; o orquestrador concentra a lógica em um
   ponto só (KISS, sem caminho paralelo).

## Por quê

O ambiente já usa GitHub Actions como pipe de publicação — aproveitá-lo
evita estrutura nova. O orquestrador resolve de uma vez dois problemas
reais: padronizar a execução (um comando basta) e cobrir o Ciclo 6, cujo
teste precisa de servidor de pé (subir/aguardar health/rodar/derrubar). O
escopo determinístico (sem IA/playwright) garante CI estável mesmo sem
chaves de LLM ou browsers; `--tudo` fica para rodada local completa.

## Evidência

`run_suite.py` executado localmente em 2026-09-10: STATUS OK (5 labs
aprovados, 0 falhas, 0 skips) — Ciclos 1, 2, 3, 5 e 6; `ciclo-9-run-suite.json`
gerado em `benchmarks/`. Bloco K promovido a VALIDATED/3 no mapa de
competências (`conhecimento/web/README.md`).

**Projeto:** EcoSystemUmGrau