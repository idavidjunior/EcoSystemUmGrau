---
tags: [deadline, fundamentos, lucro, maximização, padrao, várias]
aliases: [Fundamentos: programação dinâmica e algoritmos greedy]
date: 2026-08-17
---

# Fundamentos: programação dinâmica e algoritmos greedy

**Fonte:** fundamentos

Programação dinâmica (PD) resolve problemas com **subestrutura ótima** (solução ótima contém soluções ótimas dos subproblemas) e **subproblemas sobrepostos** (o mesmo subproblema aparece várias vezes). A ideia é resolver cada subproblema uma única vez e guardar o resultado.

### Passos para modelar PD
1. **Defina o estado**: a menor unidade que descreve o subproblema (ex.: `dp[i]` = custo mínimo até a posição `i`).
2. **Equação de recorrência**: como `dp[i]` depende de estados anteriores.
3. **Caso base**: valores iniciais conhecidos.
4. **Ordem de preenchimento**: bottom-up (iterativo) ou top-down com memoização (recursivo + cache).
5. **Reconstrução da solução**: guarde as decisões para recuperar o caminho, não só o valor ótimo.

Exemplo clássico (knapsack 0/1), bottom-up:
```
# itens com (peso, valor); dp[c] = maior valor com capacidade c
for (w, v) in itens:
    for c in range(capacidade, w-1, -1):
        dp[c] = max(dp[c], dp[c-w] + v)  # de trás pra frente evita reuso
```

### Comum em problemas PD
- Longest common subsequence (LCS), edit distance, caminhos mínimos em grid, Fibonacci, coin change, longest increasing subsequence.
- Complexidade típica: `O(número de estados × custo de transição)`.

### Greedy
Escolhe, a cada passo, a opção **localmente ótima** esperando atingir o ótimo global. Só é correta quando a escolha local é sempre segura — precisa de **prova** (argumento de troca ou greedy choice property), não de intuição.

**Funciona**: troco com moedas canônicas, árvore geradora mínima (Kruskal/Prim), Huffman coding, Dijkstra (pesos não negativos), agendamento por deadline com maximização de lucro.

**Não funciona**: knapsack 0/1 (o fracionário sim), troco com moedas arbitrárias, Dijkstra com pesos negativos.

### PD × Greedy × força bruta
- **Greedy**: 1 decisão, nunca volta atrás. Mais rápido (`O(n log n)` ou menos), mas exige prova de corretude.
- **PD**: explora todas as combinações relevantes com cache. Mais caro, porém sempre correto quando as propriedades valem.
- **Força bruta**: sem overlap, só para entradas pequenas.

**Regra prática**: tente greedy primeiro e prove; se houver contraexemplo, parta para PD. Para PD, comece top-down com memoização (mais fácil de raciocinar) e converta para bottom-up quando quiser reduzir overhead de recursão.
## Conexoes

- [[cluster-hub-programacao]]
- [[fundamentos-algoritmos-de-ordenação-e-busca]]
- [[fundamentos-análise-de-complexidade-assintótica-big-o]]
- [[fundamentos-estruturas-de-dados-essenciais-e-quando-usar-cad]]
- [[fundamentos-recursão-e-técnicas-de-divisão-e-conquista]]
- [[padrao-hub-padroes]]