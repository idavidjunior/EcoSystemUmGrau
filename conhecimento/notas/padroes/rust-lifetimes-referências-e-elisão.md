---
tags: [devolve, intenção, padrao, rust, time, visão]
aliases: [Rust: lifetimes, referências e elisão]
date: 2026-08-13
---

# Rust: lifetimes, referências e elisão

**Fonte:** rust

Lifetimes são a notação do borrow checker para 'quanto tempo esta referência pode viver'. Em `&'a T`, `'a` é o intervalo durante o qual `T` está emprestado. O compilador verifica que uma referência nunca sobrevive ao dado que referencia — é o que mata use-after-free em compile time.

Na prática você raramente escreve lifetimes: a elisão inferida cobre `fn f(x: &T) -> &T` (retorno empresta de `x`). Escrever anotações é necessário quando o retorno não é óbvio ou há múltiplas entradas:

```rust
fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() > b.len() { a } else { b }
}
```

Aqui `'a` une ambos os parâmetros ao retorno: o chamador garante que o resultado não sobrevive a nenhum dos dois. Lifetimes estão em tipos de referência — não mudam a runtime, são zero-cost.

Estruturas que guardam referências precisam de parâmetro de lifetime: `struct Parser<'a> { s: &'a str }` — uma vez embutido, ele contamina (propaga) para impls e usos. Alternativas quando isso aperta: owned (`String` em vez de `&str`), ou `Cow<'a, str>` para dados que às vezes são emprestados, às vezes owned.

Lifetimes especiais: `'static` = vive por todo o programa (literais `&'static str`, `static`); aparece muito em threads (`'static` para mover para nova thread) e trait objects. Armadilhas: retornar referência a variável local é erro clássico; drop order importa (`std::mem::drop` para forçar); reborrowing (`&*x` quando `x: &mut T`) é idiomático e seguro. Não confie na 'cadeira elétrica' do compilador para validar sua lógica de propriedade — as anotações documentam intenção. Quando usar: parâmetros de leitura (`&str` em vez de `&String`), slices `&[T]` para iterar/ler arrays, e qualquer API que devolve visão de dados owned.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[rust-enums-pattern-matching-result-e-option]]
- [[rust-ownership-borrow-checker-e-o-modelo-de-memória]]
- [[rust-traits-generics-e-trait-objects]]