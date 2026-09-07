---
tipo: episodio
tags: [sandbox, docker, implementacao, seguranca]
data: 2026-09-07
contexto: implementação do sandbox isolado com Docker preferencial
decisao: eco_sandbox com executar e degradado mais imagem multi-stage não-root
impacto: agentes ganham base segura com auditoria e limites rígidos
---

O cliente vive em scripts e eco sandbox. Ele valida antes de rodar.
Ele prefere Docker com rede desligada e limites duros. Sem Docker ele degrada com alerta.
A imagem usa base travada e usuário comum e entrypoint explícito.
O EcoClient ganhou sandbox executar sem quebrar a API antiga.
O teste de fumaça passou em modo degradado neste host.

## Conexoes

- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]