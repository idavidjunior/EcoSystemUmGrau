# Hora na tela vs hora no Ã¡udio (Jarvis)

- **Data:** 31/07/2026
- **SessÃ£o:** ImplementaÃ§Ã£o de `normalizar_hora_display()` na bridge

## Problema
O LLM reescrevia a hora do briefing/saudaÃ§Ã£o em forma falada ("23 horas e 29",
"22 horas em ponto", "meia-noite") no prÃ³prio TEXTO exibido no app. O usuÃ¡rio
deixou claro: **o formato exibido deve continuar `21:44`; sÃ³ a PRONÃšNCIA do
Jarvis precisava ser corrigida.**

## SoluÃ§Ã£o (divisÃ£o de responsabilidades)
- `melhorar_fala(texto)` â†’ transforma `HH:MM` em "HH horas e MM" / "HH horas em
  ponto" **apenas para o Ã¡udio** (jÃ¡ era chamado dentro de `gerar_audio()`).
- `normalizar_hora_display(texto)` â†’ reverte formas faladas para `HH:MM` no
  **texto exibido** (`text` do JSON enviado ao app).
- Fluxo em `lidar()`: `texto_tela = normalizar_hora_display(texto)` â†’
  `ws.send({"text": texto_tela, "audio": gerar_audio(texto_tela)})`.
  O Ã¡udio nasce do texto da tela (round-trip garantido).

## Regras do normalizador
1. `horas?/hs? + e + MM` â†’ `HH:MM` ("23 horas e 29")
2. `h + MM` â†’ `HH:MM` ("09h30")
3. `horas?/hs? + em ponto` â†’ `HH:00` ("22 horas em ponto")
4. `horas?/hs? + MM` (sem "e") â†’ `HH:MM` ("09 hs 30")
5. `horas?/hs?` (sÃ³ hora) â†’ `HH:00` ("22h")
6. `HH e MM` (sem palavra "horas", sÃ³ se 0<=HH<=23 e MM<=59) â†’ `HH:MM`
   ("23 e 29"), preservando "Faltam 2 e 3 coisas" intacto.

## PadrÃ£o capturado
- O LLM fala horas por extenso no texto; a tela nÃ£o deve depender do LLM para
  formatar hora â€” a ponte normaliza. Sempre separar **texto de exibiÃ§Ã£o** do
  **texto de sÃ­ntese** (TTS) quando houver transformaÃ§Ãµes linguÃ­sticas.

## ValidaÃ§Ã£o
- 10 casos de tela + 3 round-trips (telaâ†’fala) em `test_vox.py`
  (`teste_normalizar_hora_display()`); 22/22 offline no total.
- WebSocket real com saudaÃ§Ã£o e respostas do LLM sem regressÃ£o.
