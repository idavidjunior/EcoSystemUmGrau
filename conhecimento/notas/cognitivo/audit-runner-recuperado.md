---
tags: [atômica, cognitivo, escrita, general, resultado, tmp]
aliases: [audit runner recuperado]
date: 2026-08-28
---

# audit runner recuperado

**Dominio:** general

---
tipo: erro
tags: [guardian, auditoria, monitor, audit_runner, widget]
data: 2026-08-28
contexto: system_guardian.py executava scripts/audit_runner.py a cada ~30 min para gerar runtime/audit_result.json e reportar saúde do ecossistema.
decisao: Recriar scripts/audit_runner.py (arquivo referenciado não existia mais), reutilizando audit_eco.run_audit como fonte única e escrevendo o resultado com escrita atômica (tmp + os.replace) no contrato que o guardian lê (timestamp epoch + score + findings
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]