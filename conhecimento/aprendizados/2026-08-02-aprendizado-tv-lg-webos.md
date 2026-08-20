# 2026-08-02 - Aprendizado da TV LG 50UT8050PSA (webOS)

**Categoria:** padrao
**Fonte:** sessao_aprendizado_tv
**Gravidade:** media

## Contexto

Missão de aprendizado do controle nativo da TV LG via SSAP (wss://192.168.15.6:3001),
para habilitação do Jarvis como controle remoto de voz.

## O que funciona (validado em 02/08/2026)

- **Conectividade:** porta 3001 (WSS/SSAP) aberta; porta 3000 (SSAP legado), 8009 (Google Cast) e 7000 (AirPlay) também abertas.
- **Estado:** `ssap://com.webos.service.tvpower/power/getPowerState` â†’ `Active`.
- **Volume:** `ssap://audio/getVolume` â†’ 14; `setVolume`, `volumeUp/Down`, `setMute` OK.
- **Apps em primeiro plano:** `ssap://com.webos.applicationManager/getForegroundAppInfo` â†’ `amazon`, depois `youtube.leanback.v4`.
- **Entradas:** `ssap://tv/getExternalInputList` â†’ HDMI 1, 2 e 3.
- **Teclas remotas:** pointer socket (HOME, UP/DOWN, OK...) via `ssap://com.webos.service.networkinput/getPointerInputSocket`.
- **Mídia:** `ssap://media.controls/play|pause|stop|rewind|fastForward` OK.
- **Tela:** `ssap://com.webos.service.tv.display/setScreenState` retorna vazio (não confirmado).
- **Desligar:** `ssap://system/turnOff`. **Ligar:** Wake-on-LAN (MAC `00:a1:59:82:bb:08`).

## O que NÃO funciona (proteção do webOS)

- `ssap://com.webos.applicationManager/listApps` e `listLaunchPoints` â†’ **401 insufficient permissions**
  mesmo após re-pareamento com manifesto completo (incluindo READ_INSTALLED_APPS).
- `ssap://com.webos.applicationManager/getAppInfo` â†’ 401.
- Modo desenvolvedor (porta 5000) **fechada** — não ativado.

## Conclusão

No webOS atual (LG 50UT8050PSA), a listagem do catálogo de apps via SSAP é bloqueada
por segurança para clientes de segunda tela — mesmo com permissões no manifesto.
O caminho para o catálogo completo (147 apps) é o **Modo Desenvolvedor** da TV
(instalar o app "Developer Mode" na loja LG e ativar na TV), que libera a porta 5000
e serviços de dev.

Controle essencial (power, volume, teclas, mídia, HDMI, foreground) está **100% funcional**
e pronto para uso do Jarvis como controle remoto de voz.

## Próximo passo (opcional)

Ativar Modo Desenvolvedor na TV (manual, requer a loja LG) para liberar `listApps`
e navegação total de apps por voz.
