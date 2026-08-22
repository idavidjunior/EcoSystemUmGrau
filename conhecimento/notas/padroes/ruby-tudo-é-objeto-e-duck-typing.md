---
tags: [labels, nada, padrao, pato, proxies, ruby]
aliases: [Ruby: tudo é objeto e duck typing]
date: 2026-08-22
---

# Ruby: tudo é objeto e duck typing

**Fonte:** ruby

### Tudo é objeto

Em Ruby **não existem tipos primitivos**: `1`, `"a"`, `true`, `nil` são objetos. `1.class` → `Integer`; `nil.class` → `NilClass`. Chamar método é **enviar mensagem**: `obj.metodo` equivale a `obj.send(:metodo)`. Se o método não existe, `method_missing` pode interceptar — base de DSLs e proxies. Teste antes com `obj.respond_to?(:metodo)`.

### Duck typing

O tipo concreto não importa, apenas os métodos respondidos ("se faz quack e nada, é um pato"). Idiomático: `def processa(obj); obj.work; end` funciona com qualquer classe que implemente `work`. Combine com `respond_to?` para código defensivo ou com um módulo `include` para contratos leves.

### nil e valores

- `nil` é o único objeto de `NilClass` e é falsy; `false` também é falsy. **Somente esses dois** são falsy — `0`, `""`, `[]`, `{}` são truthy (diferente de C/PHP).
- Variáveis não inicializadas valem `nil`; `hash[:chave_ausente]` retorna `nil` (ou o `default`) sem levantar erro.
- Para checar presença, use `x.nil?`/`x.empty?`; evite `if x` para testar nil-ness de flags.

### Convenções

- `snake_case` para variáveis e métodos; `CamelCase` para classes e módulos.
- `?` e `!` no fim do nome fazem parte do identificador: `?` indica predicado que devolve booleano (`empty?`), `!` indica versão perigosa/mutante (`save!`, `map!`).
- Getters/setters: `attr_reader :name`, `attr_writer`, `attr_accessor` geram `name` e `name=` automaticamente.
- `self` é **obrigatório** para atribuir dentro de método (`self.name = x`); sem ele, cria-se variável local.

### Symbols

`Symbols` (`:nome`) são strings imutáveis e internadas — use como chaves de Hash e labels; comparam por identidade e economizam memória. `str.to_sym`, `sym.to_s`. `{ nome: "x" }` é açúcar para `{ :nome => "x" }`.

```ruby
def chama(obj)
  obj.call if obj.respond_to?(:call)
end
x = nil
puts x&.nome          # nil-safe navigation (2.3+)
puts [1, 2, 3].sum     # 6
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[ruby-blocks-procs-e-lambdas]]
- [[ruby-rails-activerecord-e-mvc]]