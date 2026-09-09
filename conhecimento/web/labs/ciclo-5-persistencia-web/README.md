# Ciclo 5 — Persistência Web (bloco G)

**Status:** VALIDADO
**Data:** 2026-09-09
**Mapa:** bloco G → VALIDATED/3
**Stack:** sqlite3 (stdlib) + ThreadingHTTPServer stdlib (ADR-003 mantido; ADR-005)
**Arquivos:** `server.py`, `test_persistencia.py`, `index.html`, `data/app.db`

## Entrega

API HTTP com persistência real em banco sqlite3, no mesmo padrão dos ciclos anteriores (server stdlib + teste de integração auto-contido):

- `GET /` — página `index.html` (CRUD via fetch).
- `GET /api/health` — status do servidor + estatísticas do banco (`schema_version`, `notas`, caminho).
- `POST /api/notas` — cria nota (201; valida `titulo` obrigatório; 400 para corpo inválido/vazio). Ponto único de escrita.
- `GET /api/notas` — lista notas ativas (exclui arquivadas).
- `GET /api/notas/<id>` — nota por id (404 se ausente).
- `PUT /api/notas/<id>` — atualiza título/conteúdo (valida título vazio; 404 se inexistente).
- `PATCH /api/notas/<id>` — arquiva nota (404 se inexistente).
- `DELETE /api/notas/<id>` — exclui nota.
- `GET /api/explode` — erros internos → 500 com JSON de erro (adversarial).

## Persistência

- Banco SQLite em `data/app.db`, criado no primeiro uso. `PRAGMA journal_mode=WAL`, `foreign_keys=ON`.
- Migrations versionadas via `PRAGMA user_version`: v1 cria `notas`, v2 adiciona índice em `titulo`. Aplicadas em ordem na inicialização (thread-safe via lock).
- Escritas atômicas: toda mutação roda `commit` com `rollback` automático em falha — ponto único de persistência do lab (gate).
- Estado REAL em disco: dados sobrevivem ao reinício do servidor (validado no teste: S2 abre o mesmo banco e reencontra a nota).

## Como validar

```
python conhecimento/web/labs/ciclo-5-persistencia-web/test_persistencia.py
```

## Resultado

```
[PASS] GET / index.html servido
[PASS] health indica banco e schema
[PASS] POST cria nota 201
...
[PASS] dados persistem apos reinicio
[PASS] nota persistida recuperavel por id
STATUS: OK (25 checks, 0 falhas)
```

## Notas de arquitetura

- `Dashboard` encapsula toda persistência: migrations, conexão, lock e transações. O HTTP handler nunca toca SQL direto (Separation of Concerns).
- Uma conexão nova por operação (abre/fecha), segura e sem cache de conexão improvável de vazar sob threads.
- Padrão do mapa: todo estado local real é persistido via banco, não em memória.

## Decisão

ADR-005 (`conhecimento/web/adrs/2026-09-09-adr-005-persistencia-sqlite3.md`): sqlite3 como camada de persistência web (stdlib, zero dependência); ThreadingHTTPServer mantido (ADR-003); PostgreSQL/Redis só se o produto exigir (decisão externa pendente no roadmap).