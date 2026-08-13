---
tags: [ergonomia, forçando, padrao, partialeq, rust, tratamento]
aliases: [Rust: enums, pattern matching, Result e Option]
date: 2026-08-13
---

# Rust: enums, pattern matching, Result e Option

**Fonte:** rust

Enums de Rust são tagged unions (dados + tag de discriminante) e a base da modelagem de erros e de soma de tipos. `enum Option<T> { None, Some(T) }` e `enum Result<T, E> { Ok(T), Err(E) }` são os cavalos de batalha: sem exceções e sem null pointer, todo fallo é representado no tipo.

Pattern matching com `match` é exaustivo (o compilador exige cobrir todos os casos — adicionar um variant quebra a compilação, forçando tratamento):

```rust
let n = s.parse::<i32>().map_err(|e| format!("parse: {e}"))?;  // ? propaga erro
match v {
    Some(x) if *x > 10 => println!("grande: {x}"),
    Some(x) => println!("pequeno: {x}"),
    None => println!("vazio"),
}
```

`?` é o idioma de propagação de erro: em função que retorna `Result`, `foo()?` extrai `T` e propaga `Err` no caminho de erro automaticamente (via `From`). Isso substitui try/catch com custo zero e verificação em tempo de compilação.

Combinadores para pipelines: `.ok()`, `.map()`, `.and_then()`, `.unwrap_or_default()`, `.ok_or_else(|| ...)`, `.filter()`, `.collect::<Result<_, _>>()` (para 'colapsar' vetores de Result em Result de vetor). Evite `unwrap()`/`expect()` fora de testes/protótipos — são panics disfarçados. Erros próprios: derive `Debug + Display` e implemente `std::error::Error`; ou use `thiserror` (deriva) / `anyhow` (erros dinâmicos em apps). `panic!` é para bugs invariantes quebrados, não para fluxo esperado.

Idioma para domain modeling: enum para estados exclusivos (`enum Msg { Text(String), File(Vec<u8>) }`), `#[derive(Debug, Clone, PartialEq)]` para ergonomia. Ao lidar com `Option`, prefira `if let Some(x) = ...` para um caso único e `match` para cobertura exaustiva. Quando usar: toda função que pode falhar retorna `Result`; `Option` quando ausência é estado normal. Nunca crie null-aware structs à moda de outras linguagens — use o sistema de tipos.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[rust-lifetimes-referências-e-elisão]]
- [[rust-ownership-borrow-checker-e-o-modelo-de-memória]]
- [[rust-traits-generics-e-trait-objects]]