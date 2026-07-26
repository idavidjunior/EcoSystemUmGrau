# Instalador do Claude Code Extra Agents
# Uso: .\install.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Claude Code Extra Agents - Instalador" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Perguntar escopo
Write-Host "Onde deseja instalar?"
Write-Host "  1) Global ($HOME\.claude\) - disponivel em todos os projetos"
Write-Host "  2) Local (.claude\) - apenas neste projeto"
$SCOPE = Read-Host "Escolha (1/2)"

if ($SCOPE -eq "1") {
    $TARGET = "$HOME\.claude"
} else {
    $TARGET = ".claude"
}

Write-Host ""
Write-Host "Instalando em: $TARGET"
Write-Host ""

# Criar diretórios
New-Item -ItemType Directory -Force -Path "$TARGET\agents" | Out-Null
New-Item -ItemType Directory -Force -Path "$TARGET\skills" | Out-Null
New-Item -ItemType Directory -Force -Path "$TARGET\commands" | Out-Null

# Copiar agentes
Write-Host "[1/3] Instalando agentes..."
if (Test-Path "agents") {
    Copy-Item -Path "agents\*" -Destination "$TARGET\agents\" -Recurse -Force
    $AGENT_COUNT = (Get-ChildItem -Path "agents\*.md").Count
    Write-Host "  -> $AGENT_COUNT agentes instalados"
}

# Copiar skills
Write-Host "[2/3] Instalando skills..."
if (Test-Path "skills") {
    Copy-Item -Path "skills\*" -Destination "$TARGET\skills\" -Recurse -Force
    $SKILL_COUNT = (Get-ChildItem -Path "skills" -Directory).Count
    Write-Host "  -> $SKILL_COUNT skills instaladas"
}

# Copiar comandos
Write-Host "[3/3] Instalando comandos..."
if (Test-Path "commands") {
    Copy-Item -Path "commands\*" -Destination "$TARGET\commands\" -Recurse -Force
    $CMD_COUNT = (Get-ChildItem -Path "commands\*.md").Count
    Write-Host "  -> $CMD_COUNT comandos instalados"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Instalacao concluida com sucesso!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Agentes disponiveis:"
Get-ChildItem "$TARGET\agents\*.md" | ForEach-Object {
    Write-Host "  - " -NoNewline
    Write-Host $_.BaseName -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Skills disponiveis:"
Get-ChildItem "$TARGET\skills" -Directory | ForEach-Object {
    Write-Host "  - " -NoNewline
    Write-Host $_.Name -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Abra o Claude Code e comece a usar."
Write-Host "Exemplo: 'Tem um erro 500 em producao, me ajuda'"
Write-Host "         'Revise esse codigo que o Copilot gerou'"
Write-Host "         'Quero treinar meu time para incidentes'"
Write-Host ""
