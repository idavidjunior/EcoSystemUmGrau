---
tags: [concurrent, golang, heap, padrao, stack, writes]
aliases: [Go: slices, maps e ponteiros]
date: 2026-08-21
---

# Go: slices, maps e ponteiros

**Fonte:** golang

# slices, maps e ponteiros

Slice é um *descritor* `{ptr, len, cap}` para um array subjacente. Copiar um slice copia o descritor — os dados continuam compartilhados. `append` escreve no array se `len < cap`; se estourar `cap`, aloca um novo array e copia.

## Idioms
- `make([]T, len, cap)` para slices com capacidade inicial; `append(s, v...)` para juntar slices.
- `copy(dst, src)` copia até o menor `len`; use quando precisar isolar os dados.
- **Nil slice** (`var s []T`) é válido: `len == 0`, aceita `append`, e serializa como `null` em JSON (diferente de `make([]T,0)` que vira `[]`). Use nil para «sem dados».
- Fatiar (`s[lo:hi]`) cria uma janela sobre o mesmo array — devolver `s[2:]` de um buffer grande retém o array inteiro (leak de memória); copie quando necessário.
- `range` copia cada elemento: mutar o item não altera o slice; acesse por índice para modificar.

## Maps
- São *reference types*; iteração é **não ordenada** (aleatória por design).
- Chave ausente retorna o zero value; use comma-ok: `v, ok := m[k]`.
- `delete(m, k)` remove; map nil é «vazio» para leitura, mas **escrever em map nil panica**.
- **Concorrência**: ler e escrever o mesmo map sem lock é data race e pode panicar («concurrent map writes»). Use `sync.RWMutex` ou `sync.Map` (leitura pesada).

## Ponteiros
- `&x` e `*p`; retornar ponteiro para variável local é seguro — o escape analysis decide stack/heap.

```go
s := make([]int, 0, 8) // evita realocações
s = append(s, 42)      // pode reescrever o descritor
if v, ok := m["x"]; ok { use(v) }
```

Regra: passar slices é barato, mas lembre do array compartilhado e proteja maps concorrentes.
## Conexoes

- [[cluster-hub-programacao]]
- [[go-context-cancelamento-e-timeouts]]
- [[go-goroutines-canais-e-csp]]
- [[go-interfaces-implícitas-method-set-e-composição]]
- [[padrao-hub-padroes]]