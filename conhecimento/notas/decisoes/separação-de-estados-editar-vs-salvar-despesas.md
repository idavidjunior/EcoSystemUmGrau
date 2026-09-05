---
tags: [decisao, descrição, gravavam, opencode, pago, pendente]
aliases: [Separação de estados: Editar vs Salvar despesas]
date: 2026-08-14
---

# Separação de estados: Editar vs Salvar despesas

**Fonte:** opencode

## Problema

Quando usuário clicava **"Editar"** em um arquivo de despesas já salvo:
1. `currentExpenseFile` era setado imediatamente
2. Auto-saves (click "Pendente"/"Pago", editar descrição) gravavam no **arquivo original**
3. Ao clicar **"Salvar como novo"**, o original já estava modificado
4. O usuário perdia o arquivo original

## Solução

Separar dois estados:

- `editingExpenseFile` — arquivo carregado para edição (setado no "Editar", **não** grava auto-saves)
- `currentExpenseFile` — arquivo confirmado para auto-saves (só setado no **"Atualizar"**)

```java
// loadExpensesFromFile (via botão "Editar")
editingExpenseFile = file;  // Só carrega, não grava

// showSaveExpenseDialog - "Atualizar"
currentExpenseFile = editingExpenseFile;  // Confirma para auto-save
saveExpensesToFile(currentExpenseFile);
editingExpenseFile = null;
```

## Fluxo correto

| Ação | Auto-saves | "Atualizar" | "Salvar como novo" |
|------|-----------|-------------|-------------------|
| Editar arquivo A |
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]