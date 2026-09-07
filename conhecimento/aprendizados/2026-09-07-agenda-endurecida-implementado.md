---
tipo: episodio
tags: [agenda, seguranca, idempotencia, retry, watchdog]
data: 2026-09-07
contexto: endurecimento da agenda protótipo como infraestrutura automática
decisao: caminho com realpath contido mais disparo com estados e retry e watchdog
impacto: agenda vira infra confiável com tick periódico e recuperação de crash
---

O escape com ponto ponto barra foi fechado com realpath.
O disparo grava running antes de executar a ação real.
O retry repete transitória com espera exponencial e teto.
O órfão após crash vira falha com motivo no tick seguinte.
O loop com prova de vida alimenta o watchdog de inatividade.
O registro no schtasks ficou como passo manual documentado.

## Conexoes

- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]