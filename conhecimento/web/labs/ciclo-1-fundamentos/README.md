# Micro-lab — Ciclo 1 (Fundamentos Web)

**Categoria:** padrao
**Fonte:** Missão permanente de capacitação web (2026-09-08)
**Projeto:** EcoSystemUmGrau
**Dominio:** Engenharia Web — bloco A

## Problema

Validar na prática os fundamentos deste bloco (HTML, CSS, HTTP, JSON, servidores) com
uma evidência executável, sem depender de estrutura nova ou de dependências externas.

## Solução

`server.py` — servidor HTTP padrão (stdlib `http.server`, `ThreadingHTTPServer`) que:

- serve página HTML responsiva em pt-BR (paleta dark do ecossistema) com `GET /`;
- expõe endpoint `GET /api/health` respondendo JSON com status, servidor e tempo ISO;
- responde 404 com JSON de erro para rotas desconhecidas.

`test_server.py` — validação real (httpx + urllib) que sobe o servidor numa thread,
executa as requisições, verifica cada resposta e encerra sem processo externo (evita
flakiness de kill no shell PowerShell).

## Quando usar

Como base para os próximos micro-labs de backend e como exemplo do padrão de evidência:
todo lab termina com teste executado e resultado registrado.

## Resultado da validação

`python conhecimento/web/labs/ciclo-1-fundamentos/test_server.py`

```
OK: servidor stdlib, HTML, JSON, 404, urllib — tudo validado.
```

Rota `/` retorna 200 text/html com `lang="pt-BR"`; `/api/health` retorna 200
application/json com `status=ok`; rota desconhecida retorna 404 com JSON de erro.
Validação também coberta por `urllib` (sem dependência externa).