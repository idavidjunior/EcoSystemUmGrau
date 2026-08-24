---
tipo: erro
tags: [vigilante, sinapses, powershell, timer, evento, resiliencia]
data: 2026-08-23
contexto: Ciclo das Sinapses Vivas não disparava há 32h; marcador runtime/sinapses/ultimo_ciclo.txt parado em 22/08 15:23.
decisao: |
  Duas falhas encadeadas:
  1. O processo do vigilante (PID 7788) morreu em silêncio — sem log de erro,
     coerente com as mortes por pressão de memória desta máquina (4GB, mesma
     causa dos daemons Gradle).
  2. Mesmo com o processo vivo, Register-ObjectEvent + System.Timers.Timer não
     entrega a Action enquanto o runspace está bloqueado no while+Start-Sleep;
     o tick das 23:48 passou em branco.
  Correção: checagem das Sinapses movida PARA DENTRO do loop principal do
  vigilante (mesmo padrão determinístico do resto do script), com o gate de 24h
  num if simples. Vigilante reiniciado via Start-ScheduledTask EcoSystemVigilante.
impacto: |
  Ciclo provado em produção às 23:58:26 ("[OK] nenhuma lacuna pendente" +
  ciclo de vida decay/reindex/relatório; marcador atualizado). O laço automático
  Sinapses agora não depende mais de eventos de timer. Observação aberta: a
  tarefa agendada vem reencarnando o vigilante com PIDs novos (5348/7904/10952
  em ~2 min); LastTaskResult=15 sugere RestartOnFailure — vale auditar depois.
---

# Timer de evento do PowerShell não entrega; loop principal sim

## Sintomas
- Marcador `ultimo_ciclo.txt` congelado; nenhum "SINAPSES:" novo no `.vigilante.log`.
- Processo do vigilante às vezes nem existia mais (morte silenciosa).

## Diagnóstico
`Register-ObjectEvent $timer "Elapsed" -Action {...}` enfileira o evento, mas a
Action só roda quando o runspace libera o pipeline. Com `while($true){Sleep 10}`
a entrega fica indefinida na prática. Além disso, processo host pode morrer sem
deixar rastro nesta máquina com RAM no limite.

## Correção aplicada (scripts/vigilante.ps1)
```powershell
while ($true) {
    try {
        $ultima = if (Test-Path $marcador) { (Get-Item $marcador).LastWriteTime } else { [datetime]::MinValue }
        if (((Get-Date) - $ultima).TotalHours -ge 24) { & $onSinapsesCiclo }
    } catch { Write-Log "SINAPSES loop: erro: $_" }
    Start-Sleep -Seconds 10
}
```

## Evidência
```
[23:58:26] SINAPSES: destilacao de lacunas iniciando...
[23:58:27] SINAPSES destilar: [OK] nenhuma lacuna pendente
[23:58:27] SINAPSES: ciclo de vida iniciando (decay + reindex + relatorio)...
```
