---
tags: [identity, integer, padrao, primary, sql, suporta]
aliases: [SQL: transações, ACID e dialetos]
date: 2026-08-17
---

# SQL: transações, ACID e dialetos

**Fonte:** sql

### ACID

Transação é uma unidade atômica de trabalho:
- **Atomicity**: ou tudo ou nada — falha no meio reverte tudo (ROLLBACK).
- **Consistency**: invariantes do banco preservadas (constraints, FKs, CHECKs).
- **Isolation**: transações concorrentes não se veem parcialmente.
- **Durability**: commit persistido mesmo em crash (WAL / write-ahead log).

### Controle

`BEGIN` → operações → `COMMIT` ou `ROLLBACK`. Detalhes por dialeto: no **Postgres** até DDL é transacional; no **MySQL**, DDL e DML têm auto-commit (só InnoDB suporta transações; MyISAM não). Para leitura com bloqueio: `SELECT ... FOR UPDATE`.

### Níveis de isolamento (SQL standard)

1. **READ UNCOMMITTED**: permite ler dados sujos (dirty reads).
2. **READ COMMITTED**: lê só o que já foi commitado — default de Postgres, Oracle e SQL Server.
3. **REPEATABLE READ**: a mesma consulta retorna o mesmo resultado na transação — default do MySQL/InnoDB.
4. **SERIALIZABLE**: máximo; execução como se fosse serial.

Fenômenos que cada nível evita: dirty read, non-repeatable read, phantom read.

### Implementação e concorrência

- **MVCC** (Postgres, InnoDB, SQLite em modo WAL): leituras não bloqueiam escritas — cada transação vê um snapshot.
- Locking pessimista vs concorrência otimista: para alta contenção de escrita, use `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?` (e verifique linhas afetadas).
- Deadlocks: acesse recursos em ordem consistente; o SGBD detecta e aborta uma transação — implemente retry.

### Diferenças de dialetos (resumo)

- **Auto-increment**: Postgres `BIGSERIAL`/`GENERATED ... AS IDENTITY`, MySQL `AUTO_INCREMENT`, SQLite `INTEGER PRIMARY KEY`, SQL Server `IDENTITY(1,1)`.
- **Limite de linhas**: `LIMIT/OFFSET` (Postgres, MySQL, SQLite) vs `OFFSET ... FETCH` ou `TOP` (SQL Server).
- **JSON**: `JSONB` (Postgres), `JSON` (MySQL/SQL Server).
- **Datas/funções**: `now()`/`CURRENT_DATE` (Postgres/MySQL) vs `GETDATE()` (SQL Server).
- **Concatenação**: `||` (Postgres/SQLite/SQL Server) vs `CONCAT()` (MySQL).
- **Case-insensitive**: `ILIKE` (Postgres) vs `LOWER(col) LIKE` (MySQL).

```sql
BEGIN;
UPDATE conta SET saldo = saldo - 100 WHERE id = 1;
UPDATE conta SET saldo = saldo + 100 WHERE id = 2;
COMMIT;  -- ou ROLLBACK em caso de erro
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[sql-joins-e-semântica-de-conjunto]]
- [[sql-modelagem-relacional-e-normalização]]
- [[sql-índices-e-estratégias-de-acesso]]