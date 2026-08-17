---
tags: [chain, golang, modere, padrao, privado, string]
aliases: [Go: context, cancelamento e timeouts]
date: 2026-08-17
---

# Go: context, cancelamento e timeouts

**Fonte:** golang

# context, cancelamento e timeouts

`context.Context` é a forma idiomática de propagar cancelamento, deadlines e valores de request pela call chain. Deve ser o **primeiro parâmetro** de funções e o ponto de entrada de servidores. Nunca armazene em struct.

## Idioms
- `context.Background()` é a raiz (geralmente em `main`); `context.TODO()` onde ainda não decidiu.
- `WithCancel`, `WithTimeout`, `WithDeadline` derivam filhos; **sempre** chame o `cancel()` devolvido (via `defer`) para liberar timers — mesmo se a operação terminar antes.
- Em loops/goroutines: `select { case <-ctx.Done(): return; case <-ch: ... }` para respeitar cancelamento.
- `WithValue` para dados de request (correlation IDs, principal) — use chave de tipo privado, não string, e modere: é só para request-scoped.
- Handlers HTTP já recebem `ctx` via `r.Context()`; clientes (`net/http`, grpc, drivers) respeitam cancelamento automaticamente.
- `errgroup` (golang.org/x/sync) orquestra fan-out com cancelamento no primeiro erro.

## Armadilhas
- **Esquecer `cancel()`**: timers internos ficam presos e viram vazamento sob carga. `defer cancel()` cobre a maioria dos casos.
- Passar `Background()` no meio da cadeia quebra o cancelamento — propague sempre o ctx recebido.
- Bloquear em `ch <- x` sem `select` ignora cancelamento → goroutine trava.
- `WithValue` com valores mutáveis ou chaves de tipo built-in colidem; use chave de tipo próprio.
- Context não é para «configuração opcional» — para isso use argumentos normais.

```go
ctx, cancel := context.WithTimeout(parent, 3*time.Second)
defer cancel()
res, err := http.NewRequestWithContext(ctx, ...)
```

Regra: ctx como primeiro parâmetro, `defer cancel()`, e `select` no `ctx.Done()` em qualquer bloqueio.
## Conexoes

- [[cluster-hub-programacao]]
- [[go-goroutines-canais-e-csp]]
- [[go-interfaces-implícitas-method-set-e-composição]]
- [[go-slices-maps-e-ponteiros]]
- [[padrao-hub-padroes]]