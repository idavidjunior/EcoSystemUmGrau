---
tags: [blocking, delegado, interface, node, non, padrao]
aliases: [Node.js: event loop e I/O não bloqueante]
date: 2026-08-14
---

# Node.js: event loop e I/O não bloqueante

**Fonte:** node

Node.js é um runtime JavaScript sobre o motor V8 com libuv por baixo. O model é single-threaded para código JS + thread pool para I/O pesado. O event loop (implementado pela libuv) processa fases em ordem: timers (setTimeout/setInterval), pending callbacks, idle/prepare, poll (I/O — fase onde a maioria dos callbacks roda), check (setImmediate) e close callbacks. Microtasks (promises, queueMicrotask, process.nextTick) rodam entre fases, com `nextTick` ANTES de promises.

Consequências práticas:
- `setImmediate` vs `setTimeout(0)`: dentro de módulo a ordem depende do contexto (timer pronto no início do loop, check no fim); no poll, setImmediate roda antes do próximo timer.
- `process.nextTick` deveria ser evitado em código de aplicação — recursão sem cuidado esgota a call stack de microtasks; use para delegar callbacks síncronos ao fim do tick.
- Código CPU-bound bloqueia o loop inteiro: requisições, timers e I/O morrem juntos. Divida em chunks (`setImmediate`/worker) ou delegue a `worker_threads`.

I/O não bloqueante: todas as APIs do core (fs, net, http, crypto) têm versões async que retornam antes de terminar. `fs.promises` é a API moderna (promises); `fs.readFileSync` e outras versões sync bloqueiam o loop — proibidas em handlers de requisição.

Thread pool: `crypto.pbkdf2`, `zlib`, `fs` async usam `libuv` thread pool (padrão 4 threads, ajustável via `UV_THREADPOOL_SIZE`) — I/O de arquivo não é assíncrono de verdade, é delegado a threads, mas a interface é non-blocking. Rede (TCP/UDP) é genuinamente assíncrona via epoll/IOCP, sem consumir thread pool.

Armadilhas: unhandled rejection derruba o processo (desde Node 15); `--unhandled-rejections=strict` é o padrão. `process.exit()` mata sem drenar pending I/O. Grandes buffers em `Buffer` (não-UTF-8-friendly, use TextDecoder quando precisar) — `Buffer.from(string)` vs `new Buffer()` (deprecated). Melhores práticas: tudo async, `fs/promises`, limites de concorrência (p-limit ou Promise.all com batch), e health checks que monitoram event loop delay (process.hrtime).
## Conexoes

- [[cluster-hub-programacao]]
- [[nodejs-commonjs-esm-e-resolução-de-módulos]]
- [[nodejs-streams-e-backpressure]]
- [[padrao-hub-padroes]]