---
tags: [decidir, decisao, descrição, finance, gravasse, opencode]
aliases: [Separação de estados: Editar vs Salvar despesas]
date: 2026-08-14
---

# Separação de estados: Editar vs Salvar despesas

**Fonte:** opencode

---
tipo: decisao
tags: [android, supermarket-calculator, despesas, persistencia, bug-fix, editing-state]
data: 2026-08-14
contexto: SupermarketCalculator - Bug: auto-save de despesas sobrescrevia arquivo original durante edição
contexto_detalhado: Quando usuário clicava "Editar" num arquivo de despesas já salvo na aba Finance, o `currentExpenseFile` era setado imediatamente. Isso fazia com que qualquer auto-save (clicar em "Pendente"/"Pago", editar descrição) já gravasse no arquivo original antes do usuário decidir "Atualizar" ou "Salvar como novo". O arquivo original era modificado indevidamente.
decisao: Separar em dois estados distintos: (1) `editingExpenseFile` - arquivo sendo editado visualmente, NÃO recebe auto-saves; (2) `currentExpenseFile` - arquivo confirmado para auto-saves, só é setado quando usuário clica explicitamente em "Atualizar". Auto-saves (saveExpensesToFile()) usam `currentExpenseFile` se setado, senão default `despesas.json`.
impacto: O arquivo original só é modificado quando usuário clica explicitamente em "Atualizar". "Salvar como novo" cria arquivo novo mantendo original intacto. Auto-saves durante edição vão para `despesas.json` (arquivo temporário de trabalho).
arquivo: Projectos/SupermarketCalculator/src/com/supermarket/calculator/MainActivity.java
---

# Separação de estados: Editar vs Salvar despesas

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
| Editar arquivo A | → `despesas.json` (não mexi no A) | Grava no **A** | Cria **B** novo, **A** intacto |
| Novo do zero | → `despesas.json` | N/A | Cria timestamp |
| Depois de "Atualizar" | → arquivo **A** | Grava no **A** | Cria novo, **A** intacto |

## Arquivo

`Projetos/SupermarketCalculator/src/com/supermarket/calculator/MainActivity.java`

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]