---
name: streaming
description: Streaming e reproducao — controle de reproducao continua de midia, transmissao de audio/video e integracao com dispositivos de saida (TV, audio). Ativa quando o usuario precisa transmitir, reproduzir ou controlar midia em fluxo continuo. Trigger keywords: "streaming", "stream", "transmitir", "reproduzir", "tocar", "play", "pause", "TV", "cast", "chromecast", "media", "radio", "fila de reproducao".
---

# streaming — Streaming e Reprodução

## Objetivo

Lidar com mídia em fluxo contínuo: reprodução, transmissão, controle de player e
integração com dispositivos de saída (ex.: TV LG).

## Operações

### Reprodução
- Iniciar/pausar/parar/pular mídia (play, pause, stop, next/prev).
- Filas de reprodução contínua.

### Transmissão (cast)
- Enviar mídia do dispositivo para uma saída maior (TV, speaker).
- Reuso: controle de TV LG via `scripts/tv_control.py` (pareamento `lg_pair_tv.py`).

### Controle de player
- Volume, posição, mídia atual, estado do player.

## Regras
- Controle de TV/mídia = `scripts/tv_control.py` / `scripts/lg_pair_tv.py`.
- Não inventar protocolos de cast; usar o que a integração do ecossistema suporta.

## Arquivos
- `skill.md` — definição.
- Reuso: `scripts/tv_control.py`, `scripts/lg_pair_tv.py`.
