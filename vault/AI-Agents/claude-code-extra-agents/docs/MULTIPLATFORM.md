# Multi-platform Compatibility

## Objetivo
Manter um core unico de agentes/skills e gerar artefatos para multiplas plataformas.

## Fonte unica
- `agents/*.md`
- `skills/*/skill.md`

## Core spec gerado
- `core-spec/agents/*.agent.yaml`
- `core-spec/skills/*.skill.yaml`
- `core-spec/manifest.json`

## Targets gerados
- Claude Code: `dist/claude-code/manifest.json`
- Ollama: `dist/ollama/modelfiles/*.Modelfile`
- Open WebUI: `dist/openwebui/agents/*.json`
- Continue/Cline: `dist/continue/prompts/*.prompt.md`

## Comandos
```powershell
python ./scripts/build_core_and_targets.py
python ./scripts/validate_core_spec.py
```

## Ollama (exemplo)
```bash
ollama create agent-debug-forensic -f dist/ollama/modelfiles/debug-forensic.Modelfile
```

## Open WebUI
Importe os arquivos `dist/openwebui/agents/*.json` como personas/presets.

## Continue/Cline
Use `dist/continue/prompts/*.prompt.md` como prompt base de role/agente.
