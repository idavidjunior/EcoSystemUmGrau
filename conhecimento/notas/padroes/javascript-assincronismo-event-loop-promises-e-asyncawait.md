---
tags: [efeito, javascript, moderno, padrao, processo, repete]
aliases: [JavaScript: assincronismo (event loop, promises e async/awai]
date: 2026-08-15
---

# JavaScript: assincronismo (event loop, promises e async/await)

**Fonte:** javascript

JavaScript é single-threaded; o event loop gerencia a execução. Chamadas assíncronas (timers, I/O, promises) colocam callbacks em filas que são processadas quando a call stack esvazia. Ordem de processamento: microtasks (promises, queueMicrotask) rodam ANTES da próxima macrotask (timers, I/O, eventos). Isso explica por que `Promise.resolve().then(...)` executa antes de `setTimeout(..., 0)`.

Promises têm três estados (pending, fulfilled, rejected) e são imutáveis após resolução — consumir a mesma promise não repete o efeito. `then` devolve nova promise permitindo encadeamento; erros fluem pela cadeia até um `catch`. Padrões essenciais:
- `Promise.all` (todas ou nada, falha rápido), `Promise.allSettled` (espera todas, com status), `Promise.race` (primeira que resolver), `Promise.any` (primeira fulfilled, ES2021).
- `new Promise((resolve, reject) => ...)` é um anti-padrão quando você só quer converter API de callback — use `util.promisify` (Node) ou wrappers prontos.
- Evite promise chains profundas; `async/await` é açúcar sobre promises e deve ser o padrão.

`async/await`: `await` pausa a execução da função async sem bloquear o thread. Erros precisam de `try/catch` — um `await` rejeitado não capturado vira unhandled rejection (derruba o processo em Node moderno). Executar em paralelo: nunca `await` dentro de loop quando as chamadas são independentes — colete `const p = items.map(fn)` e `await Promise.all(p)`.

Armadilhas:
- Callback hell: aninhamento de callbacks — a migração para promises resolve.
- Esquecer `await` em `async` função retorna Promise não resolvida (bug de timing sutil).
- `for await...of` para streams e iterables async.
- Timer com atraso zero não é garantia de imediatismo.

Melhores práticas: `async/await` por padrão; `Promise.all` para concorrência; cancelamento com AbortController em vez de rejeitar manualmente; nunca misturar callbacks e promises no mesmo caminho.
## Conexoes

- [[cluster-hub-programacao]]
- [[javascript-closures-escopo-e-hoisting]]
- [[javascript-this-prototypes-e-herança]]
- [[javascript-tipos-coerção-e-igualdade]]
- [[padrao-hub-padroes]]