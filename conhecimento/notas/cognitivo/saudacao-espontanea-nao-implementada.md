---
tags: [cognitivo, ecosystemumgrau, general, informando, operante, tom]
aliases: [saudacao espontanea nao implementada]
date: 2026-08-23
---

# saudacao espontanea nao implementada

**Dominio:** general

## Problema

A cláusula pétrea **AUTOAPRESENTAÇÃO AUTOMÁTICA NA PRIMEIRA MENSAGEM DE CADA SESSÃO** não está sendo cumprida. O fluxo atual:

1. Usuário abre nova sessão
2. Agente responde direto ao pedido
3. **FALTA**: saudação espontânea curta confirmando operacionalidade

## Requisito da Cláusula

> Fluxo obrigatório na primeira mensagem de qualquer sessão (antes de atender o pedido):
> 1. Executar silenciosamente: `python scripts/runtime_boot.py --check`
> 2. Se integridade OK: iniciar a resposta com uma confirmação **CURTA e ESPONTÂNEA (máximo 3-4 linhas)**, variando o tom a cada sessão, informando que o EcoSystemUmGrau está ativo e operante. Incluir leve contexto (projeto ativo, memória, pendências) quando disponível.
> 3. Se houver problema de integridade: informar brevemente o que falhou e o que foi corrigido antes de atender o pedido.
> 4. Depois da confirmação curta, atender o pedido normalmente.

## Implementação Necessária

Criar hook/mecanismo que:
1. Detecte primeira mensag
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]