---
tags: [base, bloco, checks, padrao, padrão, typescript]
aliases: [TypeScript: type narrowing, guards e type assertions]
date: 2026-08-15
---

# TypeScript: type narrowing, guards e type assertions

**Fonte:** typescript

Narrowing é o processo de reduzir um tipo amplo (union) a um mais específico dentro de um bloco, com base em checks de controle de fluxo. O TypeScript acompanha o narrowing a partir de `if`, `switch`, `typeof`, `instanceof`, `in`, truthiness e chamadas a type guards.

Técnicas:
- `typeof x === 'string'` estreita primitivos; `Array.isArray(x)` para arrays; `instanceof Date`/`instanceof MyClass` para classes; `'prop' in obj` para discriminar uniões de objeto.
- Discriminated unions: `type Shape = { kind: 'circle'; r: number } | { kind: 'rect'; w: number; h: number }` — o campo literal `kind` é o discriminador; `switch (s.kind)` estreia cada caso automaticamente.
- Type guards próprios: funções com assinatura de predicado `function isFish(x: Pet): x is Fish` — o TS confia nesse retorno booleano para estreitar no call site.
- Truthiness: `if (str)` estreia de `string | undefined` para `string` (mas cuidado com `''` e `0`).
- Assertion functions (`asserts x is T`) — nunca retornam, lançam se inválidas; útil em validação de entrada.

Type assertions (`as`): declaram que VOCÊ sabe mais que o compilador; `x as string` ou `x as unknown as number` (double assertion via unknown para cruzar tipos incompatíveis). `!` (non-null assertion) é `x!` — afirma não-null. São ferramentas de escape: usar demais sinaliza modelagem fraca. `satisfies` valida sem alterar o tipo inferido.

Armadilhas:
- `typeof` em `null` retorna 'object' — `typeof x === 'object'` não exclui null.
- Narrowing por `typeof` não funciona para tipos de objeto — precisa de guard ou `in`.
- `as` não é checado em runtime; se o dado real divergir, você terá um erro de runtime em vez de compile-time. Prefira guard em dados externos.
- Variáveis capturadas em closures podem perder narrowing (controle de fluxo entre frames).

Melhores práticas: projete uniões discriminadas para dados de múltiplos formatos; use guards para fronteiras (JSON, fetch, form input) e `unknown` + narrowing como caminho padrão de entrada; reserve `as` para a última fronteira (interop com libs sem tipos); use `satisfies` para validar estrutura mantendo literais. Narrowing correto elimina a categoria inteira de bugs 'cannot read property of undefined'.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[typescript-generics-e-tipos-condicionais]]
- [[typescript-sistema-de-tipos-estrutural]]