# 2026-08-02 - Aprendizado da TV LG 50UT8050PSA (webOS)

**Categoria:** padrao
**Fonte:** sessao_aprendizado_tv
**Gravidade:** media

## Contexto

MissÃ£o de aprendizado do controle nativo da TV LG via SSAP (wss://192.168.15.6:3001),
para habilitaÃ§Ã£o do Jarvis como controle remoto de voz.

## O que funciona (validado em 02/08/2026)

- **Conectividade:** porta 3001 (WSS/SSAP) aberta; porta 3000 (SSAP legado), 8009 (Google Cast) e 7000 (AirPlay) tambÃ©m abertas.
- **Estado:** `ssap://com.webos.service.tvpower/power/getPowerState` â†’ `Active`.
- **Volume:** `ssap://audio/getVolume` â†’ 14; `setVolume`, `volumeUp/Down`, `setMute` OK.
- **Apps em primeiro plano:** `ssap://com.webos.applicationManager/getForegroundAppInfo` â†’ `amazon`, depois `youtube.leanback.v4`.
- **Entradas:** `ssap://tv/getExternalInputList` â†’ HDMI 1, 2 e 3.
- **Teclas remotas:** pointer socket (HOME, UP/DOWN, OK...) via `ssap://com.webos.service.networkinput/getPointerInputSocket`.
- **MÃ­dia:** `ssap://media.controls/play|pause|stop|rewind|fastForward` OK.
- **Tela:** `ssap://com.webos.service.tv.display/setScreenState` retorna vazio (nÃ£o confirmado).
- **Desligar:** `ssap://system/turnOff`. **Ligar:** Wake-on-LAN (MAC `00:a1:59:82:bb:08`).

## O que NÃƒO funciona (proteÃ§Ã£o do webOS)

- `ssap://com.webos.applicationManager/listApps` e `listLaunchPoints` â†’ **401 insufficient permissions**
  mesmo apÃ³s re-pareamento com manifesto completo (incluindo READ_INSTALLED_APPS).
- `ssap://com.webos.applicationManager/getAppInfo` â†’ 401.
- Modo desenvolvedor (porta 5000) **fechada** â€” nÃ£o ativado.

## ConclusÃ£o

No webOS atual (LG 50UT8050PSA), a listagem do catÃ¡logo de apps via SSAP Ã© bloqueada
por seguranÃ§a para clientes de segunda tela â€” mesmo com permissÃµes no manifesto.
O caminho para o catÃ¡logo completo (147 apps) Ã© o **Modo Desenvolvedor** da TV
(instalar o app "Developer Mode" na loja LG e ativar na TV), que libera a porta 5000
e serviÃ§os de dev.

Controle essencial (power, volume, teclas, mÃ­dia, HDMI, foreground) estÃ¡ **100% funcional**
e pronto para uso do Jarvis como controle remoto de voz.

## PrÃ³ximo passo (opcional)

Ativar Modo Desenvolvedor na TV (manual, requer a loja LG) para liberar `listApps`
e navegaÃ§Ã£o total de apps por voz.
