---
tipo: decisao
tags: [idioma, pt-br, clausula-petrea, constituicao, regras, config]
data: 2026-08-08
contexto: O usuário relatou dificuldade em fazer o sistema responder sempre em português do Brasil por padrão; respostas vinham em inglês com frequência. Não existia nenhuma regra explícita de idioma no ecossistema.
decisao: Adicionada a CLÁUSULA PÉTREA — IDIOMA PADRÃO — PORTUGUÊS DO BRASIL (PT-BR) à Constituição (config/agents/00-system-rules.md), logo após a SOBERANIA DO RUNTIME E DO KERNEL. A cláusula obriga todo agente a responder, comunicar, documentar e narrar sempre em pt-BR por padrão, mantendo nomes técnicos na forma original, sem alternância de idioma e corrigindo imediatamente qualquer resposta que saia em outro idioma. Sincronizado via sync_rules.py update (14 regras nas 3 camadas: Constituição, AGENTS.md, deployed).
impacto: Respostas do ecossistema agora seguem o padrão pt-BR de forma permanente, sem depender de pedido explícito do usuário em cada sessão. O comando @eco continua confirmando a operacionalidade e agora inclui o idioma padrão pt-BR nas regras ativas.
---

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]