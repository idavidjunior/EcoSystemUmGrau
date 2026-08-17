---
tags: [chama, construtor, javascript, padrao, pai, super]
aliases: [JavaScript: this, prototypes e herança]
date: 2026-08-17
---

# JavaScript: this, prototypes e herança

**Fonte:** javascript

O valor de `this` é determinado por COMO a função é chamada, não onde é definida: (1) chamada de método `obj.f()` — `this` = obj; (2) chamada solta `f()` — `this` = global (ou `undefined` em strict mode); (3) `new F()` — `this` = novo objeto; (4) `call`/`apply`/`bind` — `this` = argumento explícito; (5) arrow functions ignoram tudo isso e usam o `this` léxico do escopo de criação. `bind` fixa permanentemente (bind de bind não re-binda); arrow + bind = no-op.

Prototypes: todo objeto tem um prototype (cadeia). Herança real em JS é delegativa: `child.prop` percorre a cadeia até encontrar `prop`. `Object.create(proto)` cria objeto com prototype explícito (melhor que `new` para herança). `class` (ES6) é açúcar sintático sobre prototypes — `extends` monta a cadeia, `super` chama o construtor pai.

Detalhes que separam iniciante de sênior:
- `Array.prototype.map` etc. só funcionam em objetos array-like se chamados com `.call(arrayLike, fn)`.
- `Function.prototype` herda de `Object.prototype`; `Object.create(null)` cria dicionário puro sem prototype — `{}.hasOwnProperty` pode ser sobrescrito, use `Object.hasOwn(obj, key)` (ES2022) ou `Object.prototype.hasOwnProperty.call`.
- Propriedades de instância sombreiam as do prototype (shadowing) — remover com `delete` revela a do prototype.
- `constructor` é uma propriedade convencional, não garantida.

Armadilhas:
- Perder `this` ao passar método solto: `arr.forEach(obj.method)` — use arrow `x => obj.method(x)` ou `obj.method.bind(obj)`.
- `new` com arrow lança TypeError.
- `class` não sofre hoisting e não pode ser chamado sem `new` (TypeError).
- Herança múltipla nativa não existe — use composição ou mixins.

Melhores práticas: prefira `class` para domínio e factories para construção complexa. Para objetos-dicionário, `Object.create(null)` ou Map. Compare corretamente: `obj.constructor === Array` é frágil — use `Array.isArray`. Memoize com `Map` para evitar colisão de chaves (`{__proto__: ...}`). Cadeia de prototypes rasteira significa menos lookups e menos bugs de shadowing.
## Conexoes

- [[cluster-hub-programacao]]
- [[javascript-assincronismo-event-loop-promises-e-asyncawait]]
- [[javascript-closures-escopo-e-hoisting]]
- [[javascript-tipos-coerção-e-igualdade]]
- [[padrao-hub-padroes]]