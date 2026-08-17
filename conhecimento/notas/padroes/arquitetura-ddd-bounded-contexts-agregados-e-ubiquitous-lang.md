---
tags: [arquitetura, customer, moderação, padrao, supplier, uso]
aliases: [Arquitetura: DDD — bounded contexts, agregados e ubiquitous ]
date: 2026-08-17
---

# Arquitetura: DDD — bounded contexts, agregados e ubiquitous language

**Fonte:** arquitetura

Domain-Driven Design coloca o domínio de negócio no centro do modelo. Três ideias centrais:

**Ubiquitous language**: vocabulário único e compartilhado entre domínio (negócio) e código — `AprovacaoCredito`, `Pedido`, `EstoqueReservado`. Se a palavra não existe na fala do especialista, não deveria existir no código; traduções terminológicas criam bugs silenciosos.

**Bounded context**: um domínio grande se parte em contextos delimitados (venda, logística, financeiro). Cada contexto tem seu próprio modelo e linguagem — o termo `Cliente` pode ter significados diferentes e versões de dados distintas em cada um. As fronteiras são o que há de mais importante: definem a autonomia de cada subdomínio, modelagem própria e integração explícita. Padrões de integração entre contextos: **anti-corruption layer** (traduz modelos), **open-host service** (API pública), **shared kernel** (modelo compartilhado, uso com moderação), **customer/supplier**.

**Agregado**: cluster de entidades tratado como unidade de consistência. O agregado tem uma **raiz** (aggregate root) que é a única porta de entrada — `Pedido` raiz contendo `ItemPedido`. Toda invariante (regra que deve sempre valer, ex.: total = soma dos itens, ou 'pedido só muda de estado via transições válidas') é protegida dentro do agregado. Regras: transações e consistência dentro do agregado; entre agregados, consistência eventual via eventos de domínio.

Suporte: **value objects** imutáveis para medidas, datas, intervalos (identidade por valor); **domain events** para efeitos colaterais entre agregados; **repositories** que escondem o armazenamento.

Na prática: comece mapeando subdomínios (core, supporting, generic) e bounded contexts; desenhe os agregados em volta das regras de consistência, não das tabelas; não force DDD em CRUD simples — DDD paga onde a regra de negócio é complexa e mutável.
## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]