---
tags: [cognitivo, general, limpeza, rmtree, tem, viva]
aliases: [Snapshots "corrompidos" do opencode: referência no banco dec]
date: 2026-08-22
---

# Snapshots "corrompidos" do opencode: referência no banco decide, não heurística

**Dominio:** general

## Contexto
Usuário apontou a mensagem recorrente "[SNAP] 2 snapshot(s) corrompido(s) - limpeza
adiada (desktop ativo)" no log do guardian. Investigação revelou três camadas.

## Causas encontradas
1. Falso positivo estrutural: o detector marcava o subdiretório `objects` interno
   do próprio git (por conter info/pack) como snapshot corrompido.
2. Snapshot real mas EM USO: a sessão "Jarvis greeting" (criada 20/08, atualizada
   hoje) referencia o hash em 27 partes da tabela part. Estrutura parcial sem HEAD
   é estado normal de snapshot em uso pelo opencode.
3. Meu primeiro patch (limpar "órfãos" com mtime >6h mesmo com desktop ativo)
   estava ERRADO: mtime antigo não prova abandono — sessão viva criada ontem tem
   snapshot com mtime de ontem.

## Quase-acidente e o que salvou
A execução intermediária apagou hooks/info/refs do snapshot da sessão viva; só os
packfiles sobreviveram porque processos OpenCode seguravam handle (rmtree parcial).
Se os handles não existissem, teria corrompi
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]