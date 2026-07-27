#!/bin/bash
# Instalador do Claude Code Extra Agents
# Uso: bash install.sh

set -e

echo ""
echo "============================================"
echo "  Claude Code Extra Agents - Instalador"
echo "============================================"
echo ""

# Perguntar escopo
echo "Onde deseja instalar?"
echo "  1) Global (~/.claude/) - disponível em todos os projetos"
echo "  2) Local (.claude/) - apenas neste projeto"
read -p "Escolha (1/2): " SCOPE

if [ "$SCOPE" = "1" ]; then
    TARGET="$HOME/.claude"
else
    TARGET=".claude"
fi

echo ""
echo "Instalando em: $TARGET"
echo ""

# Criar diretórios
mkdir -p "$TARGET/agents"
mkdir -p "$TARGET/skills"
mkdir -p "$TARGET/commands"

# Copiar agentes
echo "[1/3] Instalando agentes..."
if [ -d "agents" ]; then
    cp -r agents/* "$TARGET/agents/" 2>/dev/null || true
    AGENT_COUNT=$(ls -1 agents/*.md 2>/dev/null | wc -l)
    echo "  -> $AGENT_COUNT agentes instalados"
fi

# Copiar skills
echo "[2/3] Instalando skills..."
if [ -d "skills" ]; then
    cp -r skills/* "$TARGET/skills/" 2>/dev/null || true
    SKILL_COUNT=$(ls -1d skills/*/ 2>/dev/null | wc -l)
    echo "  -> $SKILL_COUNT skills instaladas"
fi

# Copiar comandos
echo "[3/3] Instalando comandos..."
if [ -d "commands" ]; then
    cp -r commands/* "$TARGET/commands/" 2>/dev/null || true
    CMD_COUNT=$(ls -1 commands/*.md 2>/dev/null | wc -l)
    echo "  -> $CMD_COUNT comandos instalados"
fi

echo ""
echo "============================================"
echo "  Instalacao concluida com sucesso!"
echo "============================================"
echo ""
echo "Agentes disponiveis:"
ls -1 "$TARGET/agents/"*.md 2>/dev/null | while read f; do
    echo "  - $(basename "$f" .md)"
done
echo ""
echo "Skills disponiveis:"
ls -1d "$TARGET/skills/"*/ 2>/dev/null | while read d; do
    echo "  - $(basename "$d")"
done
echo ""
echo "Abra o Claude Code e comece a usar."
echo "Exemplo: 'Tem um erro 500 em producao, me ajuda'"
echo "         'Revise esse codigo que o Copilot gerou'"
echo "         'Quero treinar meu time para incidentes'"
echo ""
