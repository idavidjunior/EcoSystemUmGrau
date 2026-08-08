---
tags: [cognitivo, forenses, funcoes, general, processid, read]
aliases: [Bug: parametro Pid e variavel automatica do PowerShell]
date: 2026-08-08
---

# Bug: parametro Pid e variavel automatica do PowerShell

**Dominio:** general

---
tipo: erro
tags: [watchdog, powershell, bug, resiliencia]
data: 2026-08-06
contexto: Certificacao forense de processos no watchdog.ps1 (Test-ForensicoLixo / Invoke-KillCertificado)
decisao: Renomear parametro [int]Pid para [int]ProcessId nas funcoes forenses
impacto: Evita que o watchdog mate o proprio processo (variavel automatica PID read-only)
---

# Bug: parametro Pid e variavel automatica do PowerShell

## Sintoma
A funcao `Test-ForensicoLixo` e `Invoke-KillCertificado` declaravam `[int
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]