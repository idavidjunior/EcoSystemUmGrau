---
tags: [direção, fundamentos, linguagem, padrao, suporta, verifique]
aliases: [Fundamentos: recursão e técnicas de divisão-e-conquista]
date: 2026-08-14
---

# Fundamentos: recursão e técnicas de divisão-e-conquista

**Fonte:** fundamentos

Recursão resolve um problema definindo-o em termos de uma versão menor de si mesmo. Todo algoritmo recursivo tem: **caso base** (condição de parada) e **passo recursivo** (reduz o tamanho do problema em direção ao caso base).

### Anatomia
```
def fatorial(n):
    if n <= 1:          # caso base
        return 1
    return n * fatorial(n-1)   # passo recursivo
```
A pilha de chamadas guarda o estado de cada nível; recursão profunda pode estourar o stack (`StackOverflowError`, `RecursionError`). Como regra, limite prático: milhares de frames em linguagens típicas.

### Divisão-e-conquista (divide and conquer)
Estrutura em três fases: **dividir** o problema em subproblemas independentes → **conquistar** resolvendo cada subproblema recursivamente → **combinar** as soluções.
- Merge sort: divide, ordena cada metade, intercala.
- Quick sort: particiona, ordena cada lado.
- Busca binária: descarta metade do espaço a cada passo.
- Multiplicação de matrizes (Strassen), pares mais próximos, transformada rápida de Fourier (FFT).

Complexidade via **Teorema Mestre**: para `T(n) = a·T(n/b) + O(n^d)`:
- se `d > log_b(a)` → `O(n^d)` (a divisão não ajuda muito);
- se `d = log_b(a)` → `O(n^d · log n)` (merge sort: `a=2, b=2, d=1` → `O(n log n)`);
- se `d < log_b(a)` → `O(n^(log_b(a)))` (recursão domina).

### Técnicas aliadas
- **Backtracking**: explora todas as escolhas com poda (N-queens, Sudoku, subconjuntos). Exponencial no pior caso.
- **Memoização**: cache de resultados de subproblemas para eliminar recomputação (vira programação dinâmica top-down).
- **Tail recursion**: quando a chamada recursiva é a última operação, compiladores otimizam para loop (evita crescimento da pilha) — verifique se a linguagem suporta.

### Armadilhas
- Esquecer caso base → recursão infinita.
- Não reduzir o tamanho do problema → nunca termina.
- Recomputar o mesmo subproblema sem memoização → exponencial desnecessário (ex.: Fibonacci ingênuo é `O(2^n)`).

**Checklist**: 1) defina o caso base menor possível; 2) garanta que cada chamada reduz a entrada; 3) identifique subproblemas repetidos e memorize; 4) considere reescrever como loop se a pilha for limitada.
## Conexoes

- [[cluster-hub-programacao]]
- [[fundamentos-algoritmos-de-ordenação-e-busca]]
- [[fundamentos-análise-de-complexidade-assintótica-big-o]]
- [[fundamentos-estruturas-de-dados-essenciais-e-quando-usar-cad]]
- [[fundamentos-programação-dinâmica-e-algoritmos-greedy]]
- [[padrao-hub-padroes]]