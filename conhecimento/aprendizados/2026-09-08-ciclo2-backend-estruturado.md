---
tipo: padrao
tags: [engenharia-web, backend, rotas, status-codes, erros-json, stdlib, adr]
data: 2026-09-08
contexto: Missão de capacitação web — Ciclo 2 (Backend estruturado) encerrado com validação real (test_server.py: STATUS OK, 14 checks, 0 falhas; incluindo adversarial) e ADR-003 registrado.
decisao: Manter/estender ThreadingHTTPServer stdlib como backend do Ciclo 2 (rotas múltiplas, query params, 400/404/405/500 em JSON, guarda de corpo não-dict e JSON inválido); ADR-003 fixa stdlib vs uvicorn puro (FastAPI fora); corrigir erro de indentação via script Python com escrita atômica quando o tool edit falhar por par idêntico.
impacto: Bloco F do mapa = VALIDATED/3; 14/14 checks passando; ADR-003 registrado; base pronta para o Ciclo 3.
---

# Ciclo 2 — Backend estruturado (rotas, status codes, erros JSON)

## O que foi validado

- `python conhecimento/web/labs/ciclo-2-backend-estruturado/test_server.py` → `STATUS: OK (14 checks, 0 falhas)`.
- Rotas: `/` (200, nome do lab), `/api/health` (200), `/api/soma?a=2&b=3` (200, `soma=5`), `/api/items` (200), `/api/items/7` (200 `id=7`), `/api/items/abc` (404).
- POST `/api/items`: 201 com corpo válido; 400 `"campo nome obrigatorio"` com corpo sem nome; 400 `"corpo JSON invalido"` com `b"{quebrado"` (via `_request_raw`).
- DELETE `/api/items/3` (200 `deletado=3`); PUT (405); rota inexistente (404); `/api/explode` (500 `"erro interno do servidor"` com try/except).
- Teste adversarial incluído: JSON quebrado, parâmetro inválido (`a=x` → 400), id não numérico (404).

## Correção de indentação (pitfall)

- `def do_POST(self):` ficou na coluna 0 com corpo a 8 espaços → `IndentationError: unindent does not match any outer indentation level` na linha seguinte (dedent para 4 espaços de `do_DELETE` não casa nível externo) → quebra o import `from server import start`.
- Falhas repetidas do tool edit por `newString` idêntico ao `oldString` (sem os 4 espaços) não aplicam nenhuma mudança.
- Correção determinística e verificável: script Python que lê o texto, faz `replace` do par e escreve atômico (`tmp` + `os.replace`), imprimindo as linhas alteradas. Evitar depender do tool edit quando o par enviado é idêntico.

## Padrão consolidado

- Backend do lab em stdlib (`ThreadingHTTPServer` + `BaseHTTPRequestHandler`), rotas em dict `ROTAS_VALIDAS`, helpers `_rotas`, `_json`, `_erro`, `_ler_corpo`, `_ids`.
- Teste canônico auto-contido (thread daemon + shutdown/server_close, porta via `server.server_address[1]`), 14 checks com `[PASS]/[FAIL]` e `STATUS: OK/FALHOU (N checks, M falhas)`.

## Próximo

Ciclo 3 — frontend estático com templates (server-side rendering com jinja2) e/ou SPA leve; avaliar uvicorn puro quando async/WebSocket provar necessidade.
