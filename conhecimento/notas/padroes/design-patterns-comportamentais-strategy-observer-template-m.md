---
tags: [autorização, debitar, designpatterns, explícitas, notificar, padrao]
aliases: [Design patterns: comportamentais — strategy, observer, templ]
date: 2026-08-22
---

# Design patterns: comportamentais — strategy, observer, template method e state

**Fonte:** designpatterns

Padrões comportamentais distribuem responsabilidade e algoritmos entre objetos, tornando o comportamento extensível sem reescrever a classe.

**Strategy**: encapsula uma família de algoritmos em classes intercambiáveis com interface comum — `CalculoImposto` com implementações `ICMS`, `ISS`, `PIS`; o contexto escolhe em runtime. Elimina condicionais gigantes (`switch`/`if-else` de tipo) e facilita testar cada algoritmo isoladamente. Use com factory para escolher a estratégia.

**Observer**: define dependência um-para-muitos — quando o sujeito muda, todos os observadores são notificados automaticamente (`EventEmitter`, `Subject`/`Observer`, hooks de UI, listeners). Ideal para propagar mudanças de estado sem acoplar o produtor aos consumidores. Cuidados: notificação síncrona pode acoplar a latência; memory leaks por observadores não removidos; ordem de notificação raramente deve importar — se importa, é outro pattern. Em arquiteturas event-driven, domain events desempenham papel análogo.

**Template Method**: define o esqueleto de um algoritmo em uma classe base, delegando passos específicos (hooks) às subclasses — `ProcessarPagamento` fixa fluxo (validar, autorizar, debitar, notificar) e subclasses variam a autorização. É herança para reuso: base fixa o invariante, subclasse variam os pontos de variação. Diferença do strategy: template usa herança (varia partes dentro de um fluxo fixo), strategy usa composição (troca o algoritmo inteiro). Prefira strategy quando a variação é o algoritmo; template quando o fluxo é fixo.

**State**: o objeto muda de comportamento conforme muda seu estado interno, parecendo trocar de classe — `Pedido` em estados `Pendente`, `Pago`, `Enviado`, `Cancelado`, cada um uma classe com transições explícitas. Elimina condicionais de estado espalhadas e torna transições inválidas impossíveis (máquina de estados). Use em workflows e máquinas de estado; combine com pattern State Machine para validação de transições.
## Conexoes

- [[cluster-hub-programacao]]
- [[design-patterns-anti-patterns-comuns-god-object-service-loca]]
- [[design-patterns-creacionais-factory-builder-e-por-que-single]]
- [[design-patterns-estruturais-adapter-facade-e-decorator]]
- [[design-patterns-solid-e-como-os-padrões-gof-derivam-dele]]
- [[padrao-hub-padroes]]