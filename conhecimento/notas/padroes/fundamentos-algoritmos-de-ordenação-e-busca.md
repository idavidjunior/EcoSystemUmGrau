---
tags: [fixo, fundamentos, padrao, partes, pequenas, tamanho]
aliases: [Fundamentos: algoritmos de ordenação e busca]
date: 2026-08-12
---

# Fundamentos: algoritmos de ordenação e busca

**Fonte:** fundamentos

Ordenação e busca são os blocos de construção de quase todo sistema que processa dados. Entender a complexidade e a estabilidade de cada algoritmo permite escolher a ferramenta certa.

### Ordenação por comparação
- **Bubble / Insertion / Selection**: `O(n^2)` no pior caso. Insertion sort é eficiente para vetores pequenos ou quase ordenados (`O(n)` no melhor caso), e por isso é usado como base do Timsort para partes pequenas.
- **Merge sort**: `O(n log n)` garantido, estável, mas usa `O(n)` de espaço extra.
- **Quick sort**: `O(n log n)` médio, `O(n^2)` pior caso (pivô ruim). In-place, mas não estável por padrão; domina na prática (Introsort combina quick+heap+insertion).
- **Heap sort**: `O(n log n)` garantido, in-place, mas instável e com pior localidade de cache.
- **Timsort**: ordenação adaptativa usada por Python e Java; explora sequências já ordenadas (runs).

Limite teórico: ordenação por comparação não pode ser mais rápida que `O(n log n)` (árvore de decisão). Ordenações não comparativas (counting/radix sort) atingem `O(n)` para dados com range limitado (inteiros, strings de tamanho fixo).

### Busca
- **Linear**: `O(n)`, útil para dados pequenos ou desordenados, ou quando o item provável está no início.
- **Binária**: `O(log n)` em vetor ordenado; essencial para testes de propriedade e busca em intervalos.
```
busca_binaria(v, alvo):
  lo, hi = 0, len(v)-1
  enquanto lo <= hi:
    mid = lo + (hi - lo)//2   # evita overflow
    se v[mid] == alvo: return mid
    se v[mid] < alvo: lo = mid+1
    else: hi = mid-1
  return -1
```
- **Busca em árvores (BST/B-tree)**: `O(log n)` em árvores balanceadas.
- **Hash**: `O(1)` médio para lookup, sem ordem.
- **Interpolation search**: `O(log log n)` médio para dados uniformemente distribuídos.

### Estabilidade
Um algoritmo é **estável** quando elementos iguais preservam a ordem original — requisito para ordenar por múltiplos critérios (ex.: por data e depois por prioridade). Merge e insertion são estáveis; quicksort e heapsort, não.

**Decisão prática**: use a ordenação nativa da linguagem (normalmente Introsort/Timsort) como padrão; implemente mergesort quando precisar de estabilidade com garantia de `O(n log n)`, e radix/counting sort quando o domínio das chaves for pequeno e inteiro.
## Conexoes

- [[cluster-hub-programacao]]
- [[fundamentos-análise-de-complexidade-assintótica-big-o]]
- [[fundamentos-estruturas-de-dados-essenciais-e-quando-usar-cad]]
- [[fundamentos-programação-dinâmica-e-algoritmos-greedy]]
- [[fundamentos-recursão-e-técnicas-de-divisão-e-conquista]]
- [[padrao-hub-padroes]]