---
tipo: padrao
tags: [visual, power-bi, dashboard, estilo-por-pedido]
data: 2026-08-24
contexto: David instruiu que o estilo do visual corresponda ao pedido e sugeriu aprender Power BI para criacoes de dados
decisao: Novo tipo 'dashboard' no gerador_visual.py replicando a identidade visual Power BI; preferencia registrada na memoria #513
impacto: Pedidos de dados/financeiro/analytics abrem painel estilo Power BI em janela flutuante; mockups mantem moldura de celular
---

# Estilo por pedido (Power BI implementado)

## Regra
O estilo do visual acompanha a natureza do pedido:
- Dados/financeiro/analytics -> tipo "dashboard" (tema Power BI)
- Telas de aplicativo -> tipo "mockup" (moldura celular)
- Numeros soltos -> kpi; comparacoes -> barras; series -> tabela

## Tema Power BI implementado
Fundo #201F1F, tiles #252423 com sombra suave, destaque amarelo #F2C811,
header com faixa amarela e marca POWER BI STYLE.
Componentes SVG puros sem dependencias: donut (stroke-dasharray),
gauge semicircular (path + dasharray), barras horizontais coloridas,
tabela escura.

## Uso
python scripts/gerador_visual.py --titulo "..." --tipo dashboard \
  --arquivo dados.json --mostrar
JSON: subtitulo, kpis[], graficos[] {tipo: donut|gauge|barras|tabela,
largura: meia|inteira}, notas[]

## Teste
Painel Tesouro Selic gerado (7733 bytes) e aberto vivo na janela flutuante
via WMI (pid confirmado).
