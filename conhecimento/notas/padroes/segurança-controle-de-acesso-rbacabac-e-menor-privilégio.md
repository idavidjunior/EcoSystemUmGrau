---
tags: [delete, específicos, padrao, schemas, seguranca, update]
aliases: [Segurança: controle de acesso — RBAC/ABAC e menor privilégio]
date: 2026-08-15
---

# Segurança: controle de acesso — RBAC/ABAC e menor privilégio

**Fonte:** seguranca

Autorização decide o que um sujeito autenticado pode fazer sobre um recurso. Sem um modelo explícito, cada endpoint inventa sua regra e a superfície de erro explode (OWASP #1: broken access control).

**Modelos:** RBAC (Role-Based Access Control) — usuários têm roles, roles têm permissões (ex.: `editor`, `admin`). Simples, auditável, mas explode em empresas com muitos papéis. ABAC (Attribute-Based Access Control) — decisões por atributos do sujeito, recurso, ação e contexto (ex.: `department == finance && resource.region == user.region && time within business_hours`). Flexível, mas exige PDP/PEP bem projetados para não virar caixa preta. ReBAC (Relationship-Based, Google Zanzibar) — autorização por grafo de relações (ex.: \"editor do documento X\"), ideal para multitenancy colaborativa.

**Princípio do menor privilégio (PoLP):** cada identidade (humano ou máquina) recebe o mínimo necessário para operar, nada mais. No banco: app conecta com usuário sem DDL e sem privilégios além do necessário (`SELECT/INSERT/UPDATE/DELETE` em schemas específicos); em infra: IAM roles por serviço (não conta root compartilhada); em código: permissões default-deny, nunca allow-all com exceção.

**Na prática:** 1) um único ponto de decisão (middleware/guard) que valida toda request; 2) decisão no servidor sempre — nunca confie em `isAdmin` vindo do cliente; 3) verifique permissão de dono em acessos a objetos (IDOR: `/api/orders/123` deve checar se `order.user_id == session.user_id`); 4) deny-by-default: só permite o que existe em allowlist; 5) ações sensíveis exigem reautenticação/confirmação; 6) audite e logue negações (acesso negado é sinal de scan); 7) teste negativo: fluxo de usuário sem permissão tentando caminhos alternativos (métodos HTTP, IDs de outros tenant).

**Organização:** separe autenticação de autorização; centralize a política (Policy as Code com OPA/Cedar/Rebeccca); revogue acesso em offboarding (automático via IAM lifecycle); nunca deixe herança implícita de permissões por grupo sem revisão periódica (entitlement review). Menor privilégio também vale para segredos, builds e CI: cada job acessa só o que precisa.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]