---
tags: [c, duplicado, estouro, free, padrao, size]
aliases: [C: comportamento indefinido e o modelo de memória]
date: 2026-08-23
---

# C: comportamento indefinido e o modelo de memória

**Fonte:** c

UB (undefined behavior) é a fonte central de bugs em C: o padrão não impõe NENHUM comportamento, e o compilador assume que ele nunca acontece — otimizações corretas para código válido podem produzir resultados absurdos quando o programa viola a premissa. Exemplos canônicos: signed integer overflow (`INT_MAX + 1`), dereferência de nulo/inválido, divisão por zero, shift por quantidade >= largura do tipo ou negativa, ler variável não inicializada, out-of-bounds, `free` duplicado, estouro de `size_t` em `p + n`.

O compilador pode até remover código inteiro baseado em UB: `if (x + 1 < x)` é otimizado para sempre-falso, removendo o ramo de overflow. Isso significa que 'funciona no meu teste' não valida nada — o mesmo código pode quebrar com `-O3`, outro compilador ou outra arquitetura.

Strict aliasing: acessar o mesmo objeto via tipos incompatíveis é UB. `-fstrict-aliasing` explora isso. Idiomas seguros: `memcpy` (que se compila para movimentos eficientes), `union`, ou ponteiros `char*`/`unsigned char*` (exceção permitida para leitura byte a byte de qualquer objeto). Sinalizar com `-fno-strict-aliasing` troca performance por compatibilidade.

Sequence points e ordenação: entre dois sequence points o mesmo objeto não pode ser modificado mais de uma vez nem lido e escrito sem regra (ex.: `i = i++` é UB; `a[i] = i++` também, pois a ordem de avaliação dos operandos é indeterminada). Comportamento indeterminado (indeterminate/unspecified) é menos grave mas ainda impede assumir ordem: argumentos de função podem ser avaliados em qualquer ordem.

Conclusão prática: compile sempre com `-Wall -Wextra -Werror -O2` e sanitizers no CI (`-fsanitize=undefined,address`), use tipos `uint8_t`/`int32_t` de `<stdint.h>` para aritmética previsível, e trate warnings de overflow/alias como bugs.
## Conexoes

- [[c-ponteiros-aritmética-e-gestão-manual-de-memória]]
- [[c-strings-c-buffers-e-funções-inseguras]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]