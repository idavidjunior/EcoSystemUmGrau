---
tags: [google-skills, gemini-omni-flash-api, video-generativo]
aliases: [Gemini Omni Flash, Omni Flash, video generativo]
date: 2026-09-15
categoria: google-skills
---

# gemini-omni-flash-api — Gemini Omni 1.1 Flash (Vídeo)

**Categoria:** google-skills
**Fonte:** mcp/google/habilidades/google-agent-skills/gemini-omni-flash-api/

## Papel

Skill oficial para geração e edição de vídeo generativo com o modelo `gemini-omni-1.1-flash` via SDK `google-genai`: texto para vídeo, primeiro-quadro para vídeo (`--first-frame`), transição primeiro-e-último-quadro, extensões (até 40s), edição (máx 10s), geração com referências de imagem/vídeo.

## Pontos chave

- Resoluções: `360p`, `720p` (padrão), `1080p`, `4k` — landscape `16:9` e portrait `9:16`
- Duração por geração: 3–10s; extensão +10s por turno até 40s total
- Mídia deve ser enviada antes via Files API (upload_file.py)
- `prep_video.py`: normaliza/ajusta vídeos grandes (max 1280x720 landscape); `inspect_video.py`: inspeciona com ffprobe
- Áudio: manter original (padrão) ou regenerar tudo com `--strip-audio`
- `--previous-interaction-id` para edição/extensão multitorre sem re-enviar mídia
- Prompts simples funcionam melhor para edição; `"Keep everything else the same"` mantém consistência visual
- Tags de papel: `<FIRST_FRAME>`, `<LAST_FRAME>`, `<IMAGE_REF_N>`, `<VIDEO_REF_N>`; declaração explícita com `[# Sources ...]`/`[# References ...]`
- Restrição regional: upload de vídeo para edição/extensão indisponível em EEA, Suíça, Reino Unido e alguns estados dos EUA

## Dependências

- `google-genai` >= 2.19.0 (Python); Python >= 3.10
- `ffmpeg` + `ffprobe` no PATH (para prep/inspect e strip-audio)
- `GEMINI_API_KEY` configurada

## Conexões

- [[cluster-hub-google-skills]] — hub do cluster das skills do Google
- [[google-agent-skills]] — padrão Agent Skills no qual esta skill se baseia
- [[gemini-api-dev]] — skill irmã: SDK, modelos e Interactions API