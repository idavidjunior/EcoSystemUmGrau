# Aprendizado â€” 2026-07-31 â€” Horas faladas corretamente no TTS do Jarvis

## Contexto
- O edge-tts lia `21:44` de forma errada (como razÃ£o/hora digital). O usuÃ¡rio trouxe 3 estratÃ©gias e recomendou a **#1: substituiÃ§Ã£o de texto via cÃ³digo antes do TTS**.

## O que foi feito (`scripts/jarvis_bridge.py`)
- Em `melhorar_fala()` (preparaÃ§Ã£o do texto para o Ã¡udio), **antes** da troca de `:` por vÃ­rgula (que comeria o tempo):
  - `(\d{1,2}):00\b` â†’ `\1 horas em ponto` (ex.: "22:00" â†’ "22 horas em ponto")
  - `(\d{1,2}):(\d{2})\b` â†’ `\1 horas e \2` (ex.: "21:44" â†’ "21 horas e 44")
- Aplica-se apenas ao texto do ÃUDIO; a tela continua mostrando `21:44`.
- `test_vox.py`: novo `teste_horas_para_fala()` (5 casos); `JARVIS_SYSTEM.md` documentado.

## HeurÃ­sticas registradas
- **Ordem importa**: a regra de horas deve rodar ANTES de qualquer normalizaÃ§Ã£o de `:` (virgula para respiraÃ§Ã£o do TTS), senÃ£o o tempo vira "21,44".
- **TTS Ã© uma conversa separada da tela**: texto_tela (formatado) e texto_fala (expandido) podem divergir â€” quem mostra Ã© o JSON de resposta (texto original); quem lÃª Ã© o texto pÃ³s-`melhorar_fala()`.

## Estado
- `melhorar_fala`: 5/5 OK; `fix_punctuation`: 7/7 OK (regressÃ£o zero).
- `gerar_audio("SÃ£o 21:44.")` e `("Agora sÃ£o 22:00.")` geram Ã¡udio (smoke OK).
- SaudaÃ§Ã£o real pÃ³s-restart jÃ¡ fala horas naturalmente ("...23 e 29 em SÃ£o Paulo...").
