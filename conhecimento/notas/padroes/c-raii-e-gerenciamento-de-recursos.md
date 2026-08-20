---
tags: [caminhos, cpp, cópia, erro, movimento, padrao]
aliases: [C++: RAII e gerenciamento de recursos]
date: 2026-08-20
---

# C++: RAII e gerenciamento de recursos

**Fonte:** cpp

RAII (Resource Acquisition Is Initialization) é o idioma central do C++: o construtor adquire o recurso, o destrutor o libera, e o escopo (ou a pilha de desempilhamento em exceções) garante a liberação mesmo em caminhos de erro. Substitui a gestão manual de C com custo zero:

```cpp
void f() {
    std::ifstream in("file.txt");   // abre: construtor
    if (!in) throw std::runtime_error("abrir");
    // ... leitura ...
}  // fecha automaticamente no destrutor, mesmo com throw
```

Regra dos 3/5: se você declarar destrutor, copy constructor ou copy assignment, declare todos — e no C++11 decida o destino das operações de cópia/movimento. Classes de recursos raramente devem ser copiadas (um `FILE*` duplicado = double-free); use `= delete` para proibir.

Os smart pointers são RAII prontos: `std::unique_ptr<T>` (propriedade exclusiva, move-only), `std::shared_ptr<T>` (contagem de referências, bloqueio do pointee com `std::weak_ptr` para quebrar ciclos). Regra prática: `unique_ptr` por padrão; `shared_ptr` apenas quando a propriedade é genuinamente compartilhada; ponteiros brutos apenas como observadores não proprietários (`T*` = "empréstimo"). Exceções: destrutores devem ser `noexcept` e não lançar — `std::terminate` no unwind duplo.

`std::vector`, `std::string`, `std::lock_guard`, `std::thread` e containers da STL são RAII: quando você os usa em vez de `new[]`/`malloc`/`free`, elimina leaks e UAF por construção. Se precisar de alocação própria, use `std::make_unique`/`std::make_shared` (exceção-safe, uma única alocação para shared).

Quando usar: todo recurso — memória, arquivos, sockets, mutexes, conexões — deve ter um owner RAII; a gestão manual só é justificável em código de baixíssimo nível isolado e revisado. Combine RAII com exceções para satisfazer a garantia forte (strong exception safety): nunca deixe invariantes quebradas no meio.
## Conexoes

- [[c-move-semantics-rvalue-references-e-ownership]]
- [[c-templates-sfinae-constexpr-e-o-custo-zero]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]