---
tags: [desatualizadas, geram, padrao, planos, ruins, sql]
aliases: [SQL: índices e estratégias de acesso]
date: 2026-08-14
---

# SQL: índices e estratégias de acesso

**Fonte:** sql

### O que é um índice

Estrutura auxiliar (geralmente **B-tree**) que evita full scan: em vez de varrer todas as linhas, o SGBD navega a árvore em O(log n). Índices aceleram `WHERE`, `JOIN`, `ORDER BY`, `UNIQUE` e buscas por FK. Custo: espaço em disco e manutenção em INSERT/UPDATE/DELETE — cada índice extra torna escritas mais lentas.

### Tipos mais comuns

- **B-tree**: default; ideal para igualdade, ranges (`>`, `<`, `BETWEEN`) e prefixo de string (`LIKE 'abc%'`).
- **Composite (composto)**: índice em várias colunas. Vale a **regra do prefixo mais à esquerda (leftmost prefix)**: `(a, b, c)` atende `WHERE a=?`, `WHERE a=? AND b=?`, mas **não** `WHERE b=?` ou `WHERE c=?` sozinhos.
- **UNIQUE**: além de acelerar, impõe unicidade — chaves naturais entram aqui.
- **Covering index**: inclui todas as colunas que a query precisa → index-only scan, sem voltar à tabela.
- Especiais: `GIN`/`GiST` (Postgres: arrays, JSON, full-text), `FULLTEXT` (MySQL), `HASH` (alguns dialetos).

### Quando indexar

- FKs e colunas usadas em JOIN.
- Colunas filtradas com alta seletividade.
- `ORDER BY`/`GROUP BY` podem usar índice para evitar sort.
- **Não** indexe colunas de baixa cardinalidade (booleano, status com 2 valores) — full scan ganha.
- Remova índices órfãos (usados em nenhuma query).

### EXPLAIN e leitura de plano

Sempre valide o plano: `EXPLAIN (ANALYZE, BUFFERS)` (Postgres), `EXPLAIN ANALYZE` (MySQL), `SET STATISTICS IO ON` (SQL Server). Observe:

- **Seq Scan vs Index Scan**: se o filtro retorna mais de ~5–10% da tabela, o full scan costuma vencer.
- **Nested Loop vs Hash Join vs Merge Join**: nested loop com pequeno conjunto interno ok; tabelas grandes exigem hash/merge.
- Compare estimativas (`rows`, `cost`) com o real — estime sempre com `ANALYZE`/`VACUUM` (estatísticas desatualizadas geram planos ruins).

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM pedido
WHERE cliente_id = 7
  AND criado_em > now() - interval '30 days';
-- Índice ideal: (cliente_id, criado_em)
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[sql-joins-e-semântica-de-conjunto]]
- [[sql-modelagem-relacional-e-normalização]]
- [[sql-transações-acid-e-dialetos]]