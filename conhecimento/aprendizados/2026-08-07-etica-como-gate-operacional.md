---
tipo: decisao
tags: [etica, governanca, clausula-petrea, lgpd, privacidade, preflight]
data: 2026-08-07
contexto: Diagnóstico do ecossistema moral identificou 4 lacunas: ética declarativa (não operacional), cláusulas pétreas sem deveres externos, ausência de gate de bloqueio ético e falta de política de retenção de dados.
decisao: Implementar 4 correções completas — (1) agente 04-etica operacional, (2) Cláusula Pétrea de Deveres Externos na Constituição, (3) preflight_etica.py como gate de bloqueio integrado ao preflight técnico, (4) política de retenção + inventário + rotação de dados.
impacto: Ética deixou de ser declarativa e passou a ser gate operacional obrigatório. Toda entrega que toque dados/usuários/impacto externo é bloqueada se não passar no preflight ético.
recursos: scripts/preflight_etica.py, scripts/rotacao_dados.py, conhecimento/etica/POLITICA_RETENCAO.md, conhecimento/etica/inventario_dados.json, config/agents/04-etica.md, config/agents/00-system-rules.md
nota: Teste negativo confirmou que o preflight bloqueia corretamente quando a política de retenção está ausente (exit 1).
---

## Conexoes

- [[cluster-hub-programacao]]