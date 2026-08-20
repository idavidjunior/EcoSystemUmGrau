---
tipo: padrao
tags: [unified-bridge, tts, narrador, widget, singleton]
data: 2026-08-18
contexto: unified_bridge.py estava em _legado/ e faltava em scripts/
decisao: Copiar de _legado/ para scripts/ e validar sintaxe
impacto: Ponte unica restaurada - narrador + TTS service + widget em processo unico
---

## Contexto

O arquivo unified_bridge.py é a ponte unica que combina:
- Narrador (monitora opencode.db SQLite)
- TTS service (SpeechPipeline singleton)
- Widget pywebview (controle Jarvis)

O problema original era vozes duplicadas: 3 processos separados cada um com sua SpeechPipeline.

## O que aconteceu

O arquivo estava em `scripts/_legado/unified_bridge.py` mas faltava em `scripts/unified_bridge.py`. Foi copiado e validado.

## Arquitetura

O unified_bridge.py usa:
- Lock de arquivo (unified_bridge.lock + unified_bridge.pid) para garantir instancia unica
- Limpeza automatica de processos duplicados via taskkill
- SpeechPipeline singleton (instancia unica)
- Widget pywebview na thread principal (webview.start bloqueia)
- Narrador + TTS service em background thread

## Arquivos relacionados

- `scripts/unified_bridge.py` — ponte unica (deve ser o unico processo)
- `scripts/narrador_desktop.py` — narrador standalone (usa TTS via IPC)
- `scripts/tts_service.py` — daemon TTS standalone (backup)
- `scripts/widget_controle_jarvis.py` — widget antigo (NAO deve rodar separado)
