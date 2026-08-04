---
tipo: decisao
tags: [tts, edge-tts, ssml, naturalidade, jarvis, pronuncia, clausula-petrea]
data: 2026-08-02
contexto: ClÃ¡usula pÃ©trea exige comunicaÃ§Ã£o contÃ­nua em Ã¡udio. O edge-tts jÃ¡ suporta SSML completo e o ecossistema precisa evoluir pronÃºncia e naturalidade sem trocar de TTS.
decisao: "Adicionei _ssml_enriquecer() em scripts/jarvis_bridge.py e mudei a ordem em gerar_audio(): phoneme primeiro sobre texto puro, depois SSML enriquece naturalidade."
impacto: "NÃºmeros, percentuais, ordinais e datas lidos naturalmente; pausas de respiraÃ§Ã£o; Ãªnfase em alertas de recursos. test_vox passa (3 falhas preexistentes ambientaiss). preflight OK."
---

# EvoluÃ§Ã£o do TTS Jarvis â€” naturalidade via SSML

## Contexto
ClÃ¡usula pÃ©trea exige comunicaÃ§Ã£o contÃ­nua em Ã¡udio. O edge-tts jÃ¡ usado pela bridge
suporta SSML completo (testado: `say-as`, `break`, `prosody`, `emphasis`, `phoneme`,
`sub`). A pergunta era evoluir pronÃºncia e naturalidade sem trocar de TTS â€” o edge-tts
Ã© a melhor voz PT-BR neural gratuita do planeta.

## DecisÃ£o
Adicionei `_ssml_enriquecer()` em `scripts/jarvis_bridge.py` e mudei a ordem em
`gerar_audio()`:

  sanitizar â†’ melhorar_fala (texto puro) â†’ aplicar_phonemes (texto puro + `<phoneme>`)
  â†’ _ssml_enriquecer (envolve em SSML) â†’ edge-tts stream.

### Por que a ordem importa
`aplicar_phonemes` usa regex `\\b(palavra)\\b` sobre o texto. Se aplicado DEPOIS do
SSML (que jÃ¡ tem tags `<say-as>`), o regex pode casar palavras dentro de atributos
(`number`, `interpret`) e corromper as tags. Aplicar phoneme sobre texto PURO antes e
mais seguro â€” a camada SSML apenas enriquece o texto jÃ¡ fonetizado.

## Recursos SSML aplicados
| Regra | Exemplo | Ãudio |
|-------|---------|-------|
| `say-as` percent | `85 %` | "oitenta e cinco por cento" |
| `say-as` ordinal | `1Âº` | "primeiro" |
| `say-as date dmy` | `31/07/2026` | "trinta e um de julho de 2026" |
| `break` abertura | "EntÃ£o, â€¦" | pausa respiraÃ§Ã£o 350ms |
| `break` entre frases | ". PrÃ³xima frase" | pausa 150ms (ritmo humano) |
| `emphasis` (alertas) | "CPU em 85%" | Ãªnfase leve |
| `phoneme` (IPA) | david, jarvis | pronÃºncia garantida via `pronuncias.json` |

## Bug aprendido
Regex de porcentagem `\\b(\\d{1,3})\\s*%\\b` **nunca casava** `85%` â€” porque `%` e o
espaÃ§o seguinte nÃ£o sÃ£o word-chars, o `\\b` Ã  direita nÃ£o existia. Fix: regex sem `\\b`
final: `(\\d{1,3})\\s*%|(\\d{1,3})\\s*por cento`.

## ValidaÃ§Ã£o
- `test_vox`: fix_punctuation 7/7, horas_para_fala 5/5, normalizar_hora_display 10/10.
  (`caminho_rapido`: 3 falhas preexistentes sÃ£o ambientais â€” dependem de servidores
  WebSocket offline â€” nÃ£o relacionadas a esta mudanÃ§a.)
- `preflight_check.py`: TODOS TESTES PASSARAM.
- Ãudio gerado via `gerar_audio()` e tocado via `vox_audio.py falar`: OK.

## PrÃ³ximos passos (nÃ£o implementados)
- `prosody rate/pitch` dinÃ¢mico por tipo de frase (pergunta ascendente) â€” o edge-tts
  jÃ¡ inclina a entonaÃ§Ã£o no `?`, mas `prosody` dÃ¡ controle fino.
- DicionÃ¡rio de pronÃºncia autoevolutivo: toda interaÃ§Ã£o "pronuncie X" registra IPA
  automaticamente (loop jÃ¡ documentado em `JARVIS_SYSTEM.md`).

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]]