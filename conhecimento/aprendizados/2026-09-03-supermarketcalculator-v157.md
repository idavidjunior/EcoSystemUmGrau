---
tipo: decisao
tags: [android, sdk-puro, supermarketcalculator, build, release]
data: 2026-09-03
contexto: Auditoria e correção de bugs no app Android SupermarketCalculator (SDK puro). Usuário pediu para manter sequência de versões no versionamento.
decisao: Corrigir 5 bugs no MainActivity, consertar build.ps1 e adicionar opções "Salvar como novo"/"Atualizar" ao editar lista salva.
impacto: App mais funcional e versão v1.5.7 gerada e versionada.
---

# SupermarketCalculator v1.5.7

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
- CalcSimplesActivity.java excluído do build (referencia layout e IDs que não existem mais).

## Versionamento seguido
- Mantida a sequência v1.5.X (v1.5.7).
- AndroidManifest.xml: versionCode 13, versionName 1.5.7 (incremento +1 a cada build).
- APK em releases/SupermarketCalculator-v1.5.7.apk.
- RELEASE.md atualizado com linha do histórico.
