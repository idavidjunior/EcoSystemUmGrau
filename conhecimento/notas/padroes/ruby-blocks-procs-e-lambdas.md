---
tags: [closure, fornece, métodos, padrao, reduce, ruby]
aliases: [Ruby: blocks, procs e lambdas]
date: 2026-08-23
---

# Ruby: blocks, procs e lambdas

**Fonte:** ruby

### Blocks

Um **block** é o par `do...end` (multilinha) ou `{...}` (uma linha) passado implicitamente a qualquer método. Não é objeto por si — torna-se `Proc` quando capturado. Dentro do método, chame com `yield`; ou capture com `&blk` na assinatura e invoque via `blk.call`. `block_given?` testa a presença. Ignorar um block não é erro.

### yield e iteradores

Blocks são a base da iteração idiomática: `[1,2,3].each { |n| puts n }`. O módulo **Enumerable** (incluído em `Array`, `Hash`, `Range`) fornece `map`, `select`, `reduce`, `any?`, `sort_by` etc. — basta definir `each` na sua classe e `include Enumerable` para ganhar dezenas de métodos.

### Proc vs Lambda

- **Proc** (`proc {}` ou `Proc.new {}`): `return` dentro do Proc retorna do *método circundante* (fuga de escopo). Argumentos faltantes viram `nil` — sem verificação de arity.
- **Lambda** (`->(x) {}` ou `lambda {}`): `return` retorna apenas da própria lambda. Arity rígida: número errado de argumentos lança `ArgumentError`.
- `&:metodo` (`Symbol#to_proc`): `[1,2,3].map(&:to_s)` equivale a `map { |n| n.to_s }`. Combina com `select`, `reject`, `any?`.

### Closures

Blocks/Procs capturam as variáveis locais do escopo onde foram criados (closure). Permite factories, memoização, configurators e DSLs com escopo limitado.

### Regras práticas

- Use `{ }` para blocks de uma linha, `do...end` para multilinhas e para blocks que retornam valores encadeados.
- Passe blocos adiante: `def m(&b); outro(&b); end`.
- Lambdas quando precisar de `return` interno e validação de argumentos; Procs para callbacks desestruturados/curtos.

```ruby
def cada_com_indice(arr, &blk)
  arr.each_with_index { |e, i| blk.call(e, i) }
end
cada_com_indice(%w[a b]) { |e, i| puts "#{i}: #{e}" }

prc = proc { |x| x }
prc.call              # => nil (arg ausente vira nil)
lam = ->(x) { x * 2 }
lam.call              # ArgumentError (arity rígida)
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[ruby-rails-activerecord-e-mvc]]
- [[ruby-tudo-é-objeto-e-duck-typing]]