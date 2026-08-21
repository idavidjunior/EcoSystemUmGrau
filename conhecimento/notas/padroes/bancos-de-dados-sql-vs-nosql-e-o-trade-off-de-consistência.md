---
tags: [acessos, bancos-dados, obrigatória, padrao, relatórios, transacional]
aliases: [Bancos de dados: SQL vs NoSQL e o trade-off de consistência]
date: 2026-08-21
---

# Bancos de dados: SQL vs NoSQL e o trade-off de consistência

**Fonte:** bancos-dados

A escolha entre relacional e NoSQL não é estética: é um trade-off de consistência, disponibilidade e tolerância a partição guiado pelo teorema CAP. CAP afirma que em uma rede com partições (situação inevitável em sistemas distribuídos) você precisa escolher entre consistência forte (C) ou disponibilidade (A). O ponto chave: quando não há partição, tudo é consistente e disponível; a decisão só aparece durante falhas de rede. Por isso o acrônimo correto seria CA/P.

**Quando usar relacional (PostgreSQL, MySQL):** dados com relações ricas e integridade forte (finanças, pedidos, usuários), queries ad-hoc e relatórios, consistência transacional obrigatória. Use constraints, FKs e transações para garantir invariantes.

**Quando usar NoSQL:** escala horizontal massiva de escrita, esquemas flexíveis ou polimórficos, dados de leitura em alta velocidade com acessos por chave. Categorias: document (MongoDB) para agregados com query por conteúdo; key-value (Redis) para cache e sessões; wide-column (Cassandra) para escrita massiva e particionamento por chave; graph (Neo4j) para relacionamentos profundos.

**Padrões de decisão práticos:** 1) Modele o agregado: se as queries sempre acessam uma raiz com filhos, document store simplifica; se há joins frequentes entre entidades independentes, relacional. 2) Não migre por hype: relacional escala com réplicas de leitura, sharding e caching — a maioria dos sistemas morre de query ruim, não de escala. 3) Consistência eventual exige tolerância de leituras obsoletas: desenhe a UI e os contratos para aceitar isso (temporal, retry, read-your-writes com session affinity). 4) Híbridos são comuns e corretos: relacional como fonte da verdade + NoSQL/cache para leitura. 5) Meça: latência p95, throughput e consistência exigida pelo domínio antes de escolher.

Erro clássico: escolher NoSQL para fugir de migrations e acabar com schema drift e consistência manual pior que o problema original.
## Conexoes

- [[bancos-de-dados-orm-vs-sql-puro-migrations-e-schema-drift]]
- [[bancos-de-dados-transações-acid-e-níveis-de-isolamento]]
- [[bancos-de-dados-índices-planos-de-execução-e-custo-de-escrit]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]