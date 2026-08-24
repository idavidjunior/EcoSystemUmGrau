---
tipo: erro
tags: [narrador, system-guardian, syntax-error, encoding, git]
data: 2026-08-21
---

# Narrador morto por bloco duplicado; falso-positivo de encoding no log

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

## Correção aplicada
1. git show a2d996c4:scripts/narrador_desktop.py extraído via python subprocess
   (bytes puros — redirecionamento > do PowerShell grava UTF-16 e corrompe).
2. Escrita atômica tmp + os.replace.
3. py_compile OK; execução manual VIVA após 8s (antes morria na hora).
4. Guardian retomou sozinho: "Narrador reiniciado e confirmado rodando", PID ativo.

## Impacto
Voz do ecossistema restaurada; ciclo infinito de spawn/morte do narrador encerrado
(isso também aliviava RAM). Gate em modo MANUAL: mudança pendente de commit pelo usuário.

## Lições registradas
- Validar encoding com python open(utf-8) antes de culpar quem grava o log.
- Extrair conteúdo do git sempre via python subprocess, nunca via > do PS 5.1.
- Diffr estrutural entre versões do git separa acidente de evolução antes de restaurar.

## Conexoes

- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]