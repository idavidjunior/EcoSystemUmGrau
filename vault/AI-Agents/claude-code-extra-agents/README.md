# Claude Code Extra Agents

Ecossistema de agentes e skills para desenvolvimento, qualidade, seguranca e operacao no Claude Code.

## Instalacao em 1 minuto

### Opcao 1: Plugin Marketplace (recomendada)
```text
/plugin marketplace add idavidjunior/claude-code-extra-agents
/plugin install claude-code-extra-agents@claude-code-extra-agents
```

### Opcao 2: Script local (Windows)
```powershell
./install.ps1
```

### Opcao 3: Script local (Linux/macOS)
```bash
bash install.sh
```

## Multi-plataforma (core unico)
- Guia: [Multi-platform](docs/MULTIPLATFORM.md)
- Core spec: `core-spec/agents/*.agent.yaml` e `core-spec/skills/*.skill.yaml`
- Targets: Claude Code, Ollama, Open WebUI, Continue/Cline

Gerar e validar:
```powershell
python ./scripts/build_core_and_targets.py
python ./scripts/validate_core_spec.py
```

## Agent Reliability Lab
- Guia: [Reliability Lab](reliability-lab/README.md)
- Cenarios fixos, rubrica e leaderboard por versao

Executar avaliacao:
```bash
python ./scripts/evaluate_reliability_lab.py
```

## Quick Start
- Guia rapido: [Quickstart](docs/QUICKSTART.md)
- Modelo de operacao: [Operating Model](docs/OPERATING_MODEL.md)
- Matriz agente x skill: [Agent x Skill Matrix](docs/AGENT_SKILL_MATRIX.md)
- Indice de skills: [Skill Index](docs/SKILL_INDEX.md)
- Referencia de comandos: [Commands](docs/COMMANDS.md)

## Estado Atual
- Agentes: 22
- Skills: 30
- Comandos: 13

## Validacao
- Estrutura front matter: `./scripts/validate-ecosystem.ps1`
- Links locais de docs: `./scripts/validate-doc-links.ps1`

## Licenca
MIT
