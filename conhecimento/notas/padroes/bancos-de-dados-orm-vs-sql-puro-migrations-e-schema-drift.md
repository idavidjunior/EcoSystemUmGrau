---
tags: [bancos-dados, boilerplate, models, padrao, portabilidade, sgbds]
aliases: [Bancos de dados: ORM vs SQL puro, migrations e schema drift]
date: 2026-08-17
---

# Bancos de dados: ORM vs SQL puro, migrations e schema drift

**Fonte:** bancos-dados

ORM (SQLAlchemy, Prisma, ActiveRecord, Hibernate) mapeia objetos para tabelas e gera SQL. SQL puro é escrito na mão. Não é guerra: é seleção de ferramenta por contexto.

**Quando ORM vence:** desenvolvimento rápido, CRUD padrão, proteção contra injection via query builder, migrations unificadas, menos código boilerplate, portabilidade entre SGBDs. **Quando ORM perde:** queries complexas (joins profundos, window functions, CTEs recursivas) geram SQL ineficiente; N+1 (lazy loading disparando uma query por registro); controle fino de locks, hints e planos; o custo de abstração esconde custos reais — a query no log não parece a que você escreveu.

**Práticas que evitam o ORM como vazamento de performance:** 1) desligue lazy loading; use eager loading explícito (`selectinload`, `joins`); 2) para relatórios e agregados pesados, use query builders nativos ou SQL puro mapeado manualmente (read models); 3) sempre cap o tamanho: batch inserts, `page size`, sem N+1; 4) audite o SQL gerado em staging com logs de slow query; 5) conheça o plano de execução da query gerada, não só o resultado.

**Migrations:** código versionado que evolui o schema (Alembic, Flyway, Prisma Migrate, Django Migrations). Regras: migrations são aplicadas apenas para frente e imutáveis depois do merge — nunca edite uma migration publicada, crie uma nova; rode em CI e valide contra um banco limpo; migrações destrutivas (DROP, ALTER com rebuild) exigem estratégia: add-and-migrate em dois deploys (expand/contract pattern); use `IF EXISTS`/`IF NOT EXISTS`; versionamento explícito (Flyway) ou por hash (Prisma).

**Schema drift:** diferença entre schema no banco real e o versionado. Causas: alguém alterou o banco à mão, migration nunca aplicada, devs com branches divergentes. Detecção: `pg_dump --schema-only` comparado via diff; Flyway validate; `gh-ost`/`pt-online-schema-change` para ALTER em produção sem downtime. Meta: banco de produção == migrations aplicadas do zero em um pipeline reproduzível.
## Conexoes

- [[bancos-de-dados-sql-vs-nosql-e-o-trade-off-de-consistência]]
- [[bancos-de-dados-transações-acid-e-níveis-de-isolamento]]
- [[bancos-de-dados-índices-planos-de-execução-e-custo-de-escrit]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]