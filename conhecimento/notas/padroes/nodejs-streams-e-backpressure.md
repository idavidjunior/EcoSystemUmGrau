---
tags: [crypt, gzip, json, node, padrao, parse]
aliases: [Node.js: streams e backpressure]
date: 2026-08-17
---

# Node.js: streams e backpressure

**Fonte:** node

Streams processam dados por pedaços (chunks) em vez de carregar tudo na memória — essencial para arquivos grandes, rede e pipelines. Quatro tipos: Readable (fonte), Writable (destino), Duplex (ambos) e Transform (modifica chunks, tipo gzip, crypt, JSON parse).

API moderna (Node 10+): async iterables.
```javascript
for await (const chunk of readableStream) {
  await writable.write(chunk);
}
```
`stream/promises` oferece `pipeline(readable, transform, writable)`, `finished(stream)`. Prefira `pipeline` a `pipe()` — `pipeline` propaga erros e destrói corretamente; `pipe` não propaga erros e pode vazar (leaks). `pipeline` também faz backpressure automaticamente.

Backpressure: quando a leitura é mais rápida que a escrita, o Writable sinaliza. Com `pipe`/`pipeline`/`for await`, o Node pausa o Readable (`highWaterMark` controla o buffer, padrão 16KB; para buffers de alta vazão aumente com `stream.pipeline`+`highWaterMark`). Se escrever manualmente, cheque `writable.write(chunk)` — se retornar `false`, aguarde o evento `drain` antes de continuar; ignorar isso estoura a memória do processo.

Eventos: Readable — `data` (flowing mode), `readable` (paused mode, chame `read()`), `end`, `error`; Writable — `drain`, `finish`, `error`. Sempre trate `error` — sem handler o erro derruba o processo. Com async iterable e `for await`, erro de stream vira exceção.

Armadilhas: `stream.pipe` em dois destinos precisa `pipe` de novo e destrói ambos (ou use `Readable.tee`); consumir stream duas vezes não funciona — re-leitura exige `Buffer.concat` prévio ou buffer em memória (cuidado com tamanho). `readable.push(null)` finaliza. `Transform._transform` deve chamar `callback`/`push` — esquecer trava o pipeline. `pipeline` destrói streams automaticamente em erro, mas você deve dar `setTimeout` para `close` antes de terminar o processo.

Melhores práticas: sempre `pipeline`; prefira Transform a manual chunks; para processar em paralelo use `pipeline` com agregação controlada; monitore com `stream.finished` e `finished(stream, cb)`; para teste use `Readable.from([chunks])` e colete com `stream/promises` + `Array.fromAsync`.
## Conexoes

- [[cluster-hub-programacao]]
- [[nodejs-commonjs-esm-e-resolução-de-módulos]]
- [[nodejs-event-loop-e-io-não-bloqueante]]
- [[padrao-hub-padroes]]