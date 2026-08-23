---
tags: [chamadas, inicialização, kotlin, mapas, padrao, segura]
aliases: [Kotlin: funções, propriedades e data classes]
date: 2026-08-22
---

# Kotlin: funções, propriedades e data classes

**Fonte:** kotlin

## Conceitos centrais

Kotlin favorece **expressões e concisão**: `if`, `when`, `try` são expressões com valor. Funções têm **argumentos nomeados** e **defaults**, eliminando sobrecargas; `fun foo(a: Int = 1, b: String = 'x')`. **Extension functions** adicionam comportamento a tipos existentes sem herança: `fun String.shout() = uppercase() + '!'`. **`data class`** gera `equals`, `hashCode`, `toString`, `copy()` e `componentN()` (para destructuring). **Propriedades** encapsulam campos com `get()`/`set()` customizados e *backing field* `field`.

**Destructuring**: `val (name, price) = produto` usa `component1()`/`component2()` — funciona com data classes, `Pair`/`Triple`, e mapas. **`when`** sobre expressões: `when (x) { 0 -> 'zero'; in 1..10 -> 'baixo'; else -> 'alto' }`. **Higher-order**: funções recebem/retornam funções — `list.filter { it > 5 }.map { it * 2 }`. Trailing lambda permite `build { }` DSL-like com receivers (`fun build(block: Builder.() -> Unit)`).

## Idioms

- `apply` (configuração), `let` (transformação/null-check), `run` (cálculo), `also` (efeito colateral), `with` (agrupar chamadas).
- `sealed interface Result<T>` com `when` exaustivo para modelar sucesso/erro sem exceções.
- Companion object para estáticos: `companion object { const val TAG = 'App' }` — `const val` só para primitivos/String.

## Armadilhas

- **Sobrecarga de inline/optimization**: `inline` reduz overhead mas aumenta tamanho do bytecode; aplique só com `reified` ou lambdas pesadas.
- `lateinit var` não pode ser `null`, mas acessar antes de inicializar lança `UninitializedPropertyAccessException` — prefira `val by lazy {}` para inicialização segura.
- Data class sobre classes com campos não-`data`: `copy()`/`equals` só cobrem os parâmetros do constructor.
- Extension functions não são métodos reais — resolução é estática: não há *override* dinâmico, apenas shadowing por classe.

## Boas práticas

- Use `data class` para DTOs/valores imutáveis e `copy()` para evolução; evite herança (classes são `final` por padrão).
- Destructuring de `Map`/`Pair` só quando a semântica for clara — legibilidade primeiro.
- Mantenha escopo de extensions pequeno e bem nomeado para não poluir APIs públicas.
## Conexoes

- [[cluster-hub-programacao]]
- [[kotlin-corrotinas-e-concorrência-estruturada]]
- [[kotlin-null-safety-e-sistema-de-tipos]]
- [[padrao-hub-padroes]]