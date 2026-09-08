# 2026-09-08 - Decisão do backend web inicial — stdlib + jinja2

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema (13 fases; FASES 1–3 entregues). O Ciclo 1 (Fundamentos) foi validado com servidor http.server em stdlib + teste httpx real (test_server.py PASSANDO; mapa bloco A = VALIDATED/3). O Ciclo 2 (Backend estruturado) exige rotas múltiplas, parâmetros, status codes corretos e erros JSON. Este ADR fixa a base do backend para os ciclos web sem dependências novas.
**Projeto:** EcoSystemUmGrau

## Decisão

Backend web inicial em Python **stdlib** (http.server/ThreadingHTTPServer + BaseHTTPRequestHandler), estendido conforme o padrão validado no Ciclo 1. **jinja2** (v3.1.6, já instalado) para renderização de templates quando necessário. **FastAPI** fica documentada como alternativa madura, a ser decidida no **ADR-003** (uvicorn puro vs FastAPI) no Ciclo 2, apenas se a complexidade real provar necessidade.

## Alternativas consideradas

1. **Alternativa A — stdlib + jinja2** — zero dependências novas, padrão já validado no Ciclo 1, controle total sobre o servidor, fácil auditoria e reversibilidade.
2. **Alternativa B — FastAPI + uvicorn** — maior produtividade, validação automática e OpenAPI; porém não instalado hoje, introduz dependência nova e uma decisão de stack maior (adiada ao ADR-003).

## Por quê

O Ciclo 1 entregou evidência real com stdlib (servidor HTTP, HTML, JSON, resposta 404 — tudo validado por teste). Aplicando mudança mínima segura e REUTILIZAR > ADAPTAR > ESTENDER > CRIAR, o backend segue por stdlib sem depender de decisões externas (Node.js fica na Iteração 2). Adiar FastAPI evita dependência especulativa e mantém a trilha Python-first operacional ciclo a ciclo; a troca, se necessária, será deliberada e registrada no ADR-003.