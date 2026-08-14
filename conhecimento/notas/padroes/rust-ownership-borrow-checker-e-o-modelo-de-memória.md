---
tags: [atomic, multi, padrao, rust, rwlock, thread]
aliases: [Rust: ownership, borrow checker e o modelo de memória]
date: 2026-08-14
---

# Rust: ownership, borrow checker e o modelo de memória

**Fonte:** rust

Rust garante memory safety SEM GC via ownership: toda alocação tem um dono (owner); quando o dono sai de escopo, a memória é liberada (drop). Regras: (1) cada valor tem um único owner; (2) uma `&mut` ou várias `&` simultâneas, nunca ambas; (3) referências nunca vivem mais que o dado. O borrow checker é um provador de tipos sobre esses contratos — erros de empréstimo são erros de compilação, não UB.

```rust
let s = String::from("oi");  // s é o dono
let t = s;                    // move: s fica inválido (compilador nega uso)
// println!("{s}");            // erro E0382: borrow of moved value
let r = &t;                   // empréstimo compartilhado (ler)
```

Consequências práticas: sem use-after-free, sem double-free, sem data races em threads — tudo vira erro em tempo de compilação. O custo é a curva de aprendizado: 'brigar com o borrow checker' significa tipar a propriedade (quem é dono? quem empresta?). Padrões para contornar: clonar (`clone`, explícito e custoso), `Rc`/`Arc` (contagem de referências, compartilhamento), `RefCell`/`Mutex` (mutabilidade interior com regras de runtime), ou redesenhar para dono único.

Mutabilidade interior: `&mut` exige exclusividade; para mutar através de `&`, use `Cell<T>` (Copy) ou `RefCell<T>` (dinâmico, panics em empréstimo conflitante em runtime) em single-thread, `Mutex`/`RwLock`/`Atomic*` em multi-thread. `Arc<Mutex<T>>` é o 'shared_ptr + mutex' do Rust.

Padrões idiomáticos: tipos pequenos em stack com ownership linear; APIs que retornam owned data (`impl ToOwned`); entrada por `&T`/`&mut T`, saída por owned. Quando usar: todo código Rust — não existe 'modo sem borrow checker'. Otimização final de perf: `unsafe` é reservado a casos medidos e comentados com invariantes; o restante da base fica segura.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[rust-enums-pattern-matching-result-e-option]]
- [[rust-lifetimes-referências-e-elisão]]
- [[rust-traits-generics-e-trait-objects]]