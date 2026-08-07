param(
    [int]$Interval = 20,
    [string]$BridgePort = "8765",
    [string]$ServePort = "8767",
    [string]$LogPath = "$PSScriptRoot\watchdog_log.txt"
)

$ErrorActionPreference = "SilentlyContinue"

# Instância unica via arquivo de lock com PID (mais robusto que Mutex nomeado:
# um Mutex abandoned no Windows nao e re-adquirido e trava o restart).
$LockPath = "$PSScriptRoot\watchdog.lock"
$meuPid = $PID
$jaExiste = $false
if (Test-Path $LockPath) {
    try {
        $outroPid = [int](Get-Content $LockPath -Raw).Trim()
        $procOutro = Get-Process -Id $outroPid -ErrorAction SilentlyContinue
        if ($procOutro -and $procOutro.ProcessName -match "powershell") {
            $jaExiste = $true
        }
    } catch { }
}
if ($jaExiste) {
    exit 0
}
try { Set-Content -Path $LockPath -Value $meuPid -Encoding ascii } catch { }

# Log com limite de tamanho (~2MB): ao estourar, descarta a metade mais antiga.
if (Test-Path $LogPath) {
    $info = Get-Item $LogPath
    if ($info.Length -gt 2MB) {
        $linhas = Get-Content $LogPath
        $linhas | Select-Object -Skip ([int]($linhas.Count / 2)) | Set-Content $LogPath
    }
}
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true

function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

$env:Path = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot\bin;" + $env:Path
$PYTHON = "C:\Users\David Jr\AppData\Local\Programs\Python\Python312\python.exe"
$WORKDIR = "C:\Users\David Jr\Documents\Default Project"
$SCRIPTS = Join-Path $WORKDIR "EcoSystemUmGrau\scripts"
$OPENCODE_BIN = Join-Path $env:APPDATA "npm\node_modules\opencode-ai\bin\opencode.exe"

# Credenciais do serve (Basic Auth) - mesma origem que a bridge (scripts/.env)
$SERVER_USER = "opencode"
$SERVER_PASS = $env:OPENCODE_SERVER_PASSWORD
if (-not $SERVER_PASS) {
    $envFile = Join-Path $SCRIPTS ".env"
    if (Test-Path $envFile) {
        $linha = Get-Content $envFile | Where-Object { $_ -match '^OPENCODE_SERVER_PASSWORD=' } | Select-Object -First 1
        if ($linha) { $SERVER_PASS = ($linha -replace '^OPENCODE_SERVER_PASSWORD=', '').Trim().Trim('"') }
    }
}
$AUTH_B64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${SERVER_USER}:${SERVER_PASS}"))
$AUTH_HEADERS = @{ Authorization = "Basic $AUTH_B64" }

function Test-BridgeUp { param($Port) (netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port") -ne $null }
function Test-ServeUp {
    param($Port)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/global/health" -Headers $AUTH_HEADERS -UseBasicParsing -TimeoutSec 5
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
    } catch {
        return $false
    }
}
# Health-check do bridge: porta LISTENING + processo dono vivo + escreve no log.
# Se a porta estiver LISTENING com socket orfao (processo morto), reinicia.
function Test-BridgeAlive {
    param($Port)
    $linha = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port" | Select-Object -First 1
    if (-not $linha) { return $false }
    $pidStr = ($linha.ToString() -split '\s+')[-1]
    if ($pidStr -notmatch '^\d+$') { return $false }
    $proc = Get-Process -Id ([int]$pidStr) -ErrorAction SilentlyContinue
    return ($proc -ne $null)
}
function Get-BridgePid {
    param($Port)
    $linha = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port" | Select-Object -First 1
    if (-not $linha) { return $null }
    $pidStr = ($linha.ToString() -split '\s+')[-1]
    if ($pidStr -notmatch '^\d+$') { return $null }
    return [int]$pidStr
}

# =====================================================================
# CERTIFICAÇÃO FORENSE DE LIXO / ÓRFÃO
# ---------------------------------------------------------------------
# Antes de matar QUALQUER processo, o watchdog certifica que ele e lixo
# de verdade. So libera o kill se TODOS os criterios forem atendidos.
# Retorna @{ Liberar = bool; Motivos = [string[]] } - a razao de cada
# criterio falhar ou passar, para auditoria no log.
# =====================================================================
function Test-ForensicoLixo {
    param(
        [int]$ProcessId,
        [string]$NomeEsperado,          # nome do processo (ex.: python, opencode)
        [int]$IdadeMinimaSeg = 30,      # nao mata processo recem-criado
        [int]$PortaListen = $null,      # se definida, o socket orfao desta porta e o alvo
        [string[]]$CaminhoProtegido = @()  # caminhos absolutos intocaveis
    )
    $motivos = New-Object System.Collections.Generic.List[string]
    $libera = $true

    # 1) Processo existe? Se nao existe, nada a fazer (ja morreu).
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) {
        $motivos.Add("processo inexistente (ja morto)")
        return @{ Liberar = $false; Motivos = $motivos.ToArray() }
    }
    # 2) Nome confere com o esperado? Nome diferente = nao e nosso alvo.
    if ($NomeEsperado -and $proc.ProcessName -ne $NomeEsperado) {
        $motivos.Add("nome diverge (esperado '$NomeEsperado', tem '$($proc.ProcessName)')")
        $libera = $false
    }
    # 3) Caminho protegido? Jamais tocar (ex.: desktop).
    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($cim -and $cim.ExecutablePath) {
        foreach ($prot in $CaminhoProtegido) {
            if ($cim.ExecutablePath -match [regex]::Escape($prot)) {
                $motivos.Add("caminho protegido: $($cim.ExecutablePath)")
                $libera = $false
            }
        }
    }
    # 4) Tem janela visivel? Processo com UI ativa NUNCA e lixo.
    if ($proc.MainWindowHandle -ne 0 -or $proc.MainWindowTitle) {
        $motivos.Add("tem janela ativa: '$($proc.MainWindowTitle)'")
        $libera = $false
    }
    # 5) Idade minima: processo recem-iniciado pode ser o que o proprio
    #    watchdog acabou de criar (evita matar o que acabamos de subir).
    $idadeSeg = 0
    try {
        $inicio = $cim.CreationDate
        if ($inicio) {
            $inicioDt = [Management.ManagementDateTimeConverter]::ToDateTime($inicio)
            $idadeSeg = ((Get-Date) - $inicioDt).TotalSeconds
        }
    } catch { }
    if ($idadeSeg -lt $IdadeMinimaSeg) {
        $motivos.Add("recem-criado ($([math]::Round($idadeSeg))s < ${IdadeMinimaSeg}s)")
        $libera = $false
    }
    # 6) Tem processos filhos vivos? Processo com filhos ativos e pai em uso.
    $filhos = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($filhos) {
        $filhosVivos = $filhos | Where-Object {
            (Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue) -ne $null
        }
        if ($filhosVivos) {
            $motivos.Add("tem $($filhosVivos.Count) filhos vivos (atividade real)")
            $libera = $false
        }
    }
    # 7) Tem conexões de rede ativas (nao-listen)? Uso real de rede = nao e lixo.
    $conns = Get-NetTCPConnection -OwningProcess $ProcessId -ErrorAction SilentlyContinue
    $conexoesAtivas = $conns | Where-Object { $_.State -in @("Established", "CloseWait", "TimeWait", "FinWait1", "FinWait2", "SynSent") }
    if ($conexoesAtivas) {
        $motivos.Add("tem $($conexoesAtivas.Count) conexoes de rede ativas (Ex.: $($conexoesAtivas[0].RemoteAddress):$($conexoesAtivas[0].RemotePort))")
        $libera = $false
    }
    # 8) Esta escutando uma porta de SERVIÇO (alem da orfa)? Porta listen com
    #    processo vivo que nao e a porta orfa alvo = servidor em uso, nao matar.
    $connsListen = $conns | Where-Object { $_.State -eq "Listen" }
    foreach ($cl in $connsListen) {
        if ($PortaListen -and $cl.LocalPort -eq $PortaListen) {
            # Esta e exatamente a porta orfa que queremos limpar - permitido.
            $motivos.Add("socket alvo na porta $PortaListen identificado (processo dono vivo)")
        } else {
            $motivos.Add("escutando porta $($cl.LocalPort) (servico possivelmente em uso)")
            $libera = $false
        }
    }
    # 9) Processo pai esta vivo? Sem pai vivo + sem filhos + sem rede + sem janela
    #    = candidato a orfao de verdade. Pai vivo nao desqualifica sozinho, mas
    #    e auditado.
    $pai = $null
    if ($cim) {
        $pai = Get-Process -Id $cim.ParentProcessId -ErrorAction SilentlyContinue
        if ($pai) {
            $motivos.Add("pai vivo: $($pai.ProcessName) (PID $($pai.Id)) - supervisionado")
        } else {
            $motivos.Add("processo pai morto - orfao de verdade")
        }
    }
    # 10) Responde a health-check HTTP? Se servir uma porta e responder, esta vivo.
    if ($PortaListen) {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$PortaListen/global/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($resp -and $resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
            $motivos.Add("responde health-check HTTP na porta $PortaListen")
            $libera = $false
        }
    }
    if (-not $motivos) {
        $motivos.Add("nenhum indicio de atividade - candidato classificado como lixo")
    }
    return @{ Liberar = $libera; Motivos = $motivos.ToArray() }
}

function Invoke-KillCertificado {
    param(
        [int]$ProcessId,
        [string]$Alvo,
        [string]$NomeEsperado,
        [int]$IdadeMinimaSeg = 30,
        [int]$PortaListen = $null,
        [string[]]$CaminhoProtegido = @()
    )
    $veredito = Test-ForensicoLixo -ProcessId $ProcessId -NomeEsperado $NomeEsperado `
        -IdadeMinimaSeg $IdadeMinimaSeg -PortaListen $PortaListen `
        -CaminhoProtegido $CaminhoProtegido
    if ($veredito.Liberar) {
        Write-Log "KILL CERTIFICADO [$Alvo PID $ProcessId]: $($veredito.Motivos -join '; ')"
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        return $true
    } else {
        Write-Log "KILL BLOQUEADO [$Alvo PID $ProcessId]: $($veredito.Motivos -join '; ')"
        return $false
    }
}

Write-Log "Watchdog iniciado (intervalo: ${Interval}s, bridge: $BridgePort, serve: $ServePort)"

while ($true) {

    # ============ BRIDGE ============
    if (Test-BridgeAlive $BridgePort) {
        Write-Log "Bridge OK (PID $(Get-BridgePid $BridgePort))"
    } else {
        if (Test-BridgeUp $BridgePort) {
            # Porta LISTENING mas processo dono nao confere: socket orfao.
            # So limpa com CERTIFICAÇÃO FORENSE completa.
            $orphanPid = Get-BridgePid $BridgePort
            if ($orphanPid) {
                Write-Log "Bridge com socket orfao na porta $BridgePort - certificando processo $orphanPid..."
                Invoke-KillCertificado -ProcessId $orphanPid -Alvo "bridge-orfao" -NomeEsperado "python" -IdadeMinimaSeg 10 -PortaListen $BridgePort -CaminhoProtegido @("opencode-aidesktop")
                Start-Sleep -Seconds 3
            }
        }
        Write-Log "Bridge MORTO na porta $BridgePort - reiniciando..."
        if (Test-Path $PYTHON) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $PYTHON
            $psi.Arguments = "-u `"$SCRIPTS\jarvis_bridge.py`""
            $psi.WorkingDirectory = $SCRIPTS
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Bridge reiniciado (PID: $($p.Id))"
        } else {
            Write-Log "Python nao encontrado em $PYTHON"
        }
    }

    # ============ SERVE (opencode) ============
    $serveUp = Test-BridgeUp $ServePort
    if ($serveUp) {
        $servePid = ((netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$ServePort")[0] -split '\s+')[-1]
        $proc = Get-Process -Id $servePid -ErrorAction SilentlyContinue
        if ($proc -and (Test-ServeUp $ServePort)) {
            $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
            Write-Log "Serve OK (PID $servePid, ${memMB}MB)"
            if ($memMB -gt 800) { Write-Log "ALERTA: Serve com ${memMB}MB - alto consumo" }
        } else {
            # Porta escuta mas sem resposta de health OU processo dono morto.
            # Certifica antes de derrubar (nunca derruba processo em uso).
            Write-Log "Serve na porta $ServePort nao responde health - certificando..."
            if ($servePid -match '^\d+$') {
                Invoke-KillCertificado -ProcessId ([int]$servePid) -Alvo "serve-mau" -NomeEsperado "opencode" -IdadeMinimaSeg 10 -PortaListen $ServePort -CaminhoProtegido @("opencode-aidesktop")
                Start-Sleep -Seconds 2
            }
        }
    } else {
        Write-Log "Serve MORTO na porta $ServePort - iniciando..."
    }
    if (-not (Test-BridgeUp $ServePort)) {
        if (Test-Path $OPENCODE_BIN) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $OPENCODE_BIN
            $psi.Arguments = "serve --port $ServePort"
            $psi.WorkingDirectory = $WORKDIR
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $envVars = @{}
            Get-ChildItem Env: | ForEach-Object { $envVars[$_.Name] = $_.Value }
            $envVars["OPENCODE_SERVER_USERNAME"] = $SERVER_USER
            $envVars["OPENCODE_SERVER_PASSWORD"] = $SERVER_PASS
            $psi.EnvironmentVariables.Clear()
            foreach ($kv in $envVars.GetEnumerator()) { $psi.EnvironmentVariables[$kv.Key] = $kv.Value }
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Serve iniciado (PID: $($p.Id))"
        } else {
            Write-Log "opencode.exe nao encontrado em $OPENCODE_BIN"
        }
    }

    # ============ ORPHANS ============
    # CLÁUSULA PÉTREA: O OpenCode DESKTOP NUNCA pode ser fechado automaticamente.
    # So o usuario, manualmente. Aqui limpamos apenas orfaos do CLI (opencode run),
    # e NUNCA tocamos em processos do desktop (@opencode-aidesktop).
    # Cada candidato passa pela CERTIFICAÇÃO FORENSE: so e morto se for lixo de
    # verdade (sem janela, sem filhos, sem rede, sem pai supervisionando, idoso).
    $desktopPath = "opencode-aidesktop"
    $candidatos = Get-Process -Name "opencode" -ErrorAction SilentlyContinue | Where-Object {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue
        $cmd = $p.CommandLine
        if (-not $cmd) { return $false }
        # Protecao absoluta: qualquer processo do desktop e intocavel.
        if ($cmd -match [regex]::Escape($desktopPath)) { return $false }
        # So avalia CLI: "opencode run" (sessões soltas) - nunca o "serve".
        ($cmd -match "opencode\.exe run")
    }
    $mortos = 0
    $bloqueados = 0
    foreach ($cand in $candidatos) {
        if (Invoke-KillCertificado -ProcessId $cand.Id -Alvo "orphan-cli" -NomeEsperado "opencode" -IdadeMinimaSeg 60 -CaminhoProtegido @("opencode-aidesktop")) {
            $mortos++
        } else {
            $bloqueados++
        }
    }
    if ($candidatos -and ($mortos -gt 0 -or $bloqueados -gt 0)) {
        Write-Log "Orfaos CLI: $mortos mortos, $bloqueados preservados. Desktop intocado."
    }

    Start-Sleep -Seconds $Interval
}

$log.Close()
try { Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue } catch {}
