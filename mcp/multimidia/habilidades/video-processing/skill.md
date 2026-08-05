---
name: video-processing
description: Processamento de video — extracao de frames, transcricao de audio de video, conversao de formatos, analise de capturas de tela em movimento. Ativa quando o usuario precisa processar, analisar, converter ou extrair informacao de arquivos de video. Trigger keywords: "video", "videos", "mp4", "mkv", "frame", "frames", "gif", "tela gravada", "screen recording", "transcrever video", "extrair frame de video".
---

# video-processing — Processamento de Vídeo

## Objetivo

Produzir, transformar e interpretar conteúdo de vídeo: extração de frames,
transcrição de áudio embutido, conversão de formatos e análise de gravações.

## Operações

### Extração de frames
- Amostrar frames de um vídeo para OCR/análise visual (ex.: diagnósticos de tela
  gravada, ver o que acontecia em um instante).

### Transcrição de vídeo
- Extrair o áudio do vídeo e transcrever (reuso do pipeline de `audio-processing`).

### Conversão
- Entre formatos (mp4/mkv/webm/gif), reenquadrar, recortar trechos.

### Análise
- Sequência de frames para entender mudanças de estado (UI, animação, reprodução).

## Regras
- Vídeo = combinação de `image-processing` (frames) + `audio-processing` (trilha).
- Extraia só os frames necessários; não processe o arquivo inteiro desnecessariamente.

## Arquivos
- `skill.md` — definição.
- Reuso: pipelines de imagem e áudio do ecossistema.
