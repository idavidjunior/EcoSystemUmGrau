---
tipo: padrao
tags: [json, sanitization, llm-wizard, package, build-artifact]
data: 2026-08-08
contexto: Categorias e sanitizacao de arquivos JSON no ecossistema
decisao: Excluir build artifacts (runtime/, conversa_unica.json) do versionamento.
  Sanitizar todos paths hardcoded (C:\\Users\\David Jr) com template vars.
  Criar LLM Selection Wizard interativo integrado ao setup-auto.ps1.
impacto: >
  - 86 tracked JSONs reduzidos a 70 (16 runtime artifacts removidos do git)
  - Zero paths hardcoded de usuario restantes em tracked files
  - {{LLM_MODEL}} template var adicionada ao opencode.jsonc
  - Wizard permite escolha interativa de modelo LLM no primeiro setup
  - Preflight: ALL TESTS PASSED
---

# JSON Sanitization + LLM Wizard

## Categorias de Arquivos JSON

### CRITICAL (config/template - INCLUIR no pacote)
- config/opencode.jsonc (template com {{USERPROFILE}}, {{LLM_MODEL}})
- config/opencode-model-fallback.jsonc
- conhecimento/episodios.json, etica/**, memoria/** (index, tfidf, etc.)
- manifesto_geral.json, mcp/**, ler-runtime/config/**

### BUILD ARTIFACT (runtime generated - IGNORAR)
- runtime/checkpoints/*.json (15 arquivos)
- runtime/state.json
- conversa_unica.json

### OBSIDIAN (vault config - manter para reprodutibilidade)
- .obsidian/*.json (appearance, hotkeys, etc.)
- .obsidian/plugins/*/manifest.json (não data.json - dados do usuario)

### PACKAGE META (npm - manter)
- package.json, package-lock.json

### USER DATA (hardcoded paths - SANITIZAR)
- Sanitizados: conhecimento/projetos-irmaos.json, scripts/opencode-serve.jsonc,
  conhecimento/memoria/memories.json
- Template usado: {{USERPROFILE}}, {{PROJECT_PARENT}}, {{PROJECT_ROOT}}

## LLM Selection Wizard

- Script: scripts/llm-wizard.py
- Integrado ao setup-auto.ps1 (step 9/10)
- Detecta providers via env vars (NVIDIA_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
- Lista modelos nativos OpenCode + proveedores baseados em keys
- Salva escolha em config/.llm-choice.json (gitignored)
- Template var {{LLM_MODEL}} renderizada no deploy


## Testes e Regressao (10/10)

### Problemas Encontrados e Corrigidos

1. **{{PROJECT_ROOT}} nao resolvido**: `scripts/opencode-serve.jsonc` usava `{{PROJECT_ROOT}}` que nao era resolvido por nenhum script. Trocado por `{{USERPROFILE}}` pattern (padrao do ecossistema).

2. **BOM embedidos em JSONs**: `knowledge_graph.json` tinha caracteres BOM (U+FEFF) embedados em 225 strings body. `tfidf_meta.json` tinha 225 BOM chars. Ambos corrigidos.

3. **Path hardcoded remanescente**: Memoria id=189 (registro do trabalho anterior) contia "C:\Users\David Jr" no summary. Removido.

### Testes Criados

- `scripts/test_json_sanitization.py`: escaneia todos os 70 JSON/JSONC tracked por:
  - Hardcoded paths (C:\Users\David, C:/Users/David)
  - BOM (file-level e embedado)
  - Template vars nao resolvidos ({{USERPROFILE}} em arquivos nao-template)

- Integrado ao `preflight_check.py` como check #8

### Resultado Final

| Metrica | Valor |
|---------|-------|
| JSON files tracked | 70 |
| Pass | 70 |
| Fail | 0 |
| Warn | 0 |
| Hardcoded paths | 0 |
| Unresolved templates | 0 |
