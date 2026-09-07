# Registro manual do tick periódico da agenda no schtasks.
# PASSO MANUAL: execute este script uma vez como administrador se quiser
# o tick automático a cada minuto. Ele NÃO é executado sozinho.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\agenda_tick_register.ps1
$raiz = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { Write-Error "python não encontrado no PATH"; exit 1 }
$acao = New-ScheduledTaskAction -Execute $python -Argument "scripts\eco_agenda.py tick" -WorkingDirectory $raiz
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$conf = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "EcoSystemAgenda" -Action $acao -Trigger $gatilho -Settings $conf -Description "Tick da agenda do EcoSystemUmGrau (a cada 1 min)" -Force
Write-Output "EcoSystemAgenda registrada. Verifique com: schtasks /query /tn EcoSystemAgenda"
