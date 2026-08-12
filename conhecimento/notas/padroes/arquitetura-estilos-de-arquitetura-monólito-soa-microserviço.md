---
tags: [arquitetura, god, integração, object, padrao, virar]
aliases: [Arquitetura: estilos de arquitetura — monólito, SOA, microse]
date: 2026-08-12
---

# Arquitetura: estilos de arquitetura — monólito, SOA, microserviços e serverless

**Fonte:** arquitetura

O monólito é o ponto de partida correto para quase todo sistema novo: um único processo, deploy único, transações locais e simplicidade de razão. Seus trade-offs: acoplamento entre módulos, escalabilidade vertical limitada e deploy que afeta o sistema inteiro. SOA (Service-Oriented Architecture) organiza a aplicação em serviços de negócio fracamente acoplados, tipicamente expostos via ESB, com contratos (WSDL/SOAP) e orquestração central — funciona bem em corporações com sistemas legados heterogêneos, mas o ESB tende a virar um god object de integração.

Microserviços escalam o desacoplamento para granularidade de negócio: cada serviço tem banco, pipeline de deploy e ownership próprios. Ganhos: escala seletiva, liberdade tecnológica, equipes autônomas (reverse Conway). Custos: consistência distribuída, complexidade de rede, observabilidade obrigatória, versionamento de contratos e dificuldade de transações. Regra prática: comece monolítico e extraia serviços (strangler fig) quando houver fronteira de domínio clara, equipe independente e causa real — nunca por modismo.

Serverless (FaaS) vai ao extremo da elasticidade e da abstração de infraestrutura: cobrança por execução, escala automática e zero provisionamento. É excelente para eventos intermitentes, filas e workloads bursty. Trade-offs: cold start, vendor lock-in, limites de timeout/memória, statelessness obrigatório e custo imprevisível sob pico sustentado.

Decisão prática: escreva o plano de trade-offs (consistência vs disponibilidade, custo vs latência, acoplamento vs autonomia) antes de escolher. A maioria dos sistemas é hibrida: monólito modular + filas + funções serverless pontuais. Prefira arquitetura que minimize o *custo de mudança*, não a que parece mais moderna.
## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]