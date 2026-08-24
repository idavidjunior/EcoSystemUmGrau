---
tags: [cpp, movido, padrao, seguros, será, são]
aliases: [C++: move semantics, rvalue references e ownership]
date: 2026-08-10
---

# C++: move semantics, rvalue references e ownership

**Fonte:** cpp

C++11 introduziu rvalue references (`T&&`) e move semantics: transferir recursos (heap, fds) por roubo em vez de cópia profunda. `std::move(x)` apenas converte `x` para rvalue (declaração de intenção); o custo real vem dos construtores de movimento das classes. Copiar um `std::vector` com 1e6 elementos custa 1e6 cópias; movê-lo custa 3 ponteiros.

```cpp
std::vector<int> v;
std::vector<int> w = std::move(v);  // v fica vazio, w rouba o buffer
```

Pontos críticos: (1) `std::move` não move nada — é um cast para `T&&`; (2) após mover, o objeto está em estado válido mas não especificado — só atribuição/`clear`/`resize` são seguros; (3) `T&&` em parâmetro de template é `T&&` universal/forwarding reference (dedução de tipo) e usa `std::forward` para encaminhar, não `std::move`; (4) retornar por valor (`return v;`) já é move/elided automaticamente (NRVO/copy elision) — `std::move` no retorno pode IMPEDIR a elisão. Regra de ouro: não mova objetos que você ainda precisa, e não declare `const` num parâmetro que será movido.

Ownership: cada objeto tem dono (owner). Dono com `unique_ptr` move a propriedade; `shared_ptr` copia a referência. `std::move` aparece em containers para transferir o buffer, em `push_back(std::move(x))`, e em fábricas que constroem por valor. Assinaturas que expressam intenção: `void f(std::vector<int> v)` (copia OU move conforme o chamador), `void g(const std::vector<int>&)` (só lê), `void h(std::vector<int>&&)` (modifica/consome).

Armadilhas: mover de um objeto ainda em uso (use-after-move é bug sutil); `std::move` em `const` objeto silenciosamente vira cópia; move não é gratuito em tipos triviais (é cópia mesmo); `std::array` move elemento a elemento. Quando usar: passar e retornar containers pesados, transferir recursos, implementar move constructors/assignment (regra dos 5). Medir com `-fno-elide-constructors` para ver os movimentos reais.
## Conexoes

- [[c-raii-e-gerenciamento-de-recursos]]
- [[c-templates-sfinae-constexpr-e-o-custo-zero]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]