---
tags: [falta, framework, inconsistente, pos, validacao]
aliases: [Metodo dos 5 Porques (5 Whys)]
date: 2026-08-05
---

# Metodo dos 5 Porques (5 Whys)

Tecnica de analise de causa raiz: pergunte 'por que?' 5 vezes para cada sintoma.

Sintoma -> Por que? -> Causa nivel 1 -> Por que? -> Causa nivel 2 -> ... -> Causa raiz. Exemplo: 'O APK crasha ao abrir' -> Por que? 'Activity nao encontrada' -> Por que? 'AndroidManifest sem entry point' -> Por que? 'Build script nao gerou manifest correto' -> Por que? 'Parametro de output name mudou e script ficou inconsistente' -> Por que? 'Nao havia teste para validar o manifest apos build'. A causa raiz NAO e o crash e sim a falta de validacao pos-build. Corrigir isso previne a classe inteira de bugs, nao apenas este.
## Conexoes

- [[cluster-hub-cognicao]]
- [[framework-hub-frameworks]]