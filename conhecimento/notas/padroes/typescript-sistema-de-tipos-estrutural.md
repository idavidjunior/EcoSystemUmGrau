---
tags: [compatibilidade, extra, padrao, passam, sólido, typescript]
aliases: [TypeScript: sistema de tipos estrutural]
date: 2026-08-20
---

# TypeScript: sistema de tipos estrutural

**Fonte:** typescript

TypeScript é um superset tipado de JavaScript, compilado com `tsc`. O sistema de tipos é ESTRUTURAL (duck typing em nível de tipos): dois tipos são compatíveis se têm a mesma forma, não o mesmo nome nominal. `interface Person { name: string }` aceita qualquer objeto com `name: string` — isso permite interoperar com JSON e bibliotecas JS sem adaptadores.

Conceitos centrais:
- `interface` e `type` (alias) são intercambiáveis na maioria dos casos; `interface` é extensível por declaração (declaration merging) e é preferida para APIs públicas; `type` serve para uniões, mapeados e tipos condicionais.
- Tipos primitivos: `string, number, boolean, null, undefined, symbol, bigint, void, never, unknown, any`. `void` é retorno sem valor; `never` é tipo de função que nunca retorna (throw, loop infinito) e do braço exaurido de uniões.
- `unknown` é o anti-`any`: aceita tudo, mas exige narrowing antes de usar; `any` desliga a checagem — use apenas em migração.
- `strict: true` no tsconfig liga `strictNullChecks` (null/undefined só entram se declarados) — não existe sistema de tipos sólido sem ele.

Armadilhas:
- Excess property check: objetos literais recebem checagem de propriedades extras, mas variáveis tipadas passam por compatibilidade estrutural sem essa checagem — `const x = { extra: 1 }; use(x)` compila mesmo com shape esperado menor.
- `readonly` não existe em runtime — apenas em tipo; modifica a instância ignorando.
- Enum numérico vaza como objeto em runtime; para strings com union de literais é mais previsível: `type Dir = 'up' | 'down'`.
- `==` não existe com enums numéricos de forma segura; preferir constantes.

Melhores práticas: ative `strict` sempre; prefira `interface` para shape de objetos públicos e `type` para uniões; use `satisfies` (TS 4.9+) para validar shape mantendo o tipo literal; `const` assertions (`as const`) para literais imutáveis. O poder está em combinar: unions, generics e index signatures com `unknown` + narrowing. Sempre que um valor vier de fora (fetch, inputs), assuma `unknown` e faça narrowing com guards.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[typescript-generics-e-tipos-condicionais]]
- [[typescript-type-narrowing-guards-e-type-assertions]]