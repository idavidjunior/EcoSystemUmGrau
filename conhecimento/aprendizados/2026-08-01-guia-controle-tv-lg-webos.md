# Guia: Controle Total de TV LG webOS (reaproveitável)
**Criado:** 01/08/2026 | Aplica-se a qualquer TV LG webOS (UT80 e similares, 2024+)

> **Know-how de ouro:** este passo-a-passo reaplica-se a qualquer TV LG webOS. Só muda o IP e o MAC.

## 1. Descoberta e identificação
- **mDNS (224.0.0.251:5353):** pergunte por `_googlecast._tcp.local`, `_airplay._tcp.local`, `_webos._tcp.local`, `_services._dns-sd._udp.local`. A TV responde com hostname + TXT records (model, serialNumber, manufacturer, deviceid).
- **ARP scan (192.168.15.0/24):** `arp -a`, depois checa OUI do MAC (ex.: `00:A1:59` → LG Electronics, confirmado via maclookup.app/macverify).
- **Port scan de serviços:** portas clássicas: 3000 (SSAP ws, obsoleto em TVs novas → reset), **3001 (SSAP wss — usar!), 8009 (Google Cast), 7000 (AirTunes/AirPlay), 80/443 (web).**
- Dica: `python -m pip install lgtvremote-cli pychromecast pywebostv` — tudo pronto pro resto.

## 2. O ponto crítico que todo mundo erra (e que nos custou tempo)
- TVs LG **2024+ usam WebSocket SEGURO na porta 3001 (`wss://IP:3001`). A porta 3000 (`ws://`) dá `Connection reset`.**
- `pywebostv` default é insecure (3000) → **não usar o default.** `lgtvremote-cli` já usa 3001 wss por padrão (via `websocket` lib) — preferir.
- Confirmação: `openssl s_client -connect IP:3001` mostra handshake TLS = serviço vivo.

## 3. Pareamento (pairing)
- **Modo PROMPT** (ideal): TV mostra "Permitir [dispositivo]?" → usuário aperta OK no controle → TV devolve `registered` + `client-key`. **Não precisa digitar PIN nenhum.**
- **Modo PIN** (alternativo): TV exibe PIN, cliente digita via `ssap://pairing/setPin`. Evitar se possível.
- Para TVs que exigem prompt, usar `pairingType: "PROMPT"` + `forcePairing: true`. Enviar manifest completo com permissions (copiado de lgtvremote-cli: `CONTROL_POWER`, `LAUNCH`, `APP_TO_APP`, `READ_RUNNING_APPS`, etc.).
- Reaproveite o manifest de `lgtvremote-cli` (`REGISTRATION_PAYLOAD`) — não invente o seu.
- **Persistir `client-key`** numa pasta git-ignorada (`scripts/keys/, NEVER ` git-ignored). O TV mantém trust por IP+MAC; re-pair só se formatação/TV resetada.

## 4. Ligar da standby (power ON quando a TV não responde mais)
- SSAP não conecta em standby. Usar **Wake-on-LAN**: magic packet pra MAC da TV (ex.: `00:a1:59:82:bb:08`) → broadcast UDP porta 7/9. Depois `power-status` mostra `on`.

## 5. Controle (CLI pronta: lgtvremote-cli)
```
TV=192.168.15.6
lgtv --tv $TV power-status           # {"power":"on/off",...}
lgtv --tv $TV on                      # Wake-on-LAN
lgtv --tv $TV off | screen-on | power
lgtv --tv $TV volume set 10           # ← REGRA: iniciar sempre 10
lgtv --tv  $TV volume up|down|mute|unmute|get
lgtv --tv $TV nav up|down|left|right|enter|home|back
lgtv --tv $TV inputs                  # lista HDMI_1..3
lgtv --tv $TV launch netflix          # app por nome ou com.webos.app.xxx
lgtv --tv $TV apps                    # lista 147 apps
lgtv --tv $TV play|pause|ff|rewind|skip-forward|skip-back|stop
lgtv --tv $TV livetv|channel up|down
```
> **Apps via Cast não funcionam igual Chromecast:** LG Cast não auto-lança a "Default Media Receiver" — `play_media` dá "no session is active". Usar **SSAP `play/pause/ff` direto** no app ativo (isso é "dar play no que está pausado").

## 6. Google Cast (camada secundária)
- `pychromecast` encontrada via mDNS/8009. Controle: **volume (0..1), mute, somente.** Lançamento de app/media é limitado no LG — usar SSAP para media.
- Volume via Cast: `set_volume(x/100)`. Mas SSAP é mais confiável.

## 7. Bibliotecas reaproveitáveis
- `lgtvremote-cli` (instala comando `lgtv`) — **preferida** (usa 3001 wss, PIN/PROMPT, WoL interno, persiste key).
- `pywebostv` — alternativa Pythonista (precisa `secure=True` manualmente pra 3001).
- `pychromecast` — volume/mute fallback + Cast discovery.

## 8. Template de reaplicação (novas TVs)
1. ARP scan + OUI → confirma LG.
2. Port scan: 3001 aberto + TLS.
3. `lgtv add IP` → pairing (aceitar na TV).
4. Salvar client-key em `scripts/keys/lgtv_<HOSTNAME>.json`.
5. Usar `lgtv --tv IP` com os comandos acima. Início volume 10.

## 9. Regra permanente de ouro
- **Volume: sempre iniciar 10, nunca no máximo. Usuário decide.**
