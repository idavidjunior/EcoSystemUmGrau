---
tags: [funcs, golang, maps, nulo, padrao, slices]
aliases: [Go: interfaces implícitas, method set e composição]
date: 2026-08-23
---

# Go: interfaces implícitas, method set e composição

**Fonte:** golang

# Interfaces implícitas, method set e composição

Go implementa interfaces **implicitamente**: não há palavra `implements`; um tipo satisfaz a interface se tiver todos os métodos exigidos. Isso dá duck typing estrutural e acoplamento fraco.

## Idioms
- Interfaces pequenas e específicas: `io.Reader`, `io.Writer`, `error` (um método `Error() string`). «Quanto maior a interface, mais fraca a abstração.»
- Componha interfaces: `type ReadWriter interface { io.Reader; io.Writer }`.
- Receivers definem o method set: com receiver **valor** (`func (p Point) M()`), tanto `Point` quanto `*Point` implementam; com receiver **ponteiro**, só `*Point` implementa. Interfaces que exigem ponteiro limitam o uso por valor.
- Defina a interface no **consumidor**; «accept interfaces, return concrete types».
- `any` (alias de `interface{}`) aceita tudo; para parametrização segura prefira **genéricos** (Go 1.18+) em vez de `any` + type switch.

## Armadilhas
- **Nil interface trap**: `(*T)(nil)` convertido para interface resulta em interface não-nula com ponteiro interno nulo; `iface != nil` é `true`, mas chamar métodos pode panicar. Verifique o valor, não a interface.
- Adicionar um método a uma interface grande quebra todos os implementadores (compatibilidade).
- Interfaces são comparáveis apenas se o tipo dinâmico for comparável (panic em runtime com slices/maps/funcs).
- Reflexão e `fmt` sobre interfaces perdem informação de tipo estático; use type switch com moderação.

```go
type Reader interface{ Read(p []byte) (n int, err error) }

var r io.Reader = bytes.NewBufferString("ok") // satisfeita implicitamente
```

Regra: interfaces pequenas no lado do consumidor, receivers coerentes e tipos concretos como retorno.
## Conexoes

- [[cluster-hub-programacao]]
- [[go-context-cancelamento-e-timeouts]]
- [[go-goroutines-canais-e-csp]]
- [[go-slices-maps-e-ponteiros]]
- [[padrao-hub-padroes]]