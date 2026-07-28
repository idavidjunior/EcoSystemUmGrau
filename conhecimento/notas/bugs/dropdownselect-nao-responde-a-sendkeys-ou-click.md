---
tags: [bug, treinamentonavegacao]
aliases: [Dropdown<select> nao responde a send_keys ou click]
date: 2026-07-28
---

# Bug: Dropdown<select> nao responde a send_keys ou click

**Projeto:** treinamento_navegacao

## Causa Raiz
Selects estilizados (custom dropdowns) substituem o elemento <select> nativo por uma div com opcoes ocultas

## Correcao
Clicar no select para abrir, depois clicar na opcao pelo texto visivel; se nao funcionar, usar JS para setar valor e disparar evento change
