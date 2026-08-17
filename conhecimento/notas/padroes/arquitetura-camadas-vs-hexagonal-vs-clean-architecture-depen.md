---
tags: [arquitetura, compondo, composition, padrao, raiz, root]
aliases: [Arquitetura: camadas vs hexagonal vs clean architecture — de]
date: 2026-08-17
---

# Arquitetura: camadas vs hexagonal vs clean architecture — dependência de dentro para fora

**Fonte:** arquitetura

Arquitetura em camadas (layered): presentation → application → domain → infrastructure, com dependências fluindo de cima para baixo. Simples e familiar, mas vira vazamento quando a camada de dados vaza para a interface ou o domínio depende de infraestrutura concreta. O acoplamento típico a ORM, HTTP e banco nas camadas superiores dificulta teste e evolução.

Hexagonal (ports & adapters) corrige a direção: o domínio está no centro, protegido por *ports* (interfaces) — ex.: `OrderRepository`, `PaymentGateway`. *Adapters* concretos (Postgres, Kafka, REST controller) implementam esses ports na borda. A inversão de dependência garante que o núcleo não saiba de tecnologias: ele apenas declara o que precisa e o que oferece. Resultado: domínio testável com fakes, substituição de infraestrutura sem tocar no núcleo.

Clean architecture é o mesmo princípio generalizado em anéis concêntricos (entities, use cases, adapters, frameworks). Regra de ouro: as dependências de *código-fonte* apontam sempre para dentro; nada no anel interno pode conhecer o externo. Use cases (casos de uso) carregam a regra de aplicação; entidades carregam a regra de negócio. Frameworks ficam na borda — banco, web, filas são detalhes de implementação, trocáveis.

Na prática: não precisa dos anéis completos do livro. O essencial é (1) domínio puro, sem dependências externas, (2) interfaces definidas pelo consumidor (inside-out), (3) injeção de dependência compondo na raiz (composition root), (4) infraestrutura fora do núcleo. Custo: indireção extra e mais arquivos. Valor: testabilidade, velocidade de mudança e vida útil do código de negócio. Aplique onde a regra de negócio é o ativo — não em CRUD simples.
## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]