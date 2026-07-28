#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EcoSystemUmGrau - Comandos centralizados do ecossistema.
.DESCRIPTION
    ecosystem sync   → pull + push forcado em EcoSystemUmGrau e LER
    ecosystem scan   → varre projetos Android e extrai patterns/conhecimento
    ecosystem repair → reconstrói knowledge graph dos aprendizados crus + limpa runtime
    ecosystem status → status completo de todos os componentes
    ecosystem help   → esta ajuda
.EXAMPLE
    ecosystem sync
    ecosystem scan
    ecosystem repair
    ecosystem status
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("sync", "scan", "repair", "status", "help")]
    [string]$Command = "help"
)

$ecoDir = "C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau"
$lerDir = "$ecoDir\ler-runtime"
$projectsDir = "C:\Users\Playtec-bancada\Desktop\Codigos\Android"
$learnDir = "$ecoDir\conhecimento\aprendizados"

function Write-Step { param($Msg) Write-Host "`n>>> $Msg" -ForegroundColor Cyan }
function Write-OK   { param($Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Info { param($Msg) Write-Host "  [..] $Msg" -ForegroundColor Gray }
function Write-Err  { param($Msg) Write-Host "  [!!] $Msg" -ForegroundColor Red }

# ══════════════════════════════════════════════════════════════════════
# SYNC
# ══════════════════════════════════════════════════════════════════════
function Invoke-Sync {
    Write-Step "Sincronizando EcoSystemUmGrau"
    Push-Location $ecoDir
    git pull --ff-only 2>&1 | ForEach-Object { Write-Info $_ }
    $status = git status --porcelain
    if ($status) {
        $status | ForEach-Object { Write-Info $_ }
        git add -A
        git commit -m "[ecosystem sync] $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        git push
        Write-OK "Commit + push realizado"
    } else { Write-OK "Nada a commitar" }
    Pop-Location

    Write-Step "Sincronizando LER (local)"
    Push-Location $lerDir
    $status = git status --porcelain
    if ($status) {
        $status | ForEach-Object { Write-Info $_ }
        git add -A
        git commit -m "[ecosystem sync] LER - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-OK "Commit local realizado"
    } else { Write-OK "Nada a commitar" }
    Pop-Location

    Write-Step "Consolidando conhecimento"
    $env:PYTHONPATH = "$lerDir;$env:PYTHONPATH"
    python -c "import sys; sys.path.insert(0, r'$lerDir'); from agent.knowledge_consolidator import export_markdown; export_markdown()" 2>&1
    Write-OK "CONHECIMENTO.md atualizado"
}

# ══════════════════════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════════════════════
function Invoke-Scan {
    Write-Step "Scanando projetos em $projectsDir"

    $projects = Get-ChildItem $projectsDir -Directory
    if (-not $projects) { Write-Err "Nenhum projeto encontrado"; return }

    $totalPatterns = 0
    $totalBugs = 0

    foreach ($proj in $projects) {
        Write-Step "Analisando: $($proj.Name)"
        $files = Get-ChildItem $proj.FullName -Recurse -Include "*.kt", "*.java", "*.py", "*.xml", "*.json", "*.ps1", "*.bat" -ErrorAction SilentlyContinue

        # Contagem de arquivos
        $count = ($files | Measure-Object).Count
        Write-Info "$count arquivos de codigo"

        # Bugs conhecidos: TODO, FIXME, HACK
        $todos = $files | Select-String -Pattern "(TODO|FIXME|HACK|XXX)" -SimpleMatch -CaseSensitive -ErrorAction SilentlyContinue
        $bugCount = ($todos | Measure-Object).Count
        if ($bugCount -gt 0) {
            Write-Info "$bugCount marcadores TODO/FIXME/HACK encontrados"
            $todos | Group-Object Filename | Select-Object @{N="Arquivo";E={$_.Name}}, Count | ForEach-Object {
                Write-Info "  $($_.Arquivo): $($_.Count)"
            }
        }

        # Patterns: try-catch, null checks, async patterns
        $patterns = $files | Select-String -Pattern "(catch|try\s*\{|@Override|suspend|\.map\s*\{)" -ErrorAction SilentlyContinue
        $patternCount = ($patterns | Measure-Object).Count
        Write-Info "$patternCount padroes de codigo identificados"

        $totalPatterns += $patternCount
        $totalBugs += $bugCount
    }

    Write-Step "Resumo do scan"
    Write-OK "$($projects.Count) projetos analisados"
    Write-OK "$totalPatterns padroes | $totalBugs marcadores pendentes"

    # Registrar aprendizado automatico
    $date = Get-Date -Format "yyyy-MM-dd"
    $scanFile = "$learnDir\$date-scan-automatico.md"
    $content = @"
# $date - Scan automatico de projetos

## Projetos analisados
$($projects.Count) projetos em $projectsDir

## Metricas
- Marcadores TODO/FIXME/HACK: $totalBugs
- Padroes de codigo: $totalPatterns

## Projetos
$(($projects | ForEach-Object { "- $($_.Name)" }) -join "`n")
"@
    Set-Content -Path $scanFile -Value $content -Encoding UTF8
    Write-OK "Aprendizado registrado: $scanFile"
}

# ══════════════════════════════════════════════════════════════════════
# STATUS
# ══════════════════════════════════════════════════════════════════════
function Invoke-Status {
    Write-Step "Status do Ecossistema"

    # OpenCode
    $ocode = npm list -g opencode-ai 2>&1 | Select-String "opencode-ai"
    if ($ocode) { Write-OK "OpenCode: $($ocode -replace '.*@', 'v')" }
    else { Write-Err "OpenCode: NAO INSTALADO" }

    # Node/Python/Git
    $nodeVer = node --version 2>$null
    $pythonVer = python --version 2>$null
    $gitVer = git --version 2>$null
    Write-OK "Node: $nodeVer"
    Write-OK "Python: $pythonVer"
    Write-OK "Git: $gitVer"

    # Vigilante
    $pidFile = "$env:USERPROFILE\.vigilante.pid"
    if (Test-Path $pidFile) {
        $vigPid = (Get-Content $pidFile -Raw).Trim()
        $proc = Get-Process -Id $vigPid -ErrorAction SilentlyContinue
        if ($proc) { Write-OK "Vigilante: ATIVO (PID $vigPid)" } else { Write-Err "Vigilante: PID encontrado mas morto" }
    } else { Write-Info "Vigilante: INATIVO" }

    # LER
    if (Test-Path "$lerDir\run.py") {
        Write-OK "LER runtime: $(Get-ChildItem "$lerDir\run.py" | Select-Object Length)"
        $graph = Get-ChildItem "$lerDir\knowledge\knowledge_graph.json" -ErrorAction SilentlyContinue
        if ($graph) {
            $patterns = (Get-Content $graph.FullName -Raw | ConvertFrom-Json | Measure-Object).Count
            Write-OK "Knowledge graph: $(($graph.Length / 1KB).ToString('N1')) KB, $patterns entradas"
        }
    } else { Write-Err "LER runtime: NAO ENCONTRADO" }

    # Aprendizados
    $aprendizados = Get-ChildItem $learnDir -Filter "*.md" -ErrorAction SilentlyContinue
    Write-OK "Aprendizados registrados: $(($aprendizados | Measure-Object).Count)"

    # Projetos Android
    $projects = Get-ChildItem "C:\Users\Playtec-bancada\Desktop\Codigos\Android" -Directory -ErrorAction SilentlyContinue
    Write-OK "Projetos Android: $(($projects | Measure-Object).Count)"

    # Git remotes
    Push-Location $ecoDir
    $gitRemote = git remote -v 2>&1 | Select-String "fetch"
    if ($gitRemote) { Write-OK "Git remote: $($gitRemote -replace '\s+.*','')" }
    Pop-Location

    # Config
    $ocodeConfig = Test-Path "$env:USERPROFILE\.config\opencode\opencode.jsonc"
    if ($ocodeConfig) { Write-OK "Config OpenCode: OK" }
    else { Write-Err "Config OpenCode: AUSENTE" }
}

# ══════════════════════════════════════════════════════════════════════
# REPAIR
# ══════════════════════════════════════════════════════════════════════
function Invoke-Repair {
    Write-Step "Reconstruindo knowledge graph dos aprendizados crus"

    $env:PYTHONPATH = "$lerDir;$env:PYTHONPATH"

    # 1. Recreate runtime directories if missing
    Write-Step "Verificando diretorios runtime"
    $runtimeDirs = @("$lerDir\checkpoints", "$lerDir\logs", "$lerDir\memory", "$lerDir\reports", "$lerDir\projects")
    foreach ($dir in $runtimeDirs) {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null; Write-OK "Recriado: $dir" }
    }

    # 2. Check if knowledge_graph.json is valid
    Write-Step "Verificando integridade do knowledge graph"
    $graphFile = "$lerDir\knowledge\knowledge_graph.json"
    if (Test-Path $graphFile) {
        try {
            $graph = Get-Content $graphFile -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-OK "Knowledge graph valido ($(($graph | Measure-Object).Count) entradas)"
        } catch {
            Write-Err "Knowledge graph corrompido! Reconstruindo..."
            Remove-Item $graphFile -Force
        }
    } else {
        Write-Info "Knowledge graph nao encontrado - sera criado"
    }

    # 3. Re-register all aprendizado files
    Write-Step "Re-registrando aprendizados em $learnDir"
    $files = Get-ChildItem $learnDir -Filter "*.md" -ErrorAction SilentlyContinue | Sort-Object Name
    if (-not $files) { Write-Info "Nenhum aprendizado encontrado"; return }

    $count = 0
    $errors = 0
    foreach ($f in $files) {
        try {
            $python = @"
import sys, os, json
sys.path.insert(0, r'$lerDir')
from agent.knowledge_consolidator import register_learning
register_learning(r'$($f.FullName)')
print('OK')
"@
            $result = python -c $python 2>&1
            if ($result -eq "OK") { $count++ } else { throw $result }
        } catch {
            Write-Err "  Falha em $($f.Name): $_"
            $errors++
        }
    }
    Write-OK "$count aprendizados registrados"

    # 4. Export CONHECIMENTO.md
    Write-Step "Exportando CONHECIMENTO.md"
    try {
        python -c "import sys; sys.path.insert(0, r'$lerDir'); from agent.knowledge_consolidator import export_markdown; export_markdown()" 2>&1
        Write-OK "CONHECIMENTO.md atualizado"
    } catch { Write-Err "Falha na exportacao: $_" }

    # 5. Summary
    $newGraph = Get-ChildItem $graphFile -ErrorAction SilentlyContinue
    if ($newGraph) {
        $kbSize = [math]::Round($newGraph.Length / 1KB, 1)
        $entries = (Get-Content $graphFile -Raw -Encoding UTF8 | ConvertFrom-Json | Measure-Object).Count
        Write-OK "Knowledge graph: ${kbSize}KB, $entries entradas"
    }

    if ($errors -gt 0) { Write-Err "$errors erros durante reparo" }
    else { Write-OK "Reparo concluido sem erros" }

    # 6. Git commit
    Write-Step "Versionando reparo"
    Push-Location $ecoDir
    $status = git status --porcelain
    if ($status) {
        git add -A
        git commit -m "[ecosystem repair] $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-OK "Commit realizado"
    } else { Write-OK "Nada a commitar" }
    Pop-Location
}

# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
switch ($Command) {
    "sync"   { Invoke-Sync }
    "scan"   { Invoke-Scan }
    "repair" { Invoke-Repair }
    "status" { Invoke-Status }
    default {
        Get-Help $PSCommandPath -Detailed
        Write-Host "`nUso: ecosystem [sync|scan|repair|status|help]" -ForegroundColor Yellow
    }
}
