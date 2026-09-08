# Relatório Operacional — Ciclo 1 (Fundamentos Web)

**Categoria:** episodio
**Fonte:** Missão permanente de capacitação web (2026-09-08)
**Projeto:** EcoSystemUmGrau
**Dominio:** Engenharia Web — bloco A/F

## MISSION (objetivo cumprido)

Validar na prática os fundamentos do bloco A (HTML, CSS, HTTP, JSON, DOM,
acessibilidade) com evidência executável, sem estrutura nova e sem dependências
externas. Criar o padrão de micro-lab que os ciclos seguintes reutilizam.

## STATUS

Ciclo 1 concluído em 2026-09-08. Mapa bloco A = VALIDATED/3. Mapa bloco F =
UNDERSTOOD/2 com nota do micro-lab (servidor stdlib + JSON validado). Roadmap
atualizado (linha "Ciclo 1 — Fundamentos (A/F) — concluído").

## Entregas

- Micro-lab `labs/ciclo-1-fundamentos/`: server.py (stdlib http.server,
  ThreadingHTTPServer), test_server.py (httpx + urllib, auto-contido),
  README.md (documentação do lab).
- ADR-001 (`conhecimento/web/adrs/2026-09-08-adr-001-backend-inicial.md`):
  backend web inicial em stdlib + jinja2; FastAPI diferida ao ADR-003.
- Aprendizado consolidado (`conhecimento/aprendizados/2026-09-08-ciclo1-fundamentos-servidor-stdlib.md`);
  duplicata removida.
- Roadmap com Ciclo 1 marcado concluído e Ciclo 2 descrito.

## Testes executados

`python conhecimento/web/labs/ciclo-1-fundamentos/test_server.py`

```
OK: servidor stdlib, HTML, JSON, 404, urllib — tudo validado.
```

Cobertura real: `GET /` 200 text/html (pt-BR); `GET /api/health` 200
application/json (status=ok, servidor, tempo ISO); rota desconhecida 404 com
JSON de erro; `urllib` confirma o mesmo health sem dependência externa.

## Evidências

- Saída do teste registrada no README do lab.
- Mapas e ADR-001 re-verificados por leitura direta nesta sessão.
- `runtime_boot.py --check` → INTEGRIDADE: OK.
- `runtime_state.py` registrou a conclusão no histórico do runtime.

## Falhas encontradas

- `validar.py` removido: chamava `main(args=(8000,))` incompatível e URLs com
  porta hardcoded — não deve ser recriado.
- `__pycache__/server.cpython-312.pyc` regenerado pela execução do teste
  (limpeza opcional, sem impacto funcional).

## Riscos / dependências

- Node.js/npm ausentes bloqueiam B/C (decisão externa, Iteração 2).
- Busca MCP com timeout (-32603) e `memory_engine.py add` com hang (>120s):
  registrar conhecimento via arquivos.
- Micro-lab de DOM não coberto pelo teste validado (lacuna honesta, sem falso
  VALIDATED).

## Próxima ação

Iniciar Ciclo 2 — Backend estruturado (rotas múltiplas, parâmetros, status
codes 404/405/500, erros JSON, ThreadingHTTPServer vs uvicorn, ADR-003,
mini-API 3+ rotas + teste de integração). Nunca executar dois ciclos de uma vez.