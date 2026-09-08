---
tipo: padrao
tags: [engenharia-web, fundamentos, servidor-http, stdlib, adr]
data: 2026-09-08
contexto: Missão de capacitação web — Ciclo 1 (Fundamentos A/F) encerrado com validação real (test_server.py PASSANDO) e roadmap atualizado para "concluído".
decisao: Manter o padrão de micro-lab com um só servidor (server.py) + um só teste canônico (test_server.py) por lab; registrar decisões de arquitetura web como ADR usando o template-decisao; não recriar validar.py quebrado.
impacto: Bloco A do mapa = VALIDATED/3; ADR-001 registrado (backend stdlib + jinja2; FastAPI decidida no ADR-003 no Ciclo 2); base pronta para o Ciclo 2.
---

# Ciclo 1 — Fundamentos (servidor stdlib)

## O que foi validado

- `python conhecimento/web/labs/ciclo-1-fundamentos/test_server.py` → "OK: servidor stdlib, HTML, JSON, 404, urllib — tudo validado."
- Teste canônico auto-contido: thread + ThreadingHTTPServer, porta 8091, httpx + urllib, shutdown/server_close.
- server.py: stdlib; paleta Catppuccin; rotas /, /api/health (JSON) e 404 JSON.

## Padrão consolidado

- Um micro-lab = um servidor + um teste canônico auto-contido.
- Ciclo termina com teste executado e evidência em labs/ (README com resultado).
- Decisões de arquitetura → ADR no formato conhecimento/templates/template-decisao.md.
- Não duplicar com scripts quebrados: validar.py foi removido (porta/host errados).

## Próximo

Ciclo 2 — Backend estruturado: rotas múltiplas, parâmetros, status codes correto (404/405/500), ThreadingHTTPServer vs uvicorn, ADR-003 (uvicorn puro vs FastAPI) e mini-API com 3+ rotas + teste de integração.