---
tags: [argumentos, designpatterns, nomeados, padrao, parciais, states]
aliases: [Design patterns: creacionais — factory, builder e por que si]
date: 2026-08-10
---

# Design patterns: creacionais — factory, builder e por que singleton é code smell

**Fonte:** designpatterns

Padrões creacionais desacoplam a criação de objetos da lógica que os usa — o consumidor depende da *forma* de criar, não de construtores concretos acoplados.

**Factory Method**: define uma interface de criação na qual as subclasses decidem a classe instanciada (`TransporteFactory.criar()` → `Caminhao`/`Navio`). Use quando o tipo exato depende de contexto em runtime. **Abstract Factory**: famílias de objetos relacionados (tema UI, conectores de banco) criados por uma factory que garante compatibilidade entre eles. **Builder**: constrói objetos complexos passo a passo, separando a construção da representação — ótimo para objetos com muitos parâmetros opcionais, argumentos nomeados ou states parciais. Compare com o anti-pattern **telescoping constructor** (sobrecargas `Widget(a)`, `Widget(a,b)`, ...). Regra: builder quando houver validação por etapas ou parâmetros opcionais demais; factory quando houver lógica de seleção de implementação.

**Singleton**: garante instância única global. **É um code smell** por três razões: esconde dependências (qualquer código chama `Database.getInstance()` sem declará-lo), dificulta teste (estado global imutável entre testes, fakes difíceis) e acopla ao concreto. Trate singleton como *problema de lifetime*, não de acesso: a instância única deve ser criada no composition root e **injetada** como dependência (DI), com escopo singleton definido pelo container. Singleton só se justifica como pattern quando o recurso é realmente único e não injetável (ex.: um lock, um logger no processo).

Decisão prática: prefira construtores simples; suba de complexidade na ordem construtor → static factory → builder → factory. Sempre injete dependências; nunca acesse singletons globais. Prefira injeção do container para lifetime único, mantendo as classes testáveis.
## Conexoes

- [[cluster-hub-programacao]]
- [[design-patterns-anti-patterns-comuns-god-object-service-loca]]
- [[design-patterns-comportamentais-strategy-observer-template-m]]
- [[design-patterns-estruturais-adapter-facade-e-decorator]]
- [[design-patterns-solid-e-como-os-padrões-gof-derivam-dele]]
- [[padrao-hub-padroes]]