---
tags: [alinhamento, alocação, c, importa, layout, padrao]
aliases: [C: ponteiros, aritmética e gestão manual de memória]
date: 2026-08-22
---

# C: ponteiros, aritmética e gestão manual de memória

**Fonte:** c

Em C, toda memória é gerenciada manualmente: stack, memória estática e heap. `malloc`/`calloc`/`realloc` alocam no heap e retornam um ponteiro opaco; `free` devolve o bloco. Regras de ouro: sempre checar o retorno de `malloc` (retorna `NULL` em falha), sempre `free` exatamente uma vez por alocação, e nunca usar memória após `free` (use-after-free). Padrão idiomático:

```c
T *p = malloc(sizeof(*p) * n);  // sizeof(*p), não sizeof(T), evita erro se T mudar
if (!p) { /* trata OOM */ }
/* usa p... */
free(p);
```

Aritmética de ponteiros: `p + i` avança `i * sizeof(*p)` bytes — nunca some offset em bytes manualmente. `p[i]` é açúcar para `*(p+i)`. `p - q` entre dois ponteiros do MESMO array é válido (ptrdiff_t); entre objetos distintos é UB. Ponha `const` no tipo certo: `const int *p` (dado constante) vs `int *const p` (ponteiro constante).

Armadilhas fatais: buffer overflow (escrever além de `p[n-1]`) é UB e vetor clássico de exploitação; dereferência de ponteiro nulo é UB; ponteiro pendurado (dangling) após escopo da variável local; leaks por não liberar em todos os caminhos de retorno. `realloc` pode mover o bloco — aponte o ponteiro original até validar o retorno (`p = realloc(p, ...)` sem armazenar em temporário perde o bloco se falhar).

Quando usar: sistemas embarcados, kernels, drivers, código com restrição de runtime ou onde o controle fino de layout/alinhamento importa. Prefira arrays VLA só quando o tamanho é pequeno (no stack); arrays grandes e dinâmicos vão para o heap. Use ferramentas: valgrind, ASan/UBSan (`-fsanitize=address,undefined`), `-Wall -Wextra -Werror`.
## Conexoes

- [[c-comportamento-indefinido-e-o-modelo-de-memória]]
- [[c-strings-c-buffers-e-funções-inseguras]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]