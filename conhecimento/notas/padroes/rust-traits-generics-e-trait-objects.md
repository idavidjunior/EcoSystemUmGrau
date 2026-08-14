---
tags: [dry, padrao, retornado, rust, safe, útil]
aliases: [Rust: traits, generics e trait objects]
date: 2026-08-14
---

# Rust: traits, generics e trait objects

**Fonte:** rust

Traits são o mecanismo de abstração do Rust — meio-termo entre interfaces de OOP e conceitos de C++: definem contratos de comportamento, são implementáveis para tipos locais e estrangeiros (orpan rule: impl do trait OU do tipo deve ser local), e habilitam composição. `impl Trait` em assinaturas abstrai o tipo concreto com custo zero; `&dyn Trait`/`Box<dyn Trait>` usam vtable (dynamic dispatch).

```rust
trait Area { fn area(&self) -> f64; }
impl Area for Circle { fn area(&self) -> f64 { std::f64::consts::PI * self.r * self.r } }
fn total<T: Area>(xs: &[T]) -> f64 { xs.iter().map(Area::area).sum() }
```

Generics (`T: Trait`, `where` clause) geram código monomorfizado — cada tipo concreto tem sua instância; sem custo de indireção, mas binário maior (explosão de instanciação). Trait objects (`dyn`) são unsized, exigem `&`/`Box`/`Rc` e só funcionam para traits object-safe (sem generics nos métodos, sem `Self` retornado); dão flexibilidade de runtime por vtable.

Padrões poderosos: `trait IterExt { fn sum(self) ... }` (extensões), blanket impls (`impl<T: Display> ToString for T`), supertraits (`trait Copy: Clone`), `From`/`TryFrom`/`Into` para conversões, `Default`, `Clone`, `PartialEq` via derive. `Sized` (padrão) vs `?Sized` para slices/traits. Parâmetros genéricos com `const` (`fn f<const N: usize>`) para arrays/templates numéricos. Marker traits (`Send`, `Sync`, `Unpin`) controlam segurança entre threads em compile time: `Send` = pode mover para outra thread; `Sync` = pode compartilhar via referência.

Armadilhas: trait objects não são `Send`/`Sync` automaticamente (use `Box<dyn Trait + Send + Sync>`); object safety violada gera erro enigmático; orphan rule impede `impl Display for Vec<String>`; cadeias de traits com métodos default e sobrescrita errada confundem resolução. `impl Trait` em argumento (universal) vs retorno (existencial) — no retorno esconde o tipo concreto (DRY, e útil para closures: `impl Fn(i32) -> i32`). Quando usar: generics por padrão (performance e sem dynamic); trait objects quando a coleção heterogênea ou a escolha em runtime importa; closures como traits `Fn`/`FnMut`/`FnOnce` para callbacks e pipelines.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[rust-enums-pattern-matching-result-e-option]]
- [[rust-lifetimes-referências-e-elisão]]
- [[rust-ownership-borrow-checker-e-o-modelo-de-memória]]