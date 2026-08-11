# Controle de TV LG (01/08/2026)

## TV identificada
- Modelo: **50UT8050PSA** (LG 50" webOS, firmware p20.33.31.61)
- Hostname mDNS: `[LG] webOS TV UT8050PSA`
- IP local: `192.168.15.6` (MAC `00:a1:59:82:bb:08`, LG Electronics)
- Serial: `412AZAL87976`
- ServiÃ§os: SSAP (wss://3001), Google Cast (8009), AirPlay 2 (7000)

## Controle nativo (total)
- Biblioteca: `pywebostv` + CLI `lgtvremote-cli` (porta 3001 wss, secure).
- Pareamento: PROMPT (confirmaÃ§Ã£o na tela) ou WoL para ligar.
- Client-key salvo em `scripts/keys/lgtv_50UT8050PSA.json` (`f61bccaabd247d8ae1702672d3f9c4f5`).
- Portas: 3000 (ws, bloqueado em TVs novas) â†’ usar 3001 (wss). Porta 3000 faz reset em newer models â†’ usar secure=True.

## Comandos
- `lgtv --tv 192.168.15.6 power-status` â†’ {"power":"on/off",...}
- `lgtv --tv <ip> on` â†’ Wake-on-LAN (MAC `00:a1:59:82:bb:08`)
- `lgtv --tv <ip> off|power|screen-on`
- `lgtv --tv <ip> apps|app <id>|inputs|input <n>`
- `lgtv --tv <ip> volume up|down|<n>|mute|nav <dir>`

## Regra de ouro (permanente, 01/08/2026)
- **Sempre iniciar no volume 10. Nunca deixar no mÃ¡ximo.** O usuÃ¡rio ajusta depois.

## Estado
- Pairing OK; TV controlada via SSH/CLI; ligar via WoL; SSAP 3000 bloqueado mas 3001 funciona.

## 10. LiÃ§Ã£o de navegaÃ§Ã£o em apps (01/08/2026)
- **Apps com login/perfil (Prime, Netflix, etc.) exigem seleÃ§Ã£o de perfil** antes de play. O SSAP `nav` envia teclas cegamente â€” sem visÃ£o da tela, nÃ£o dÃ¡ pra saber posiÃ§Ã£o do cursor, se teclado abriu, se resultado apareceu.
- **Fluxo realista:** usuÃ¡rio navega no app (controle fÃ­sico/app mobile) atÃ© o conteÃºdo desejado (busca, perfil, episÃ³dio), e o Jarvis assume sÃ³ o **player** (play/pause/seek/volume) via SSAP.
- **NavegaÃ§Ã£o cega = chute.** Tentar buscar "Mestres do Universo" via teclas no teclado virtual da Prime sem ver a tela falhou. NÃ£o tentar â€” combinar com usuÃ¡rio: ele posiciona, eu controlo player.
- **Se precisar buscar via automaÃ§Ã£o real:** requer OCR/visÃ£o computacional na tela (HDMI capture + CV) ou API oficial do serviÃ§o â€” fora do escopo do SSAP.

## Conexoes

- [[cluster-hub-programacao]]