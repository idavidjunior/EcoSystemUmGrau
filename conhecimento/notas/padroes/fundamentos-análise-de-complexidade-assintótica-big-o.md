---
tags: [fundamentos, ignorando, menor, ordem, padrao, termos]
aliases: [Fundamentos: análise de complexidade assintótica (Big-O)]
date: 2026-08-21
---

# Fundamentos: análise de complexidade assintótica (Big-O)

**Fonte:** fundamentos

Big-O descreve como o tempo (ou memória) cresce em função do tamanho da entrada `n`, ignorando constantes e termos de menor ordem. Serve para comparar algoritmos em escala, não para medir velocidade absoluta em dados pequenos.

### Regras básicas
- Descartar constantes: `3n` vira `O(n)`.
- Somar custos em sequência: `O(f) + O(g) = O(max(f, g))`.
- Multiplicar em laços aninhados: `O(f) * O(g)`.
- Um loop que divide o tamanho pela metade é logarítmico: `O(log n)`.

### Classes comuns (pior para melhor)
```
O(1)      acesso direto a vetor, push/pop em pilha
O(log n)  busca binária, operações em árvore balanceada
O(n)      varredura linear, busca em lista não ordenada
O(n log n) ordenação por merge/heap sort
O(n^2)    laços aninhados (insertion sort, bubble sort)
O(2^n)    backtracking exponencial
O(n!)     permutações
```

### Análise de complexidades
- **Melhor caso**: entrada ideal (ex.: busca com primeiro elemento já encontrado).
- **Caso médio**: comportamento esperado sob distribuição típica (ex.: quick sort `O(n log n)`).
- **Pior caso**: sempre o mais importante para garantias; quick sort com pivô ruim é `O(n^2)`.

### Complexidade de espaço
Conta memória extra usada pelo algoritmo, além da entrada. Merge sort usa `O(n)` de espaço extra; quicksort in-place usa `O(log n)` para a pilha de recursão.

### Armadilhas comuns
- Confundir `amortizado` (ex.: append em ArrayList/vector, `O(1)` amortizado) com `garantido`.
- Assumir `O(n log n)` sem provar: um `for` dentro de outro `for` que divide a entrada ainda é `O(n log n)` — verifique se o tamanho do loop interno realmente encolhe.
- Medir só tempo e ignorar espaço (relevante em sistemas embarcados ou com limites de memória).

**Checklist prático**: identifique o loop dominante → conte as iterações → some as funções chamadas → expresse em `n` → escolha a classe dominante. Para entrevistas e revisão de algoritmos, sempre declare a complexidade de tempo e espaço antes de implementar.
## Conexoes

- [[cluster-hub-programacao]]
- [[fundamentos-algoritmos-de-ordenação-e-busca]]
- [[fundamentos-estruturas-de-dados-essenciais-e-quando-usar-cad]]
- [[fundamentos-programação-dinâmica-e-algoritmos-greedy]]
- [[fundamentos-recursão-e-técnicas-de-divisão-e-conquista]]
- [[padrao-hub-padroes]]