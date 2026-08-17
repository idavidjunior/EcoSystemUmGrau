---
tags: [autocomplete, domina, fundamentos, mapas, padrao, sequencial]
aliases: [Fundamentos: estruturas de dados essenciais e quando usar ca]
date: 2026-08-17
---

# Fundamentos: estruturas de dados essenciais e quando usar cada

**Fonte:** fundamentos

Escolher a estrutura certa é, na prática, escolher a complexidade das operações. As operações típicas são: leitura (`get`), busca (`contains`), inserção, remoção e iteração.

### Vetores (arrays / ArrayList)
- Memória contígua; acesso indexado `O(1)`, iteração rápida, ótima localidade de cache.
- Inserção/remoção no meio é `O(n)` (desloca elementos).
- **Use quando**: precisa de acesso por índice, o tamanho é razoavelmente conhecido, ou o acesso sequencial domina. **Evite**: deleções frequentes no meio.

### Listas ligadas (linked lists)
- Inserção/remoção na ponta `O(1)`, busca é `O(n)` (não há salto direto).
- Pobre localidade de cache; raramente a melhor escolha em linguagens modernas.
- **Use quando**: precisa de fila/deque com operações constantes nas extremidades (ou use `deque`).

### Tabelas hash (HashMap / Dict / Map)
- `put`, `get`, `contains` em `O(1)` médio; iteração é `O(n)` mas sem ordem garantida.
- Chaves precisam de hash consistente e igualdade bem definida.
- **Use quando**: lookup por chave, cache, deduplicação, contagem de frequência. **Evite**: quando precisar de ordem ou range queries (prefira árvore balanceada).

### Árvores (balanceadas: AVL, Red-Black, B-tree)
- Busca, inserção e remoção em `O(log n)`; iteram em ordem quando necessário.
- **Use quando**: dados ordenados com lookups de intervalo, índices de banco, autocomplete, mapas ordenados.

### Grafos
- Estrutura de vértices + arestas. Representações: lista de adjacência (esparsa, `O(V+E)` espaço) e matriz de adjacência (densa, `O(V^2)`).
- **Use quando**: redes, dependências, caminhos, relacionamentos, topologia de sistemas.

### Heaps (filas de prioridade)
- Extração do mínimo/máximo `O(log n)`, inserção `O(log n)`.
- **Use quando**: top-k, scheduling por prioridade, algoritmo de Dijkstra, merge de streams ordenados.

### Regra de ouro
Se a operação dominante for **lookup por chave** → hash. Se for **ordem e intervalo** → árvore. Se for **acesso por índice** → vetor. Se for **prioridade** → heap. Se houver **relação entre entidades** → grafo. Antes de implementar uma estrutura customizada, meça: a estrutura da stdlib quase sempre é mais testada e mais rápida.
## Conexoes

- [[cluster-hub-programacao]]
- [[fundamentos-algoritmos-de-ordenação-e-busca]]
- [[fundamentos-análise-de-complexidade-assintótica-big-o]]
- [[fundamentos-programação-dinâmica-e-algoritmos-greedy]]
- [[fundamentos-recursão-e-técnicas-de-divisão-e-conquista]]
- [[padrao-hub-padroes]]