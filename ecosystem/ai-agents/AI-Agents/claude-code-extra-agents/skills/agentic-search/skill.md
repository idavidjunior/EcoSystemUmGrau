---
name: agentic-search
description: |
  Navegação web autônoma para pesquisa e extração com estratégia API-first, DOM-first e fallback visual.
  Trigger phrases: "agentic search", "web navigation", "scraping", "playwright mcp", "stagehand"
allowed-tools: Read, Grep, Bash, WebSearch, WebFetch
version: 1.1.0
---

# Agentic Search — Navegação Web Autônoma com Ferramentas Reais

## Objetivo
Buscar e extrair informação atualizada com segurança, baixo custo e alta confiabilidade.

## Estratégia de execução
1. API-first: use API oficial sempre que existir.
2. DOM-first: automação determinística via seletores.
3. Vision fallback: só quando o DOM não for viável.

## Quando aplicar
- Pesquisa técnica em múltiplas fontes
- Extração estruturada de páginas sem API pública
- Rotinas repetitivas de consulta/navegação

## Ferramentas por modo
- API direta: mais barato e estável
- Playwright MCP: principal para DOM previsível
- Stagehand: alternativa de automação guiada
- Computer Use/Operator: último recurso para UI não padronizada

## Checklist de segurança
- Domínio validado e HTTPS
- Escopo de URLs permitido
- Sem credenciais/tokens em formulários
- Sem downloads executáveis
- Timeouts definidos por página/tarefa

## Checklist de qualidade
- Fonte primária registrada?
- Dados extraídos com seletor estável?
- Evidência de verificação cruzada?
- Resultado final rastreável para URL/trecho?

## Anti-patterns
- Ignorar API disponível
- Usar visão para casos que DOM resolve
- Navegar fora do escopo acordado
- Extrair sem validar origem

## Saída esperada do agente
- Plano de busca por fonte
- Estratégia API/DOM/fallback escolhida
- Dados extraídos com referências
- Riscos e limitações encontrados