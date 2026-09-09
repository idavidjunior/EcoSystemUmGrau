---
tipo: padrao
tags: [engenharia-web, persistencia, sqlite3, bloco-g, stdlib, migrations]
data: 2026-09-09
contexto: Missão de capacitação web — Ciclo 5 (Persistência web, bloco G) encerrado com validação real (test_persistencia.py: STATUS OK, 25 checks, 0 falhas; CRUD HTTP + migrations v1→v2 + persistência real entre reinícios). ADR-003 mantido (HTTP stdlib), ADR-005 criado (sqlite3 stdlib).
decisao: Persistência web com sqlite3 stdlib operada por fachada Dashboard: migrations versionadas via PRAGMA user_version, escrita atômica commit/rollback, threading.Lock, WAL e foreign_keys=ON. Uma conexão por operação. Handler HTTP nunca toca SQL direto. Banco data/app.db ignorado no git (recriado por migrations).
impacto: Bloco G = VALIDATED/3 com persistência real em disco no roadmap web; Ciclo 5 concluído; próximo Ciclo 6 (Segurança OWASP). PostgreSQL/Redis permanecem condicionados ao produto (Ciclo 8).
---

# Ciclo 5 — Persistência web (sqlite3)

## O que foi validado

- `python conhecimento/web/labs/ciclo-5-persistencia-web/test_persistencia.py` → `STATUS: OK (25 checks, 0 falhas)`.
- CRUD completo: POST 201 (valida título), GET lista (exclui arquivadas), GET/PUT/PATCH/DELETE por id com 404 coerente.
- Persistência REAL: servidor S2 reabre o mesmo arquivo SQLite em disco e recupera a nota (não é estado em memória).
- Migrations aplicadas em ordem via `PRAGMA user_version` (v1 cria `notas`, v2 cria índice em `titulo`); health expõe `schema_version`.
- Adversarial: POST sem título/vazio → 400; corpo JSON inválido → 400; rota inexistente → 404; `/api/explode` → 500; PUT/PATCH/DELETE de id inexistente → 404.

## Padrão consolidado

- `Dashboard` encapsula toda persistência (migrations, conexão, lock, transações); handler HTTP delega, nunca escreve SQL direto.
- Escrita atômica: toda mutação em `try/commit/except rollback`; conexão nova por operação (abre/fecha), thread-safe via `threading.Lock`.
- Bancos gerados por labs (`data/*.db`) NÃO são versionados — adicionados ao `.gitignore`; o código recria via migrations.
- Bug corrigido no caminho: `WHERE` após `ORDER BY` em SQL é erro de sintaxe — construir WHERE antes do ORDER BY.

## Próximo

Ciclo 6 — Segurança OWASP (I): validação de entrada, headers seguros, CORS, sanitização, rate limit; auditoria com skill security-review nos labs anteriores.
