---
tags: [empty, idiomática, javascript, padrao, symbol, truthy]
aliases: [JavaScript: tipos, coerção e igualdade]
date: 2026-08-15
---

# JavaScript: tipos, coerção e igualdade

**Fonte:** javascript

JavaScript tem 7 tipos primitivos (string, number, bigint, boolean, undefined, null, symbol) e object. `typeof null` retorna 'object' — bug histórico consagrado; use `x === null` para testar. `NaN` é o único valor não igual a si mesmo (`NaN !== NaN`), teste com `Number.isNaN` (não o global `isNaN` que coerção). `typeof NaN === 'number'`. Em JS, `0/0` é `NaN`, `1/0` é `Infinity`.

Coerção implícita é a fonte de bugs clássicos: `'2' + 2` → `'22'` (o `+` com string concatena), mas `'2' - 1` → `1` (os demais operadores coerção numérica). `[] + []` → `''`, `[] + {}` → '[object Object]'. Regras: valores falsy são `false, 0, '', null, undefined, NaN` — note que `[]` e `{}` são TRUTHY (truthy/empty).

Igualdade:
- `==` compara após coerção (loose); `===` compara tipo e valor (strict) — use `===` sempre, exceto `x == null` que é abreviação idiomática para `x === null || x === undefined`.
- `null == undefined` é `true`; `null === undefined` é `false`.
- Objetos se comparam por referência: `{} == {}` é `false`.

Comparações ordenadas: `'10' < '9'` é `true` (string comparada lexicograficamente); para ordenar números use `(a, b) => a - b`. `[1,2] < '3'` é `true` porque o array vira '1,2' e compara lexicograficamente. `String.prototype.localeCompare` para ordem internacional.

Armadilhas:
- `parseInt('08')` em engines legados vira 0 (prefixo octal) — sempre passe base: `parseInt('08', 10)`.
- `Number('')` é `0`, `Number(null)` é `0`, `Number(undefined)` é `NaN` — casos clássicos de bugs de dados.
- `isFinite('123')` faz coerção e retorna `true`; `Number.isFinite` é estrito.

Melhores práticas: declare tipos claramente com TypeScript ou JSDoc; valide entrada na borda (parse com `Number(...)`, check `isNaN`); use `===` e evite coerção implícita; para valores opcionais, `x ?? fallback` (nullish coalescing) em vez de `x || fallback` que também cobre falsy como `''` e `0`.
## Conexoes

- [[cluster-hub-programacao]]
- [[javascript-assincronismo-event-loop-promises-e-asyncawait]]
- [[javascript-closures-escopo-e-hoisting]]
- [[javascript-this-prototypes-e-herança]]
- [[padrao-hub-padroes]]