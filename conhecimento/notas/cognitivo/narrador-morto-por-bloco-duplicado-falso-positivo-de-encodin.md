---
tags: [cognitivo, general, iniciar, perfeito, sai, system]
aliases: [Narrador morto por bloco duplicado; falso-positivo de encodi]
date: 2026-08-22
---

# Narrador morto por bloco duplicado; falso-positivo de encoding no log

**Dominio:** general

## Contexto
Investigação pedida pelo usuário sobre duas anomalias no log do system_guardian:
texto corrompido ("ap��s") e o narrador morrendo logo após iniciar em loop.

## Causa raiz 1 — narrador (real)
Entre os commits a2d996c4 (14:18) e adcfb195 (16:08) de 21/08/2026, um enxerto de
286 linhas duplicadas do próprio módulo entrou no narrador_desktop.py, quebrando um
try sem except na main() (SyntaxError linha 367). O processo morria instantaneamente
e o guardian reiniciava em loop a cada ~20s. Zero evolução legítima perdida:
diff com difflib.SequenceMatcher mostrou que a versão nova era apenas
versão boa + duplicata.

## Causa raiz 2 — texto corrompido (falso-positivo)
O guardian_log.txt é gravado corretamente em UTF-8 (FileHandler encoding="utf-8").
Lendo via Python open(encoding="utf-8"), o texto sai perfeito ("logo após iniciar").
O lixo vinha da camada de leitura: PowerShell 5.1 Get-Content assume ANSI sem BOM
e o console emite cp850. Arquivo íntegro; nada a corrigir no gravador.

## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]