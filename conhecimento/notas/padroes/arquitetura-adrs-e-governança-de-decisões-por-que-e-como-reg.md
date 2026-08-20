---
tags: [aceito, arquitetura, off, padrao, qual, trade]
aliases: [Arquitetura: ADRs e governança de decisões — por que e como ]
date: 2026-08-20
---

# Arquitetura: ADRs e governança de decisões — por que e como registrar

**Fonte:** arquitetura

Architecture Decision Record (ADR) é um documento curto e versionado que registra uma decisão arquitetural, seu contexto e suas consequências. O objetivo não é burocracia — é preservar o *porquê*: seis meses depois, quem herda o sistema precisa saber por que a equipe escolheu microserviços com Kafka em vez de monólito com jobs, e qual trade-off foi aceito.

Formato mínimo (Michael Nygard / ADR template):
- **Status**: proposed → accepted / deprecated / superseded (ADR é imutável; decisões superadas geram novo ADR que referencia o antigo).
- **Context**: o problema e as forças em jogo (restrições, precedentes, fatos), sem opinião.
- **Decision**: a decisão em si, em voz ativa e concreta, citando alternativas consideradas.
- **Consequences**: o que fica mais fácil e o que fica mais difícil — positivo e negativo, honesto.

Onde versionar: no mesmo repositório do código (padrão `docs/adr/NNNN-titulo.md`), versionado junto com o sistema, revisado em pull request — decisão próxima do código que ela afeta.

Boas práticas de governo: apenas decisões *significativas e difíceis de reverter* viram ADR (banco, framework, estilo de arquitetura, padrão de consistência); decisões triviais não. Arquitetos definem a **zona de padronização** (o que é obrigatório — ex.: observabilidade, segurança, formato de evento) e delegam o resto a padrões locais e guidelines. Estabeleça *guardrails* (formato de contrato, padrão de resiliência, limites de acoplamento) que a automação verifica, em vez de revisão manual subjetiva.

Governação leve: um ADR novo exige dono e prazo; revisão periódica (quarterly) de decisões deprecated; registro de decisões rejeitadas com o porquê. Evite: ADR longo demais, decisão registrada depois de implementada sem contexto real, e ausência de consequências.
## Conexoes

- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]