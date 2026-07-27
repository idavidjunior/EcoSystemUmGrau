---
name: search-first
description: |
  Pesquisa orientada a evidências antes de implementar: docs primárias, código real, benchmarks e riscos.
  Trigger phrases: "search first", "research before code", "look up", "find solution"
allowed-tools: Read, Grep, Bash, WebSearch, WebFetch
version: 1.1.0
---

# Search First — Pesquisar Antes de Codar

## Objetivo
Reduzir retrabalho e risco técnico validando soluções existentes antes de escrever código novo.

## Protocolo de pesquisa
1. Defina a pergunta técnica em uma frase.
2. Priorize fonte primária (docs oficiais/spec/repo oficial).
3. Colete 2-3 abordagens viáveis com trade-offs.
4. Verifique sinais de manutenção (stars recentes, releases, issues abertas).
5. Registre decisão e descarte de alternativas.

## Ordem de fontes
1. Documentação oficial
2. Código fonte oficial/exemplos mantidos
3. RFCs, specs e notas de release
4. Issues/discussions do repositório
5. Conteúdo comunitário (StackOverflow, blogs)

## Critérios de escolha
- Compatibilidade com stack atual
- Custo operacional e lock-in
- Segurança e compliance
- Maturidade de ecossistema
- Facilidade de observabilidade e teste

## Checklist de validação
- A solução resolve o problema real (não só sintoma)?
- Existe benchmark/case confiável?
- Há plano de rollback?
- Equipe consegue manter sem especialista único?
- Dependência aceita nossa política de licenças?

## Anti-patterns
- Codar antes de formular hipótese
- Copiar snippet sem compreender limites
- Escolher por hype sem avaliar custo total
- Ignorar changelog e breaking changes

## Saída esperada do agente
- Resumo com 2-3 opções e trade-offs
- Recomendação final com justificativa
- Riscos conhecidos + mitigação
- Próximos passos de implementação