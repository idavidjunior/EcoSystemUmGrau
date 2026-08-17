# 2026-08-17: CAR-BT — controle total via adb (Bluetooth automotivo)

**Categoria:** padrao
**Tags:** bluetooth, car-bt, adb, android, avrcp, a2dp, controle
**Data:** 2026-08-17

## Contexto

O usuário pediu para aprender a controlar o aparelho Bluetooth CAR-BT conectado ao celular (Xiaomi, Android via adb 100.64.71.9:5555), sem mexer em nada — apenas mapear acesso total, saber tudo sobre ele e alcançar todos os controles.

## O aparelho

- Nome: CAR-BT
- Endereço: `36:84:10:21:D8:10` (BR/EDR)
- Tipo: A2DP sink (receptor de áudio) + HFP (HeadsetService/telefonia)
- Codec A2DP: SBC (44100Hz, 16 bits, estéreo); codec config `1f000000`
- A2DP offload: habilitado (`A2dpOffloadEnabled: true`)
- AVRCP Controller versão: 261 (1.6), features 79 (controle de mídia completo)
- É o `mActiveDevice` dos perfis HeadsetService e A2dpService
- Endereço não silenciado (`Is silenced? false`)

## Estado de áudio (somente leitura)

- `dumpsys audio`: `mBluetoothName=CAR-BT`; device `bt_a2dp(80)` ativo
- `APM Connected device (A2DP sink only): type:0x80 addr:0x80:36:84:10:21:D8:10`
- Active communication device (output): `type:bt_a2dp addr:36:84:10:21:D8:10 name:CAR-BT`
- STREAM_MUSIC volume grupo: min 0, max 15; corrente no bt_a2dp visível no dumpsys (ex.: 11)
- Streams ativos: bt_a2dp em STREAM_MUSIC, STREAM_VOICE_CALL, STREAM_BLUETOOTH_SCO

## Controle de mídia (AVRCP)

- Sessão de mídia ativa: `com.mp3player.debug` / Mp3PlayerMediaSession (ownerPid 25942, uid 10496)
- Música tocando: "Make It Right (feat. Dante Bowe, Todd Dulaney, Jekalyn Carr & Mav City Gospel Choir)" — Maverick City Music, álbum "Jubilee: Juneteenth Edition"
- PlaybackState: state=2 (playing), position 9542, actions=310, velocidade 1.0
- `Global priority session: com.android.server.telecom/HeadsetMediaButton` (media button receiver do BT)
- `OnMediaKeyEventSessionChangedListener: 1 listener de com.android.bluetooth` (o celular envia media keys ao carro)
- Outra sessão presente: `com.openai.chatgpt/VoiceModeService` (state=1 paused)

## Comandos de acesso/controle (via adb)

- Estado geral: `adb shell dumpsys bluetooth_manager`
- Estado de áudio/volume: `adb shell dumpsys audio`
- Sessões de mídia: `adb shell dumpsys media_session`
- Controle de mídia (envia ao carro): `adb shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE` (85), `KEYCODE_MEDIA_NEXT` (87), `KEYCODE_MEDIA_PREVIOUS` (88), `KEYCODE_MEDIA_STOP` (86), `KEYCODE_HEADSETHOOK` (79), `KEYCODE_MEDIA_PLAY` (126), `KEYCODE_MEDIA_PAUSE` (127), `KEYCODE_MEDIA_REWIND` (89), `KEYCODE_MEDIA_FAST_FORWARD` (90)
- Volume: `adb shell media volume --show --stream 3 --set N` (N 0-15), ou `--adj` para relativo
- TOQUE: esses comandos alteram o estado. Somente executar quando o usuário autorizar explicitamente.

## Impacto

- Acesso total mapeado: conexão (HFP+A2DP ativos), áudio (codec/volume/streams), mídia (AVRCP + sessão ativa + media keys).
- Nenhum comando de escrita foi executado nesta sessão; tudo leitura.

## Referências

- `dumpsys bluetooth_manager` (perfis HeadsetService, A2dpService, AVRCP, bonded devices)
- `dumpsys audio` (mBluetoothName, DeviceInfo bt_a2dp, streams, volume groups)
- `dumpsys media_session` (Mp3PlayerMediaSession, HeadsetMediaButton, OnMediaKeyEventSessionChangedListener)
- `adb shell input keyevent` (media keycodes) e `adb shell media volume` (stream 3 = MUSIC)
