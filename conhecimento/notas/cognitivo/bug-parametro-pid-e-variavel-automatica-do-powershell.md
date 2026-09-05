---
tags: [cognitivo, general, int, proprio, quebrando, referenciava]
aliases: [Bug: parametro Pid e variavel automatica do PowerShell]
date: 2026-08-06
---

# Bug: parametro Pid e variavel automatica do PowerShell

**Dominio:** general

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
- Teste seco: processo supervisionado (pai vivo) -> 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]