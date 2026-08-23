---
tags: [except, intersect, interseção, minus, padrao, sql]
aliases: [SQL: joins e semântica de conjunto]
date: 2026-08-23
---

# SQL: joins e semântica de conjunto

**Fonte:** sql

### Tipos de JOIN

- **INNER JOIN**: apenas linhas que casam nos dois lados.
- **LEFT JOIN**: todas as linhas da esquerda + casamentos à direita; sem match, colunas da direita ficam `NULL`.
- **RIGHT JOIN**: espelho do LEFT.
- **FULL OUTER JOIN**: união dos dois; qualquer lado pode ficar `NULL`. Postgres e SQL Server têm nativamente; no MySQL, simule com `UNION` de LEFT+RIGHT.
- **CROSS JOIN**: produto cartesiano — quase sempre erro, exceto em geradores/intencional.

### Armadilhas clássicas

- **Multiplicação de linhas**: JOIN 1:N multiplica o lado "um". `cliente → pedido → item` explode se você pular um elo. Confira totais: `COUNT(*)` da query vs `COUNT(DISTINCT pedido.id)`.
- **Filtro no LEFT JOIN**: `WHERE pedido.total > 100` converte o LEFT em INNER, pois elimina os `NULL` do lado direito. Para manter o LEFT, coloque o filtro na cláusula `ON` (`LEFT JOIN pedido p ON ... AND p.total > 100`).
- **NULL e igualdade**: `NULL = NULL` é `NULL` (desconhecido), nunca verdadeiro — não casa em `ON a.id = b.id`. Para opcional, use LEFT JOIN e trate `NULL`.
- **Self-join**: hierarquias em uma tabela (`JOIN funcionario f2 ON f2.gerente_id = f1.id`).

### Operadores de conjunto

`UNION` (remove duplicatas), `UNION ALL` (mais rápido, mantém duplicatas), `INTERSECT` (interseção) e `EXCEPT`/`MINUS` (diferença). Exigem **mesmo número e tipos compatíveis** de colunas. Diferente de JOIN, operam linha a linha, não coluna a coluna.

### WHERE vs ON

`ON` define a condição de junção; `WHERE` filtra o resultado do produto da junção. Em INNER JOIN são equivalentes; em LEFT/RIGHT/FULL a diferença é crítica (veja acima).

```sql
SELECT c.nome, COUNT(p.id) AS pedidos
FROM cliente c
LEFT JOIN pedido p ON p.cliente_id = c.id
WHERE c.ativo = true
GROUP BY c.id;

-- Confirme multiplicação:
SELECT COUNT(*) FROM pedido;              -- 100
SELECT COUNT(*) FROM pedido p
JOIN item i ON i.pedido_id = p.id;        -- 340 (pedidos com 3+ itens)
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[sql-modelagem-relacional-e-normalização]]
- [[sql-transações-acid-e-dialetos]]
- [[sql-índices-e-estratégias-de-acesso]]