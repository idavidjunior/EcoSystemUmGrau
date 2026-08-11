---
tags: [binding, inicialização, mesmos, node, padrao, tdz]
aliases: [Node.js: CommonJS, ESM e resolução de módulos]
date: 2026-08-11
---

# Node.js: CommonJS, ESM e resolução de módulos

**Fonte:** node

Dois sistemas de módulos coexistem no Node: CommonJS (CJS) e ECMAScript Modules (ESM). CJS usa `require`/`module.exports` e é síncrono; ESM usa `import`/`export`, é assíncrono (top-level await permitido) e é o padrão moderno. Detecção: em `package.json`, `"type": "module"` torna `.js` em ESM; sem ele, `.js` é CJS. Extensões forçam: `.mjs` = ESM, `.cjs` = CJS.

Diferenças que mordem:
- No ESM, `import` exige extensão de arquivo local: `import { x } from './util.js'` — sem extensão falha. Em TS com `nodenext`, importe com `.js` mesmo em arquivo `.ts`.
- ESM não tem `__dirname`/`__filename`; derive com `import.meta.url` + `fileURLToPath`.
- CJS tem `require.cache` (clear para hot-reload); ESM tem cache próprio, módulos avaliados uma vez por processo.
- ESM é estrito, não expõe `module`, `exports`, `require` implicitamente — mas `import { createRequire }` cria um `require` compatível.
- `require` é síncrono: não pode importar módulo ESM diretamente em CJS por sync (desde Node 22+ há suporte experimental `require(esm)`); ESM importa CJS sem problema (default export é o `module.exports`).

Resolução: procura `exports` (se field existir, rege TUDO — caminhos fora ficam bloqueados, inclusive arquivos internos), depois `main`, depois `index.js`. O field `exports` permite subpath exports e barreiras: `"exports": { "./package.json": "./package.json" }`.

Armadilhas: circular dependency — CJS resolve com objeto incompleto (partial exports), ESM lança ReferenceError se acessar binding antes de inicialização (TDZ); evite ciclos ou use lazy require. Dual package hazard: mesma lib carregada como CJS e ESM = duas instâncias (estado duplicado) — resolva com `exports` apontando `require`/`import` para os mesmos arquivos. Named exports de CJS não são detectáveis no ESM — use default ou `module.exports = { a, b }`.

Melhores práticas: use ESM para código novo (ecossistema converge para isso); `"type": "module"` + `exports` no package.json; migre código legado incrementalmente (.cjs); para ferramentas CLI, considere `tsx`/`ts-node` para TS ESM.
## Conexoes

- [[cluster-hub-programacao]]
- [[nodejs-event-loop-e-io-não-bloqueante]]
- [[nodejs-streams-e-backpressure]]
- [[padrao-hub-padroes]]