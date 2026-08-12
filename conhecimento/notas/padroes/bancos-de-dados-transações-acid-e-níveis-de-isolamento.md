---
tags: [bancos-dados, durabilidade, falha, interferem, padrao, sobrevivem]
aliases: [Bancos de dados: transações, ACID e níveis de isolamento]
date: 2026-08-12
---

# Bancos de dados: transações, ACID e níveis de isolamento

**Fonte:** bancos-dados

Transação agrupa operações com garantia atômica. ACID: Atomicidade (tudo ou nada), Consistência (estado válido segundo constraints), Isolamento (transações concorrentes não interferem), Durabilidade (dados sobrevivem a falha). O ponto que separa profissionais: isolamento é um espectro, e cada nível previne fenômenos diferentes a custo de concorrência.

**Fenômenos de concorrência:** 1) Dirty read — ler dado não commitado (impossível acima de READ UNCOMMITTED); 2) Non-repeatable read — ler a mesma linha duas vezes e ver valores diferentes (outra transação fez UPDATE); 3) Phantom read — o mesmo WHERE retorna linhas diferentes (INSERT/DELETE de outra transação); 4) Write skew e lost update — versões sutis de inconsistência em MVCC.

**Níveis de isolamento (SQL standard):** READ UNCOMMITTED (sem proteção, raramente usado), READ COMMITTED (linhas lidas são versões commitadas; evita dirty read, mas permite non-repeatable e phantom), REPEATABLE READ (snapshot consistente; evita non-repeatable, ainda permite phantom em alguns SGBDs), SERIALIZABLE (executa como se serial; máximo custo).

**Por que READ COMMITTED é o padrão (PostgreSQL, Oracle, SQL Server, MySQL):** é o melhor equilíbrio produtividade/consistência. Em MVCC (PostgreSQL), cada query vê um snapshot: leituras nunca bloqueiam escritas e escritas não bloqueiam leituras — o custo de concorrência cai drasticamente. REPEATABLE READ seria o custo de mais bloqueios/locks por caso de uso raro. Regra: comece no padrão, promova o nível somente para transações que provem necessidade (ex.: relatórios que exigem snapshot estável com REPEATABLE READ, ou lógica financeira que exige SERIALIZABLE + retry em conflito).

**Na prática:** use transações curtas (manter transação aberta segura locks/snapshots e bloat no MVCC); não rode I/O de rede ou API dentro de transação; com SERIALIZABLE, implemente retry de `40001` (serialization failure) com backoff exponencial; verifique o isolamento por SGBD: MySQL InnoDB REPEATABLE READ não é igual ao do PostgreSQL; conheça `SELECT ... FOR UPDATE`/`FOR SHARE` (locking reads) e `SKIP LOCKED` para filas de jobs.
## Conexoes

- [[bancos-de-dados-orm-vs-sql-puro-migrations-e-schema-drift]]
- [[bancos-de-dados-sql-vs-nosql-e-o-trade-off-de-consistência]]
- [[bancos-de-dados-índices-planos-de-execução-e-custo-de-escrit]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]