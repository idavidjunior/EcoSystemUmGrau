---
tags: [awaited, colapsa, padrao, senão, thistype, typescript]
aliases: [TypeScript: generics e tipos condicionais]
date: 2026-08-21
---

# TypeScript: generics e tipos condicionais

**Fonte:** typescript

Generics parametrizam funções e tipos por tipo, preservando a relação entre entradas e saídas: `function identity<T>(x: T): T`. Inferência automática evita anotação manual; type params podem ter constraints (`T extends HasId`). Em funções, `const f = <T,>(x: T): T => x` exige a vírgula em .tsx para o parser distinguir de JSX.

Tipos condicionais (`T extends U ? X : Y`) são o coração da computação de tipos — avaliam assinatura sobre os tipos, não valores. Combinados com infer extraem tipos embutidos:
```typescript
type Unwrap<T> = T extends Promise<infer U> ? U : T;
type Elem<T> = T extends (infer U)[] ? U : never;
```
- Distributividade: condicionais distribuem sobre uniões — `Unwrap<Promise<A> | Promise<B>>` vira `A | B` automaticamente. Para NÃO distribuir, envolva em colchetes: `T extends ...` → `[T] extends [U] ? ...`.
- `infer` só é permitido em `extends` e declara construções para extração (parâmetros de função, retorno, array element).
- Mapped types (`{ [K in keyof T]: T[K] }`) transformam chaves — base de `Partial`, `Readonly`, `Pick`, `Omit`.
- Template literal types (`${K}-${string}`) geram tipos de chaves/rotas dinâmicas.

Utility types essenciais: `Partial, Required, Pick, Omit, Record<K, V>, Exclude, Extract, NonNullable, Parameters, ReturnType, Awaited, ThisType`. Exemplos: `ReturnType<typeof fn>`, `Parameters<typeof fn>`, `Omit<User, 'password'>`.

Armadilhas:
- `infer` dentro de condicional sem usar pode quebrar distribuição — use a variável inferida, senão o tipo colapsa.
- Deep readonly/partial não é automático: `Partial<T>` é raso; mapeados recursivos resolvem para estruturas profundas (ou use bibliotecas como type-fest).
- `keyof` em index signatures retorna o tipo da chave (`string`), não os nomes.
- Generics não são verificados em runtime — `T extends U ?` é checado em COMPILE TIME; valide com guards em runtime.

Melhores práticas: comece pelos utilitários do lib (`type-fest` preenche gaps); evite type-level gymnastics quando um tipo simples resolve; nomes descritivos (`T`, `K`, `R` para convenção); use generics em funções utilitárias de alto reuso (fetch wrappers, stores, transformers).
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[typescript-sistema-de-tipos-estrutural]]
- [[typescript-type-narrowing-guards-e-type-assertions]]