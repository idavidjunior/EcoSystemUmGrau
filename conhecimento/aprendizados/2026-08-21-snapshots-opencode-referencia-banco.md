---
tipo: erro
tags: [opencode-resilience, snapshots, falso-positivo, seguranca-de-dados]
data: 2026-08-21
---

# Snapshots "corrompidos" do opencode: referência no banco decide, não heurística

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
Se os handles não existissem, teria corrompido o snapshot de uma sessão ativa.
Impacto residual honesto: aquela sessão perde diff/revert via git interno;
mensagens seguras no opencode.db.

## Correção definitiva (opencode_resilience.py)
1. HEX_NAME regex: só nome hex 32-64 é raiz de snapshot; internals git ignorados.
2. Dedupe: diretório aninhado sob snapshot já detectado não re-reporta.
3. snapshot_referenciado(): consulta part/message LIKE pelo hash (prefixo 24).
   Citado = nunca tocar. Falha ao consultar = assume referenciado (fail-safe).
4. Só órfãos com zero referência são limpos, e apenas com desktop fechado.

## Lições permanentes
- Fonte de verdade para "está em uso?" é o banco do aplicativo, não o filesystem.
- mtime/idade nunca bastam para classificar lixo.
- Uma trava inesperada de arquivos pode ser a única defesa entre você e um
  desastre: investigue antes de contornar.

## Conexoes

- [[cluster-hub-ecossistema]]