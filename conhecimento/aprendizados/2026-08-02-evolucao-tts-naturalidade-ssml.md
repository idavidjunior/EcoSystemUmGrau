---
tipo: decisao
tags: [tts, edge-tts, ssml, naturalidade, jarvis, pronuncia, clausula-petrea]
data: 2026-08-02
contexto: Cláusula pétrea exige comunicação contínua em áudio. O edge-tts já suporta SSML completo e o ecossistema precisa evoluir pronúncia e naturalidade sem trocar de TTS.
decisao: "Adicionei _ssml_enriquecer() em scripts/jarvis_bridge.py e mudei a ordem em gerar_audio(): phoneme primeiro sobre texto puro, depois SSML enriquece naturalidade."
impacto: "Números, percentuais, ordinais e datas lidos naturalmente; pausas de respiração; ênfase em alertas de recursos. test_vox passa (3 falhas preexistentes ambientaiss). preflight OK."
---

# Evolução do TTS Jarvis — naturalidade via SSML

## Contexto
Cláusula pétrea exige comunicação contínua em áudio. O edge-tts já usado pela bridge
suporta SSML completo (testado: `say-as`, `break`, `prosody`, `emphasis`, `phoneme`,
`sub`). A pergunta era evoluir pronúncia e naturalidade sem trocar de TTS — o edge-tts
é a melhor voz PT-BR neural gratuita do planeta.

## Decisão
Adicionei `_ssml_enriquecer()` em `scripts/jarvis_bridge.py` e mudei a ordem em
`gerar_audio()`:

  sanitizar → melhorar_fala (texto puro) → aplicar_phonemes (texto puro + `<phoneme>`)
  → _ssml_enriquecer (envolve em SSML) → edge-tts stream.

### Por que a ordem importa
`aplicar_phonemes` usa regex `\\b(palavra)\\b` sobre o texto. Se aplicado DEPOIS do
SSML (que já tem tags `<say-as>`), o regex pode casar palavras dentro de atributos
(`number`, `interpret`) e corromper as tags. Aplicar phoneme sobre texto PURO antes e
mais seguro — a camada SSML apenas enriquece o texto já fonetizado.

## Recursos SSML aplicados
| Regra | Exemplo | Áudio |
|-------|---------|-------|
| `say-as` percent | `85 %` | "oitenta e cinco por cento" |
| `say-as` ordinal | `1º` | "primeiro" |
| `say-as date dmy` | `31/07/2026` | "trinta e um de julho de 2026" |
| `break` abertura | "Então, …" | pausa respiração 350ms |
| `break` entre frases | ". Próxima frase" | pausa 150ms (ritmo humano) |
| `emphasis` (alertas) | "CPU em 85%" | ênfase leve |
| `phoneme` (IPA) | david, jarvis | pronúncia garantida via `pronuncias.json` |

## Bug aprendido
Regex de porcentagem `\\b(\\d{1,3})\\s*%\\b` **nunca casava** `85%` — porque `%` e o
espaço seguinte não são word-chars, o `\\b` à direita não existia. Fix: regex sem `\\b`
final: `(\\d{1,3})\\s*%|(\\d{1,3})\\s*por cento`.

## Validação
- `test_vox`: fix_punctuation 7/7, horas_para_fala 5/5, normalizar_hora_display 10/10.
  (`caminho_rapido`: 3 falhas preexistentes são ambientais — dependem de servidores
  WebSocket offline — não relacionadas a esta mudança.)
- `preflight_check.py`: TODOS TESTES PASSARAM.
- Áudio gerado via `gerar_audio()` e tocado via `vox_audio.py falar`: OK.

## Próximos passos (não implementados)
- `prosody rate/pitch` dinâmico por tipo de frase (pergunta ascendente) — o edge-tts
  já inclina a entonação no `?`, mas `prosody` dá controle fino.
- Dicionário de pronúncia autoevolutivo: toda interação "pronuncie X" registra IPA
  automaticamente (loop já documentado em `JARVIS_SYSTEM.md`).
