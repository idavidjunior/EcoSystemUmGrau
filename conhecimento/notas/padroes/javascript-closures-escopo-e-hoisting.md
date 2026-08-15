---
tags: [declaração, javascript, lança, padrao, referenceerror, stack]
aliases: [JavaScript: closures, escopo e hoisting]
date: 2026-08-15
---

# JavaScript: closures, escopo e hoisting

**Fonte:** javascript

JavaScript usa escopo por função (antes) e por bloco (a partir do ES6 com `let`/`const`). Closure é a combinação de uma função com o ambiente léxico onde foi criada — a função 'lembra' as variáveis daquele escopo mesmo depois do escopo sair da stack. O padrão de factory/função retornada que captura estado é base para módulos, currying e memoization.

Hoisting: declarações `var` e declarações de `function` são movidas ao topo do escopo na fase de compilação. `var` sobe declarada mas com valor `undefined` (undefined assignment antes da linha); funções sobem completas e são invocáveis antes da definição. `let`/`const` também sofrem hoisting, mas ficam na Temporal Dead Zone (TDZ) — acessar antes da declaração lança `ReferenceError`.

Armadilhas clássicas:
- Loop com `var`: `for (var i = 0; ...)` captura a MESMA variável — todos os callbacks veem o valor final. Com `let`, cada iteração ganha seu binding. Para código antigo, use IIFE para fixar o valor.
- `function` dentro de bloco em strict mode é compatível com ES6; fora dele o comportamento é inconsistente entre engines.
- Closures em módulos: preferir `const` para nunca reatribuir acidentalmente o binding capturado.

Melhores práticas: sempre `const` por padrão, `let` quando precisar reatribuir, `var` apenas em legacy. Declare no topo de blocos para evitar TDZ confusa. Evite criar closures dentro de loops sem necessidade (custo de memória). Use closures para encapsulamento real (module pattern):
```javascript
const counter = (() => {
  let n = 0;
  return { inc: () => ++n, val: () => n };
})();
```
`this` em arrow functions é léxico (herda do escopo externo), não dinâmico — ideal para callbacks. Funções regulares têm `this` dinâmico (quem chamou). Entender escopo léxico + `this` evita os erros mais comuns em React e eventos do DOM.
## Conexoes

- [[cluster-hub-programacao]]
- [[javascript-assincronismo-event-loop-promises-e-asyncawait]]
- [[javascript-this-prototypes-e-herança]]
- [[javascript-tipos-coerção-e-igualdade]]
- [[padrao-hub-padroes]]