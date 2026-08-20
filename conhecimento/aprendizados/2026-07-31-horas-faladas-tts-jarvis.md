# Aprendizado — 2026-07-31 — Horas faladas corretamente no TTS do Jarvis

## Contexto
- O edge-tts lia `21:44` de forma errada (como razão/hora digital). O usuário trouxe 3 estratégias e recomendou a **#1: substituição de texto via código antes do TTS**.

## O que foi feito (`scripts/jarvis_bridge.py`)
- Em `melhorar_fala()` (preparação do texto para o áudio), **antes** da troca de `:` por vírgula (que comeria o tempo):
  - `(\d{1,2}):00\b` â†’ `\1 horas em ponto` (ex.: "22:00" â†’ "22 horas em ponto")
  - `(\d{1,2}):(\d{2})\b` â†’ `\1 horas e \2` (ex.: "21:44" â†’ "21 horas e 44")
- Aplica-se apenas ao texto do ÃUDIO; a tela continua mostrando `21:44`.
- `test_vox.py`: novo `teste_horas_para_fala()` (5 casos); `JARVIS_SYSTEM.md` documentado.

## Heurísticas registradas
- **Ordem importa**: a regra de horas deve rodar ANTES de qualquer normalização de `:` (virgula para respiração do TTS), senão o tempo vira "21,44".
- **TTS é uma conversa separada da tela**: texto_tela (formatado) e texto_fala (expandido) podem divergir — quem mostra é o JSON de resposta (texto original); quem lê é o texto pós-`melhorar_fala()`.

## Estado
- `melhorar_fala`: 5/5 OK; `fix_punctuation`: 7/7 OK (regressão zero).
- `gerar_audio("São 21:44.")` e `("Agora são 22:00.")` geram áudio (smoke OK).
- Saudação real pós-restart já fala horas naturalmente ("...23 e 29 em São Paulo...").
