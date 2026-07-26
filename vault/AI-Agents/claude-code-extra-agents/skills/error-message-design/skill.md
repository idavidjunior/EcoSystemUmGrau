---
name: error-message-design
description: |
  Design de mensagens de erro claras e acionáveis para usuários finais e developers.
  Trigger phrases: "error message", "mensagem de erro", "UX de erro", "debuggability"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Error Message Design — Clareza que Resolve

## Objetivo
Transformar erros em orientação útil, reduzindo suporte e retrabalho.

## Estrutura recomendada
- O que aconteceu (linguagem simples)
- Por que aconteceu (quando conhecido)
- Como resolver agora (passo acionável)
- Como obter ajuda (código/correlação)

## Camadas de mensagem
- Usuário final: foco em ação e tranquilidade
- Operação/suporte: contexto de ambiente
- Engenharia: stack + correlation ID + metadata

## Boas práticas
- Mensagens específicas por cenário
- Evitar tom culpabilizador
- Incluir estado recuperável quando possível
- Preservar privacidade (sem vazar dados sensíveis)

## Checklist
- Dá para agir sem abrir ticket?
- O texto evita jargão desnecessário?
- Existe código de erro estável?
- O log correspondente permite diagnóstico rápido?

## Anti-patterns
- "Algo deu errado" sem contexto
- Expor stack interna ao usuário final
- Mensagens inconsistentes entre canais
- Ocultar erro real por excesso de abstração

## Saída esperada do agente
- Catálogo de erros por domínio
- Template padrão de mensagem
- Regras de telemetria/correlation ID
- Plano de teste de UX de erro