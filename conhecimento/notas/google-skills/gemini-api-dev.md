---
tags: [google-skills, gemini-api-dev, interactions-api, sdk]
aliases: [Gemini API Dev, Interactions API, Gemini SDK]
date: 2026-09-15
categoria: google-skills
---

# gemini-api-dev — Gemini API Development

**Categoria:** google-skills
**Fonte:** mcp/google/habilidades/google-agent-skills/gemini-api-dev/

## Papel

Skill oficial para escrever código que chama a Gemini API: geração de texto, chat multi-turno, multimodal, geração de imagem/vídeo, streaming, function calling, saída estruturada e agentes gerenciados (Antigravity, Deep Research, custom agents). Usa a Interactions API (novo schema de `steps`, substituindo `generateContent` legado).

## Pontos chave

- Modelos atuais: `gemini-3.8-flash` (padrão), `gemini-3.5-flash-lite`, `gemini-3.1-pro-preview`, `gemini-3.5-transcribe`, `gemini-3-pro-image` (Nano Banana Pro), `gemini-3.1-flash-image`, `gemini-omni-1.1-flash` (vídeo)
- Deprecated: `gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*` — nunca usar
- SDKs atuais: `google-genai` >= 2.3.0 (Python) e `@google/genai` >= 2.3.0 (TS); SDKs legados (`google-generativeai`/`@google/generative-ai`) deprecated
- Interações armazenadas por padrão (store=True); desabilitar com store=False
- `tools`, `system_instruction` e `generation_config` são por interação (re-especificar a cada turno)
- Agentes gerenciados exigem `environment="remote"` (sandbox Linux)
- Helper de resposta: `output_text`, `output_image`, `output_audio`
- Migração de `generateContent` → consultar `references/migration.md`

## Dependências

- Python >= 3.10 (PEP 604) para SDK e exemplos
- `pip install -U google-genai`
- Antes de escrever código, buscar a doc oficial correspondente (Interactions API, Model Cards, etc.)

## Conexões

- [[cluster-hub-google-skills]] — hub do cluster das skills do Google
- [[google-agent-skills]] — padrão Agent Skills no qual esta skill se baseia
- [[gemini-live-api-dev]] — skill irmã para streaming em tempo real
- [[gemini-omni-flash-api]] — skill irmã para geração/edição de vídeo