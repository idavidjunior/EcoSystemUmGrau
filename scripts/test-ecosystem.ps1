<#
.SYNOPSIS
    Testes automatizados do ecossistema EcoSystemUmGrau.
.DESCRIPTION
    Verifica todos os componentes criticos e reporta falhas.
    Exit code: 0 = tudo OK, 1 = falhas encontradas.
#>

$passed = 0
$failed = 0
$ecoDir = Split-Path $PSScriptRoot -Parent
$lerDir = "$ecoDir\ler-runtime"

function Test-Pass { param($Name); $script:passed++; Write-Host "  [PASS] $Name" -ForegroundColor Green }
function Test-Fail { param($Name, $Detail); $script:failed++; Write-Host "  [FAIL] $Name : $Detail" -ForegroundColor Red }
function Test-Warn { param($Name, $Detail); Write-Host "  [WARN] $Name : $Detail" -ForegroundColor Yellow }

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Testes do Ecossistema" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ─── 1. Diretorios base ────────────────────────────────────
Write-Host "[1] Diretorios base" -ForegroundColor White
if (Test-Path $ecoDir) { Test-Pass "EcoSystemUmGrau existe" } else { Test-Fail "EcoSystemUmGrau" "Nao encontrado em $ecoDir" }
if (Test-Path "$ecoDir\.git") { Test-Pass "Repo git inicializado" } else { Test-Fail "Git repo" ".git nao encontrado" }

# ─── 2. LER junction ───────────────────────────────────────
Write-Host "[2] LER junction" -ForegroundColor White
$lerLink = "$env:USERPROFILE\.ler"
if (Test-Path $lerLink) {
    $linkType = (Get-Item $lerLink -ErrorAction SilentlyContinue).LinkType
    if ($linkType -eq "Junction") {
        $target = (Get-Item $lerLink).Target
        if ($target -eq $lerDir) { Test-Pass "Junction ~/.ler/ -> ler-runtime/" }
        else { Test-Warn "Junction" "Aponta para $target (esperado: $lerDir)" }
    } else { Test-Warn "$lerLink" "Nao é junction (tipo: $linkType)" }
} else { Test-Fail "~/.ler/" "Nao existe" }

# ─── 3. LER runtime ────────────────────────────────────────
Write-Host "[3] LER runtime" -ForegroundColor White
if (Test-Path "$lerDir\run.py") {
    Test-Pass "run.py existe"
    $version = python "$lerDir\run.py" --version 2>&1
    $verLine = ($version -split "`n" | Select-Object -First 1)
    if ($verLine -match "v\d") { Test-Pass "LER versao: $verLine" }
    else { Test-Fail "LER --version" "$verLine" }
} else { Test-Fail "LER run.py" "Nao encontrado" }

# ─── 4. Knowledge graph ─────────────────────────────────────
Write-Host "[4] Knowledge graph" -ForegroundColor White
$graphFile = "$lerDir\knowledge\knowledge_graph.json"
if (Test-Path $graphFile) {
    try {
        $graph = Get-Content $graphFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $total = ($graph.patterns | Measure-Object).Count + ($graph.decisions | Measure-Object).Count + ($graph.bugs | Measure-Object).Count + ($graph.mission_learnings | Measure-Object).Count
        if ($total -gt 0) { Test-Pass "Knowledge graph: $total entradas" }
        else { Test-Warn "Knowledge graph" "Vazio (0 entradas)" }
        Test-Pass "JSON valido"
    } catch { Test-Fail "Knowledge graph" "JSON invalido: $_" }
} else { Test-Fail "knowledge_graph.json" "Nao encontrado" }

# ─── 5. CONHECIMENTO.md ─────────────────────────────────────
Write-Host "[5] CONHECIMENTO.md" -ForegroundColor White
if (Test-Path "$lerDir\CONHECIMENTO.md") {
    $size = (Get-Item "$lerDir\CONHECIMENTO.md").Length
    if ($size -gt 1000) { Test-Pass "CONHECIMENTO.md: $([math]::Round($size/1KB,1)) KB" }
    else { Test-Warn "CONHECIMENTO.md" "Muito pequeno ($size bytes)" }
} else { Test-Fail "CONHECIMENTO.md" "Nao encontrado" }

# ─── 6. OpenCode ───────────────────────────────────────────
Write-Host "[6] OpenCode" -ForegroundColor White
$ocodeVersion = npm list -g opencode-ai 2>&1 | Select-String "opencode-ai"
if ($ocodeVersion) {
    $ver = $ocodeVersion -replace '.*@', ''
    Test-Pass "OpenCode $ver"
} else { Test-Fail "OpenCode" "Nao instalado" }

# ─── 7. Agents ─────────────────────────────────────────────
Write-Host "[7] Agents OpenCode" -ForegroundColor White
$agentDir = "$ecoDir\config\agents"
$expectedAgents = @("00-system-rules", "01-estrategista", "02-cetico", "03-realista", "04-etica", "05-futuro", "06-recursos", "07-criativo", "08-revisor", "10-aprendizado", "11-ler-executor", "12-parallel-planner", "13-flutter-orquestrador", "99-gerador-de-agentes")
$foundAgents = 0
if (Test-Path $agentDir) {
    foreach ($a in $expectedAgents) {
        if (Test-Path "$agentDir\$a.md") { $foundAgents++ }
    }
    if ($foundAgents -eq $expectedAgents.Count) { Test-Pass "Todos $foundAgents agents encontrados (fonte: config/agents)" }
    else { Test-Warn "Agents" "$foundAgents/$($expectedAgents.Count) encontrados em config/agents" }
} else { Test-Warn "Agent dir" "config/agents nao encontrado" }

# ─── 8. Config OpenCode ─────────────────────────────────────
Write-Host "[8] Config OpenCode" -ForegroundColor White
$configFile = "$env:USERPROFILE\.config\opencode\opencode.jsonc"
if (Test-Path $configFile) {
    $config = Get-Content $configFile -Raw
    if ($config -match "ler-runtime") { Test-Pass "opencode.jsonc aponta para ler-runtime" }
    else { Test-Fail "opencode.jsonc" "Nao referencia ler-runtime" }
    if ($config -match "EcoSystemUmGrau/mcp") { Test-Pass "Habilidades referenciadas (mcp/)" }
    else { Test-Fail "opencode.jsonc" "Habilidades nao referenciadas (mcp/)" }
} else { Test-Fail "opencode.jsonc" "Nao encontrado" }

# ─── 9. Vigilante ──────────────────────────────────────────
Write-Host "[9] Vigilante" -ForegroundColor White
$pidFile = "$env:USERPROFILE\.vigilante.pid"
if (Test-Path $pidFile) {
    $vigPid = (Get-Content $pidFile -Raw).Trim()
    $proc = Get-Process -Id $vigPid -ErrorAction SilentlyContinue
    if ($proc) { Test-Pass "Vigilante ativo (PID $vigPid)" }
    else { Test-Fail "Vigilante" "PID $vigPid encontrado mas processo morto" }
} else { Test-Warn "Vigilante" "Inativo (pode ser intencional)" }

# ─── 10. Ecosystem script ───────────────────────────────────
Write-Host "[10] Ecosystem.ps1" -ForegroundColor White
$ecoScript = "$ecoDir\scripts\ecosystem.ps1"
if (Test-Path $ecoScript) {
    if (Test-Path $ecoScript) { Test-Pass "ecosystem.ps1 pronto para uso" }
} else { Test-Fail "ecosystem.ps1" "Nao encontrado" }

# ─── 10. Regras 3 camadas ──────────────────────────────────
Write-Host "[10] Regras do ecossistema (3 camadas)" -ForegroundColor White
try {
    $rulesOut = python "$ecoDir\scripts\sync_rules.py" check 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { Test-Pass "Regras 3 camadas consistentes" }
    else {
        Test-Warn "Regras" "Divergencia detectada:"
        $rulesOut -split "`n" | Where-Object { $_ -match "DIVERGENCIA" } | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    }
} catch { Test-Warn "Regras" "sync_rules check ignorado: $_" }

# ─── 11. Profile PowerShell ─────────────────────────────────
Write-Host "[11] Profile PowerShell" -ForegroundColor White
$profileFile = "$env:USERPROFILE\Documents\WindowsPowerShell\profile.ps1"
if (Test-Path $profileFile) {
    $profileContent = Get-Content $profileFile -Raw
    if ($profileContent -match "start-vigilante") { Test-Pass "start-vigilante definida" }
    else { Test-Warn "Profile" "start-vigilante nao encontrada" }
    if ($profileContent -match "ecosystem") { Test-Pass "ecosystem definida" }
    else { Test-Warn "Profile" "ecosystem nao encontrada" }
} else { Test-Fail "Profile" "Nao encontrado" }

# ─── 12. ler.bat ────────────────────────────────────────────
Write-Host "[12] ler.bat" -ForegroundColor White
$lerBat = "$env:USERPROFILE\.local\bin\ler.bat"
if (Test-Path $lerBat) {
    $batContent = Get-Content $lerBat -Raw
    if ($batContent -match "ler-runtime") { Test-Pass "ler.bat aponta para ler-runtime" }
    else { Test-Warn "ler.bat" "Nao referencia ler-runtime" }
} else { Test-Warn "ler.bat" "Nao encontrado (precisa estar no PATH)" }

# ─── 13. Aprendizados registrados ──────────────────────────
Write-Host "[13] Base de conhecimento" -ForegroundColor White
$learnDir = "$ecoDir\conhecimento\aprendizados"
if (Test-Path $learnDir) {
    $count = (Get-ChildItem $learnDir -Filter "*.md" | Measure-Object).Count
    if ($count -gt 0) { Test-Pass "$count aprendizados registrados" }
    else { Test-Warn "Aprendizados" "Nenhum arquivo encontrado" }
} else { Test-Fail "conhecimento/aprendizados" "Nao encontrado" }

# ─── 14. Projetos Android ────────────────────────────────────
Write-Host "[14] Projetos Android" -ForegroundColor White
$projectsDir = "$ecoDir\Projetos"
$projectCount = 0
$syncedCount = 0
if (Test-Path $projectsDir) {
    $projects = Get-ChildItem $projectsDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.FullName -ne $ecoDir -and $_.Name -ne "ler-runtime" }
    foreach ($proj in $projects) {
        if (-not (Test-Path "$($proj.FullName)\.git")) { continue }
        $projectCount++
        $remote = git -C $proj.FullName remote -v 2>&1 | Where-Object { $_ -match "fetch" }
        $status = git -C $proj.FullName status --short 2>&1 | Out-String
        if ($remote) {
            if ($status.Trim()) { Test-Warn "$($proj.Name)" "Remote OK, mas $($status.Trim().Split("`n").Count) arquivo(s) pendente(s)" }
            else { Test-Pass "$($proj.Name): sincronizado"; $syncedCount++ }
        } else { Test-Warn "$($proj.Name)" "Sem git remote" }
    }
    if ($projectCount -eq 0) { Test-Warn "Projetos Android" "Nenhum repo git encontrado em $projectsDir" }
    else { Test-Pass "$syncedCount/$projectCount projetos sincronizados" }
} else { Test-Warn "Projetos Android" "Diretorio $projectsDir nao existe" }
# ─── 15. Git remotes ────────────────────────────────────────
Write-Host "[15] Git" -ForegroundColor White
$remote = git -C $ecoDir remote -v 2>&1 | Select-String "fetch"
if ($remote) { Test-Pass "Git remote configurado" }
else { Test-Fail "Git remote" "Nenhum remote encontrado" }

# ─── Resultado ──────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Resultado: $passed passed, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "============================================" -ForegroundColor Cyan

if ($failed -gt 0) { exit 1 } else { exit 0 }
