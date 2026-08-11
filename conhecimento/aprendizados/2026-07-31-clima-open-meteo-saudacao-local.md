# Aprendizado — 2026-07-31 — Clima Open-Meteo + saudação local no app

## Contexto
- A saudação criativa (tom/humor, data/hora, feriados, trânsito, previsão) já rodava no commit 992b0c8.
- Nesta sessão: migração do clima para **Open-Meteo** (gratuito, **sem chave de API**) e placeholder de saudação local no app VoxUmGrau.

## O que foi feito
1. **`scripts/clima_api.py`** reescrito para Open-Meteo:
   - Clima atual: `temperature_2m`, sensação, umidade, `weather_code` (com mapa pt-BR).
   - Previsão do dia: máx/mín, chance de chuva, descrição.
   - Fonte única de localização: `geolocalizacao.get_localizacao()`, com fallback São Paulo.
2. **VoxUmGrau** — saudação local placeholder:
   - `VoxTts.speak` ganhou parâmetro `done` opcional (callback customizado por fala).
   - `VoxViewModel`: ao conectar (1x por conexão) fala frase local curta via TTS Android, sem disparar `tentarOuvir()`.
   - Quando a saudação real chega da bridge (áudio/texto), `tts.stop()` corta o placeholder e cede lugar.
   - Flag `saudacaoLocalFalada` resetada em `connect()`.

## Heurísticas registradas
- **Latência da saudação da bridge → placeholder local**: o app fala algo imediatamente ao conectar e a bridge (LLM) cobre em ~1-2s; o áudio real substitui o local.
- **APIs meteorológicas**: preferir Open-Meteo (sem chave, CORS-friendly) a serviços que exigem token. Testar com `python clima_api.py`.
- **Push Git no Windows**: `git` não está no PATH da sessão do opencode — prefixar `$env:Path = "C:\Program Files\Git\cmd;" + $env:Path`. GitHub pode falhar por rede; validar com `Test-NetConnection github.com -Port 443` e reintentar.

## Estado
- Compilado e instalado APK no Redmi (serial `6d92eed7`), app reiniciado.
- Bridge reiniciada e ativa em `0.0.0.0:8765`; celular (`100.64.71.9`) reconectado (hist=25).
- Commits: `8730ea7` (EcoSystemUmGrau) e `3a5b340` (VoxUmGrau), ambos pushed.
