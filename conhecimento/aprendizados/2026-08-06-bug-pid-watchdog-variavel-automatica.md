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
A funcao `Test-ForensicoLixo` e `Invoke-KillCertificado` declaravam `[int]$Pid` como
parametro. No PowerShell, `$PID` e uma variavel AUTOMATICA read-only que contem o PID
do processo atual. Com `$ErrorActionPreference = "SilentlyContinue"`, a atribuicao do
parametro falhava em silencio e `$Pid` dentro da funcao referenciava o PID do proprio
watchdog.

## Risco real
O watchdog poderia certificar e matar a SI MESMO (ou o PID errado), quebrando a
resiliencia que deveria proteger.

## Correcao aplicada
- Parametros renomeados para `$ProcessId` em `Test-ForensicoLixo` e `Invoke-KillCertificado`.
- Todas as chamadas no loop atualizadas (`-ProcessId`).
- Tambem corrigido `Write-Log "..." + (array)` que virava argumentos posicionais
  descartados — perdendo a auditoria dos motivos. Agora usa interpolacao.

## Validacao
- Sintaxe: SINTAXE OK (PSParser).
- Teste seco: explorer fingindo ser python -> BLOQUEADO com motivos auditaveis.
- Teste seco: processo supervisionado (pai vivo) -> BLOQUEADO (comportamento conservador).
- Watchdog reiniciado (PID 2172), health-checks bridge/serve OK, desktop intocado (8 procs).
- Teste de resiliencia: serve derrubado -> detectado e reiniciado pelo watchdog em <60s.

## Licao
Em PowerShell, NAO usar `$Pid`/`$PID` como nome de variavel propria: e reservada.
Sempre auditar logs de auditoria em Write-Log com interpolacao, nao concatenacao "+".
