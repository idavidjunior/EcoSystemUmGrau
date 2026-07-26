# /navigate — Navegador Web Autônomo
Aciona o agente web-navigator para buscar informações, extrair dados e automatizar tarefas na internet.

## Uso
`/navigate`

## O que acontece
1. Verifica se o site tem API (sempre prefere API direta)
2. Navega via DOM determinístico (Playwright MCP)
3. Usa visão computacional como fallback
4. Extrai dados estruturados
5. Retorna com fontes, datas e verificação de consistência

## Quando usar
- Buscar informações atualizadas na internet
- Extrair dados de sites sem API
- Pesquisar documentação técnica
- Coletar preços, produtos, comparações

## Exemplo
`/navigate`
"Quais os 3 modelos de embedding mais baratos por token? Compare com fontes oficiais."
