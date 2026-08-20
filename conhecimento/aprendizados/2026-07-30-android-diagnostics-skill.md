# 2026-07-30 - Skill de Diagnóstico Remoto Android

## O que foi criado
- `scripts/android_diagnostics.py` — Script Python que conecta via ADB ao dispositivo `100.64.71.9:5555` e coleta diagnóstico completo do VoxUmGrau
- `skills/android-diagnostics/skill.md` — Skill documentando o uso do script

## Capacidades do diagnóstico
- Modelo do dispositivo, versão Android, SDK, fuso horário
- Bateria (nível, temperatura, status de carga)
- Aplicativo (versãoCode, versionName, PID, memória PSS, processo ativo)
- Rede (tipo de conexão, WebSocket na porta 8765)
- Ãudio (configurações, MediaPlayer ativo)
- Últimos 15 logs de erro/aviso do app

## Bug identificado durante o teste
**MediaPlayer com eventos não tratados**: log `"mediaplayer went away with unhandled events"` aparece quando o MediaPlayer é liberado enquanto ainda tem eventos pendentes. Causa comum: o player é fechado sem tratar o callback de completion corretamente.

**Conversão de canal de áudio**: `"aidl2legacy_AudioChannelLayout: no legacy output found for layoutMask: 16"` indica configuração de canal não padrão — pode causar problemas em alguns dispositivos.

## Comandos úteis
```bash
python scripts/android_diagnostics.py           # diagnóstico completo
python scripts/android_diagnostics.py --watch   # monitoramento contínuo (futuro)
```

## Gatilhos de uso
Usar quando o usuário relatar problemas no app Android: não responde, não ouve, sem áudio, lento, desconectado.
