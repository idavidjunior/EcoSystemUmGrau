# Relatório Operacional — Ciclo 1: Fundamentos

Categoria: episodio
Fonte: Missão permanente de capacitação web — Ciclo 1
Projeto: EcoSystemUmGrau
Dominio: Engenharia Web — bloco A

## MISSION
Desenvolver e validar um servidor web mínimo em stdlib (http.server) capaz de
servir HTML e JSON, como primeiro bloco da trilha de capacitação web do
ecossistema.

## STATUS
Concluído e consolidado em 2026-09-08. Evidência: teste de integração
passando (re-executado e confirmado OK).

## ENTREGAS
- server.py: servidor stdlib com ThreadingHTTPServer + BaseHTTPRequestHandler,
  rotas `/` (HTML pt-BR) e `/api/health` (JSON), 404 JSON para o restante,
  visual com paleta Catppuccin.
- test_server.py: teste auto-contido (thread daemon + shutdown/server_close,
  porta 8091, httpx + urllib, sem kill de processo).
- README.md do lab: padrão de uso e resultado da validação.
- ADR-001: decisão consolidada (stdlib + jinja2 3.1.6); alternativa FastAPI +
  uvicorn adiada ao ADR-003.
- Aprendizado do Ciclo 1 consolidado em arquivo único
  (2026-09-08-ciclo1-fundamentos-servidor-stdlib.md).

## TESTES EXECUTADOS
python conhecimento/web/labs/ciclo-1-fundamentos/test_server.py
-> OK: servidor stdlib, HTML, JSON, 404, urllib — tudo validado.

## EVIDÊNCIAS
- Mapa A -> VALIDATED/3 (servidor stdlib validado por teste real).
- Mapa F -> UNDERSTOOD/2 (comparação ThreadingHTTPServer vs uvicorn
  registrada no roadmap, ainda sem teste dedicado).

## FALHAS ENCONTRADAS
- validar.py removido: chamava main(args=(8000,)) inválido e usava URLs
  hardcoded na porta 8000. Não recriar.
- __pycache__/server.cpython-312.pyc regenerado pela execução do teste
  (limpeza opcional, sem impacto funcional).

## RISCOS E DEPENDÊNCIAS
- Micro-lab de DOM do Ciclo 1 não coberto pelo teste validado (lacuna honesta,
  registrada no roadmap).
- fastapi/flask/sqlalchemy não instalados; decisão de uso deferida ao Ciclo 2
  via ADR-003.
- Postgres/Redis (G) e Docker (K) não verificados.
- Node.js/npm ausentes: blocos B/C (React/Next/TS) deferidos à Iteração 2.

## PRÓXIMA AÇÃO
Ciclo 2 — Backend estruturado (bloco F/L): rotas múltiplas, parâmetros,
status codes, erros JSON (404/405/500), sessão ThreadingHTTPServer vs uvicorn,
ADR-003 (uvicorn puro vs FastAPI) e mini-API com 3+ rotas mais teste de
integração no padrão auto-contido do Ciclo 1.