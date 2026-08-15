---
tags: [bancos-dados, falta, padrao, pré, seleção, sort]
aliases: [Bancos de dados: índices, planos de execução e custo de escr]
date: 2026-08-15
---

# Bancos de dados: índices, planos de execução e custo de escrita

**Fonte:** bancos-dados

Índice é uma estrutura auxiliar (B-tree na maioria dos SGBDs) que troca espaço e custo de escrita por velocidade de leitura. Sem ele, a busca é um full scan O(n); com B-tree, O(log n). Regra prática: indexe colunas usadas em WHERE, JOIN, ORDER BY e chaves estrangeiras — nunca indexe tudo.

**Custos reais do índice:** 1) escrita mais lenta: cada INSERT/UPDATE/DELETE mantém o índice; 2) espaço em disco e cache: índices competem com dados no buffer pool; 3) índices subutilizados viram overhead puro. Use `pg_stat_user_indexes`/`sys.dm_db_missing_index_details` para achar índices nunca usados e removê-los.

**Tipos:** único (integridade + otimização), composto (ordem de colunas importa — o índice serve prefixos de esquerda para direita; `(a,b,c)` atende `WHERE a`, `WHERE a,b` mas não `WHERE b`), parcial (PostgreSQL: `WHERE status='ativo'` — menor e mais rápido), funcional (índice em `lower(email)` para busca case-insensitive), covering (inclui colunas extras para evitar buscar a tabela).

**Como ler o plano de execução:** rode `EXPLAIN ANALYZE` (PostgreSQL) ou `SET STATISTICS PROFILE ON` (SQL Server). Leia de dentro para fora: a linha com maior `actual time`/`rows` é o gargalo. Procure por: `Seq Scan` (faltou índice?), `Index Scan` vs `Index Only Scan` (este é melhor — tudo veio do índice), `Nested Loop` com muitas execuções (estimativa ruim ou falta de índice no lado interno), `Hash Join` sem pré-seleção, `Sort` sobre muitas linhas (falta índice na ORDER BY). Compare `rows` estimadas vs `actual rows`: discrepância grande = estatísticas desatualizadas, rode `ANALYZE`.

**Trabalho diário:** ative auto_explain para capturar queries lentas em produção; congele a carga com `pg_stat_statements` e ataque as queries mais executadas, não as mais bonitas; valide todo índice novo sob carga de escrita real, não apenas em dev com 1000 linhas.
## Conexoes

- [[bancos-de-dados-orm-vs-sql-puro-migrations-e-schema-drift]]
- [[bancos-de-dados-sql-vs-nosql-e-o-trade-off-de-consistência]]
- [[bancos-de-dados-transações-acid-e-níveis-de-isolamento]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]