---
tags: [arquitetura, correlação, exige, padrao, trace, transversal]
aliases: [Arquitetura: event-driven e mensageria — filas, tópicos e co]
date: 2026-08-23
---

# Arquitetura: event-driven e mensageria — filas, tópicos e consistência eventual

**Fonte:** arquitetura

Arquitetura event-driven desacopla produtores de consumidores: um evento é um fato do passado (`PedidoPago`, `EstoqueBaixo`), imutável, publicado sem saber quem consome. Duas primitivas: **fila** (one-to-one, competição entre consumidores — Kafka partitions, RabbitMQ queue) para jobs e trabalho assíncrono; **tópico/pub-sub** (one-to-many, fan-out) para notificações de domínio.

Benefícios: escalabilidade horizontal, resiliência (consumidor indisponível não derruba produtor), desacoplamento temporal e evolução independente. Custos: consistência eventual, mensagens fora de ordem, duplicação, dead-letter queues, e difícil depuração transversal (exige correlação de trace).

Padrões obrigatórios:
- **At-least-once** é o padrão dos brokers modernos (Kafka, SQS): o consumidor precisa de **idempotência** para tolerar reentregas.
- **Outbox pattern**: para publicar eventos junto com a transação no mesmo banco — escreve na tabela `outbox` na mesma transação do estado; um relay publica ao broker. Evita o problema do *dual write* (banco + broker fora de sincronia).
- **Saga / process manager**: orquestra (central) ou coreografa (distribuída) transações longas entre serviços; compensação para desfazer passos.
- **Transactional outbox + idempotent consumer + DLQ** é a tríade que sustenta confiabilidade.

Regras práticas: nomeie eventos no passado (nome do substantivo + verbo no particípio); versionne o schema (`PedidoCriadoV2`) e aceite coevolução de consumidores; não publique eventos de infraestrutura (tabela alterada) como eventos de domínio; defina TTL e política de DLQ; monitore lag e dead-letter. Lembre-se: event-driven não elimina transações — move o problema para idempotência e compensação.
## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]