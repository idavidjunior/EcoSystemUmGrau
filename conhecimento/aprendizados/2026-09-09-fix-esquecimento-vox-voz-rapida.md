---
tipo: padrao
tags: [vox, bridge, voz-rapida, contexto, esquecimento, ancora, jarvis_bridge]
data: 2026-09-09
contexto: Usuário relatou que o Vox esquece o que acabou de responder — "respondo em cima da resposta dele e ele já esqueceu". Histórico real (conversa_unica.json) confirmou: usuário pediu um mapeamento e o Jarvis respondeu "Qual mapeamento você gostaria que eu faça?".
decisao: No _montar_contexto_voz (canal de voz rápido NVIDIA), a última troca Usuário+Jarvis agora entra por inteiro como âncora (início+fim com [...] se muito longa), com 8 pares de fio (era 6) e teto de 6000 chars, sem duplicar os prefixos Usuário:/Jarvis: que já vêm no histórico.
impacto: Modelos curtos da cadeia rápida passam a ver o fim da última resposta (onde ficam ofertas e perguntas), eliminando o "esquecimento" da fala imediatamente anterior. Testes adversariais + preflight aprovados; bridge reiniciada.
---

# Fix esquecimento do Vox no canal de voz rápida

## Sintoma (evidência no histórico real)

Em `conversa_unica.json`:
- Usuário: "Qual a nossa maior deficiência dentro do ecossistema um grau?"
- Jarvis: resposta longa (~1.300+ chars) terminando com oferta de retomar um mapeamento.
- Usuário: "Quero que você faça apenas um mapeamento..."
- Jarvis: "Qual mapeamento você gostaria que eu faça?" ← esqueceu o que ele mesmo ofereceu.

## Causa raiz

`_montar_contexto_voz` (jarvis_bridge.py) cortava CADA linha do histórico a 180 chars:
`linhas.append(f"- Usuário: {u[:180]}\n  Jarvis: {jr[:180]}")`

O fim da resposta do Jarvis (onde ficam ofertas, perguntas e fechamento) era sempre descartado. Com 6 pares e corte agressivo, o modelo de voz rápida (nemotron/gpt-oss/kimi, thinking off) não tinha o antecedente e respondia no genérico.

## Correção aplicada

1. Âncora conversacional: a última troca entra por inteiro. Se a resposta do Jarvis passa de 1600 chars, preserva `jr[:1000] + " [...] " + jr[-600:]` — o fim nunca é perdido.
2. Fio ampliado de 6 para 8 pares (`_PARES_CTX_VOZ = 8`).
3. Teto de segurança `_TETO_CTX_VOZ = 6000` chars para a seção de conversa.
4. Os itens do histórico já vêm com prefixo "Usuário:"/"Jarvis:" — o strip evita duplicação no contexto.

## Validação

- Testes adversariais: cliente None, histórico vazio, número ímpar de entradas, resposta Jarvis de 4.000 chars, 20 pares, entradas None → todos passaram.
- Cena real: âncora com a última resposta por inteiro confirmada contra `conversa_unica.json`.
- `python scripts/preflight_check.py`: TODOS OS TESTES PASSARAM.
- Bridge reiniciada (PID novo), log `bridge_log.txt` saudável.