# 2026-07-30 - Skill de DiagnÃ³stico Remoto Android

## O que foi criado
- `scripts/android_diagnostics.py` â€” Script Python que conecta via ADB ao dispositivo `100.64.71.9:5555` e coleta diagnÃ³stico completo do VoxUmGrau
- `skills/android-diagnostics/skill.md` â€” Skill documentando o uso do script

## Capacidades do diagnÃ³stico
- Modelo do dispositivo, versÃ£o Android, SDK, fuso horÃ¡rio
- Bateria (nÃ­vel, temperatura, status de carga)
- Aplicativo (versÃ£oCode, versionName, PID, memÃ³ria PSS, processo ativo)
- Rede (tipo de conexÃ£o, WebSocket na porta 8765)
- Ãudio (configuraÃ§Ãµes, MediaPlayer ativo)
- Ãšltimos 15 logs de erro/aviso do app

## Bug identificado durante o teste
**MediaPlayer com eventos nÃ£o tratados**: log `"mediaplayer went away with unhandled events"` aparece quando o MediaPlayer Ã© liberado enquanto ainda tem eventos pendentes. Causa comum: o player Ã© fechado sem tratar o callback de completion corretamente.

**ConversÃ£o de canal de Ã¡udio**: `"aidl2legacy_AudioChannelLayout: no legacy output found for layoutMask: 16"` indica configuraÃ§Ã£o de canal nÃ£o padrÃ£o â€” pode causar problemas em alguns dispositivos.

## Comandos Ãºteis
```bash
python scripts/android_diagnostics.py           # diagnÃ³stico completo
python scripts/android_diagnostics.py --watch   # monitoramento contÃ­nuo (futuro)
```

## Gatilhos de uso
Usar quando o usuÃ¡rio relatar problemas no app Android: nÃ£o responde, nÃ£o ouve, sem Ã¡udio, lento, desconectado.
