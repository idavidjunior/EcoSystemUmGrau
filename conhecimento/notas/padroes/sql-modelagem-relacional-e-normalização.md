---
tags: [automaticamente, cria, padrao, pelo, sql, time]
aliases: [SQL: modelagem relacional e normalização]
date: 2026-08-22
---

# SQL: modelagem relacional e normalização

**Fonte:** sql

### Fundamentos

O modelo relacional organiza dados em **tabelas** (relações), **colunas** (atributos) e **linhas** (tuplas). Toda tabela tem **Primary Key** (única e não nula, ex.: `id BIGSERIAL PRIMARY KEY`). **Foreign Keys** garantem integridade referencial: `cliente_id BIGINT REFERENCES cliente(id)`. A FK do lado filho **precisa de índice** na maioria dos dialetos — o SGBD normalmente não cria automaticamente.

### Normalização

Processo de eliminar redundância e anomalias (insert/update/delete):

- **1FN**: atributos atômicos, sem listas/repetição — itens repetidos viram tabela filha.
- **2FN**: nenhuma dependência parcial da chave composta (coluna que depende só de parte da PK).
- **3FN**: nenhuma dependência transitiva (coluna que depende de outra não-chave — ex.: `uf` derivado de `cidade` em `cliente`).

Objetivo: cada fato registrado **uma única vez** (single source of truth), atualizações sem inconsistência.

### Modelagem prática

1. Identifique entidades e relacionamentos (1:N, N:N, 1:1) a partir dos requisitos.
2. N:N vira **tabela associativa** com PK composta + FKs (`pedido_item`).
3. Adote um padrão de nomenclatura único (`snake_case`), singular ou plural, decidido pelo time.
4. Use `id` interno (surrogate key) e `UNIQUE` nas chaves naturais reais (CPF, email, matrícula).
5. **Denormalização** é aceitável quando justificada por leitura/performance (dashboards, agregações), mas documente: a consistência passa a ser responsabilidade da aplicação ou de triggers/eventos.

### Checklist de design

- Toda FK indexada.
- Tipos corretos: numéricos para números, `date`/`timestamptz` para datas — nunca string para data/número.
- `CHECK` para domínios simples (`CHECK (quantidade > 0)`).
- Evite colunas polivalentes (um atributo com duplo significado) e chaves compostas desnecessárias.

```sql
CREATE TABLE cliente (
  id BIGSERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL
);
CREATE TABLE pedido (
  id BIGSERIAL PRIMARY KEY,
  cliente_id BIGINT NOT NULL REFERENCES cliente(id),
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pedido_cliente ON pedido(cliente_id);
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[sql-joins-e-semântica-de-conjunto]]
- [[sql-transações-acid-e-dialetos]]
- [[sql-índices-e-estratégias-de-acesso]]