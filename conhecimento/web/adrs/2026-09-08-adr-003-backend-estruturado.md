# 2026-09-08 - Decisão do backend estruturado — manter ThreadingHTTPServer stdlib

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema (13 fases; FASES 1–3 entregues). O Ciclo 1 (Fundamentos) foi validado com servidor http.server em stdlib (bloco A = VALIDATED/3). O Ciclo 2 (Backend estruturado) foi validado Com rotas múltiplas, parâmetros, status codes corretos, erros JSON e guarda de corpo (test_server.py PASSANDO: STATUS OK, 14 checks, 0 falhas; bloco F alvo VALIDATED/3). O ADR-001 adiou para este ADR a decisão uvicorn puro vs FastAPI. Este ADR fixa a base para os próximos ciclos web.
**Projeto:** EcoSystemUmGrau

## Decisão

Manter e estender o **ThreadingHTTPServer** da stdlib como backend do Ciclo 2, seguindo exatamente o padrão validado no Ciclo 1 (rotas múltiplas, parâmetros via query string, status codes, erros JSON e tratamento de método não permitido). **uvicorn puro** fica documentado como alternativa madura para os Ciclos 4+ (async/WebSocket em produção) e **FastAPI** continua fora por estar sem instalação e por não haver necessidade real comprovada hoje.

## Alternativas consideradas

1. **Alternativa A — ThreadingHTTPServer stdlib (estender ADR-001)** — zero dependências novas, padrão já validado em dois ciclos, controle total, fácil auditoria e reversibilidade; atende todos os 14 checks com evidência.
2. **Alternativa B — uvicorn puro (ASGI)** — produtividade e caminho natural para async/WebSocket futuros, porém adiciona runtime e convenções novas sem necessidade real no Ciclo 2 (sem I/O intenso nem streaming).

## Por quê

O Ciclo 2 entregou evidência real: 14/14 checks passando com stdlib (POST validando corpo JSON, 400/404/405/500 coerentes, testes adversarial incluídos). Pelo princípio da mudança mínima segura e REUTILIZAR > ADAPTAR > ESTENDER > CRIAR, o backend permanece em stdlib sem decisão de stack externa. uvicorn será reavaliado no ciclo em que o async/WebSocket provar necessidade; FastAPI, apenas se o ecossistema precisar de OpenAPI/validação automática com demanda comprovada.