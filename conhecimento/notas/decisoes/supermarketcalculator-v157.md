---
tags: [botões, decisao, dialog, dois, mostra, opencode]
aliases: [SupermarketCalculator v1.5.7]
date: 2026-09-03
---

# SupermarketCalculator v1.5.7

**Fonte:** opencode

## Novidade de UX (pedido do usuário)
Ao editar uma lista SALVA no app e finalizar, o dialog agora mostra dois botões:
"Salvar como novo" e "Atualizar". Para lista NOVA, continua apenas "Salvar".
Implementado no MainActivity.java em finishPurchase(): quando editingSession.isActive(),
adiciona um botão btnSaveAsNew ("Salvar como novo") além do btnUpdateList ("Atualizar"),
e omite o botão "Salvar" simples.

## 5 fixes no MainActivity.java
1. setButtonHidden: usa View.GONE em vez de View.VISIBLE com alpha 0.
2. onNameChanged: adicionado updateTotal() antes de saveCartState().
3. saveExpensesToFile: cria arquivo com timestamp quando currentExpenseFile é nulo.
4. loadExpensesFromFile: carrega arquivo mais recente por lastModified() em vez de hardcoded.
5. resetAllData: confirmado null check no RadioGroup.

## Fix de build.ps1
- $pwd.Path retorna null dentro de ForEach-Object. Corrigido usando $PSScriptRoot + loop foreach.
- CalcSimplesActivity.java excluído do build (referencia layout e IDs
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]