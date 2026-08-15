---
tags: [argumento, casar, coleções, padrao, php, transformar]
aliases: [PHP: sistema de tipos, arrays e coerção]
date: 2026-08-15
---

# PHP: sistema de tipos, arrays e coerção

**Fonte:** php

### Tipagem

O PHP tem **tipagem dinâmica com coerção fraca** por padrão: `"5" + 1` resulta em `6` (inteiro). Adicionar `declare(strict_types=1);` no topo do arquivo faz a *chamada* de funções rejeitar coerção de tipos escalares — lança `TypeError` se o argumento não casar. Importante: `strict_types` vale para o arquivo que **faz a chamada** (caller), não o que define a função. Operadores aritméticos e de comparação continuam com coerção interna mesmo com strict_types.

### Arrays

O array do PHP é um **mapa ordenado** (tabela hash + sequência): serve como lista, dicionário e conjunto, preservando a ordem de inserção. Chaves numéricas e string coexistem — cuidado: `$a["0"]` e `$a[0]` referenciam o mesmo elemento. `array_merge` e `+` têm semânticas distintas: `+` mantém a chave da esquerda em conflitos; `array_merge` renumera chaves numéricas e sobrescreve as string. Funções de array (`array_filter`, `array_map`, `array_reduce`) são o jeito idiomático de transformar coleções.

### Comparação e armadilhas

- `==` (igualdade solta) compara com coerção: `0 == "abc"` é verdadeiro e `0 == ""` também — armadilha clássica.
- `===`/`!==` (identidade) compara tipo e valor. Prefira sempre que o valor vier de uma função que pode retornar `false`, `0` ou `""`.
- Valores falsy: `null`, `false`, `0`, `""`, `[]` e também `"0"` (string).
- `??` (null coalescing) cobre `null` e chave ausente; `?:` (elvis) cobre qualquer valor falsy. Use `$x['chave'] ?? $default` para evitar warnings de chave indefinida.
- Para entrada de usuário, prefira `filter_var`/`filter_input` (validação real) em vez de confiar em coerção.

```php
declare(strict_types=1);
function soma(int $a, int $b): int { return $a + $b; }
// soma("2", 3); // TypeError com strict_types no arquivo chamador
$v = $arr['x'] ?? 0;     // null coalescing
if ($valor === null) { /* identidade, não == */ }
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[php-modelo-de-execução-e-sapi]]
- [[php-psrs-autoload-e-composer]]