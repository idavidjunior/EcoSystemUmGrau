---
tags: [combinadas, fechadas, hierarquias, interface, kotlin, padrao]
aliases: [Kotlin: null-safety e sistema de tipos]
date: 2026-08-22
---

# Kotlin: null-safety e sistema de tipos

**Fonte:** kotlin

## Conceitos centrais

Kotlin tem **null-safety no tipo**: `String?` pode ser nulo, `String` não. O compilador impõe checagens (flow typing): `if (x != null) x.length` compila. O operador `?.` é safe-call: `a?.b` retorna `null` se `a` for nulo. `!!` força dereferência e lança `NullPointerException` — é *code smell* se aparecer fora de testes/interoperabilidade com Java mal anotado. `?:` é o *elvis*: `x ?: default` fornece fallback. `val v: String? = s as? String` (safe-cast `as?`) evita `ClassCastException`.

O sistema de tipos inclui: **`Unit`** (como `void`, mas valor real), **`Nothing`** (subtipo de tudo, para funções que nunca retornam — `throw`, `error()`), **`Any`/`Any?`** (raiz do tipo), e **inferência**. Classes podem ser `data class` (equal/hashCode/toString/copy) e `sealed class`/`sealed interface` para hierarquias fechadas combinadas com `when` exaustivo.

## Idioms

- `val result = x?.transform() ?: fallback` compõe null-safety de forma pipeline.
- `when` exaustivo sobre `sealed`/`enum` dispensa `else`; o compilador avisa se faltar branch.
- `String?.let { ... }` executa bloco só se não-nulo.

## Armadilhas

- Interoperabilidade Java: tipos **platform** (`String!`) podem ser nulos sem aviso — a JVM não impõe checagem; verifique anotações `@Nullable`/`@NotNull` ou seja defensivo em fronteiras.
- `!!` em código de produção é a fonte #1 de NPE "surpresa" — prefira `?.`/`?:`.
- Generics: `List<T>` é **read-only**, não imutável — pode ser uma `MutableList` disfarçada; `toList()` copia.
- `Any` não é `Any?`: passar `Any` nulo compila em alguns contextos — teste bem fronteiras com bibliotecas.

## Boas práticas

- Marque parâmetros/retornos como `?` apenas quando realmente opcionais; null como estado "ausente" vira propagaçao de bugs.
- Prefira `data class` + cópia imutável (`copy`) a mutação de campos.
- Ative Kotlin compiler `-Xexplicit-api` para forçar visibilidade explícita em bibliotecas.
## Conexoes

- [[cluster-hub-programacao]]
- [[kotlin-corrotinas-e-concorrência-estruturada]]
- [[kotlin-funções-propriedades-e-data-classes]]
- [[padrao-hub-padroes]]