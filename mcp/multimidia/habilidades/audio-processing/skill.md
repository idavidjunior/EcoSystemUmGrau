---
name: audio-processing
description: Processamento de audio — transcricao (STT), sintese de fala (TTS), extracao de metadados, normalizacao e analise de arquivos de audio. Ativa quando o usuario precisa transcrever, falar, analisar, editar ou resgatar informacao de audio. Trigger keywords: "transcrever", "STT", "TTS", "falar", "audio", "mp3", "wav", "voz", "whisper", "edge-tts", "subtitulo", "podcast".
---

# audio-processing — Processamento de Áudio

## Objetivo

Produzir, transformar e interpretar conteúdo de áudio: transcrição (fala → texto),
síntese (texto → fala), extração de metadados, normalização de arquivos e análise.

## Operações

### Transcrição (STT)
- Local: `vox_audio.py ouvir` → Whisper local (STT do PC).
- Android: `SpeechRecognizer` → WebSocket → bridge (app VoxUmGrau).
- Saída: texto transcrito + confiança.

### Síntese (TTS)
- Bridge Jarvis: `jarvis_bridge.py gerar_audio` → `edge-tts` voz `pt-BR-AntonioNeural` (MP3 base64).
- Uso: resposta falada do ecossistema ("Eco").

### Extração de metadados
- Tags de MP3 (título, artista, álbum) via resgate de metadados — ver skill
  `mp3player-metadata-rescue` (categoria tecnica).

### Normalização/edição
- Converter formatos, ajustar volume, cortar trechos com ferramentas do sistema.

## Regras
- STT local = `vox_audio.py`; TTS = bridge Jarvis (`edge-tts`). Não duplicar pipelines.
- Se a entrada/saída principal é áudio, pertence aqui; se só manipula tags de arquivo,
  pertence a `tecnicas/` (ver `mp3player-metadata-rescue`).

## Arquivos
- `skill.md` — definição.
- Execução: via infra existente (`scripts/vox_audio.py`, `scripts/jarvis_bridge.py`).
