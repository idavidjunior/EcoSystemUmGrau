---
tags: [consumidores, fatal, golang, padrao, pelo, sincronização]
aliases: [Go: goroutines, canais e CSP]
date: 2026-08-17
---

# Go: goroutines, canais e CSP

**Fonte:** golang

# goroutines, canais e CSP

Goroutines são «threads» leves multiplexadas pelo runtime sobre threads de OS; criar milhares é normal (stack inicial ~2 KB, cresce sob demanda). O agendador as distribui em `GOMAXPROCS` threads. O modelo é **CSP**: «don't communicate by sharing memory; share memory by communicating».

## Idioms
- Canal **não bufferizado** (sem capacidade): cada envio sincroniza com um recebimento — *rendezvous* usado para sinais e sincronização.
- Canal **bufferizado** (capacidade > 0): fila; envio não bloqueia até encher.
- `close(ch)` sinaliza fim; iterar com `for v := range ch` drena até o fechamento.
- `select { case ...: default: }` para operação não-bloqueante; `select` com `ctx.Done()` para cancelamento.
- Worker pool: N goroutines consumindo de um canal de jobs + `sync.WaitGroup` para aguardar a conclusão.
- Quem cria o canal é quem fecha (Go idiom), nunca os consumidores.

## Armadilhas
- Enviar em canal fechado → **panic**; fechar duas vezes → panic.
- Deadlock: todos bloqueados esperando uns pelos outros (o runtime detecta e faz fatal).
- **Goroutine leak**: goroutine bloqueada para sempre (canal sem consumidor). Sempre vincule a `context` ou use buffer.
- Data race no estado compartilhado: acesse só do dono ou use `sync.Mutex`/`sync/atomic`.
- Não use canal para tudo: mutex é mais simples para proteger estado simples.

```go
jobs := make(chan int)
var wg sync.WaitGroup
for i := 0; i < 4; i++ { // 4 workers
    wg.Add(1)
    go func() { defer wg.Done(); for j := range jobs { process(j) } }()
}
close(jobs)
wg.Wait()
```

Regra: quem possui o canal decide o destino; canais para coordenação, mutex para proteção de dado.
## Conexoes

- [[cluster-hub-programacao]]
- [[go-context-cancelamento-e-timeouts]]
- [[go-interfaces-implícitas-method-set-e-composição]]
- [[go-slices-maps-e-ponteiros]]
- [[padrao-hub-padroes]]