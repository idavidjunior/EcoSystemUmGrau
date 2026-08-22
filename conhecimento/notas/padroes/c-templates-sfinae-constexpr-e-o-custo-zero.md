---
tags: [cpp, ferramenta, legíveis, melhor, padrao, suporta]
aliases: [C++: templates, SFINAE, constexpr e o custo-zero]
date: 2026-08-22
---

# C++: templates, SFINAE, constexpr e o custo-zero

**Fonte:** cpp

Templates geram código em tempo de compilação parametrizado por tipo/valor — o 'abstração de custo zero': você escreve uma vez, o compilador instancia por tipo. `<algorithm>`, `std::vector<T>`, lambdas e meta-programação dependem disso. Funcionamento: a instanciação é lazy (só o que é usado), e tipos são deduzidos em argumentos (`std::max(a, b)` sem `<int>`).

SFINAE (Substitution Failure Is Not An Error): durante a dedução de overload, uma substituição inválida nos parâmetros de template não é erro fatal — apenas remove essa candidata. Antes de `requires` (C++20), era a técnica para selecionar comportamento por propriedade de tipo. Idiomas modernos: use `std::enable_if` (legado), `if constexpr` (C++17, ramo descartado em tempo de compilação — a melhor ferramenta para 'quando o tipo suporta X'), e conceitos `requires` (C++20, mensagens de erro legíveis).

`constexpr`/`consteval`/`constinit` movem cálculo para tempo de compilação: `constexpr double c = 3.14159 * 2;`, `constexpr` functions podem rodar tanto em compile-time quanto runtime (C++14 relaxou para loops/if). Compilador precisa evaluar se contexto constante for possível; com `consteval` (C++20) a avaliação é obrigatória.

Armadilhas: erro de template = paredes de texto (mensagens ilegíveis); especialização parcial de funções não existe (use overloads); os nomes dependentes precisam de `typename`/`template`; `auto` em funções só para expressões simples. Instantiation explosion em templates pesados (`std::variant`, visitantes) pode inflar binário. Padrões produtivos: restringir com conceitos, usar `std::array` com `constexpr` tamanho, meta-programação para dispatch em tempo de compilação (tag dispatch, type traits). Quando usar: containers, algoritmos, bibliotecas genéricas, serialização, e hot paths onde vir-tual calls (vtables) custariam demais.
## Conexoes

- [[c-move-semantics-rvalue-references-e-ownership]]
- [[c-raii-e-gerenciamento-de-recursos]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]