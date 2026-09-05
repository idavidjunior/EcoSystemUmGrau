---
tags: [f2c811, flutuante, janela, opencode, padrao, vivo]
aliases: [Estilo por pedido (Power BI implementado)]
date: 2026-08-24
---

# Estilo por pedido (Power BI implementado)

**Fonte:** opencode

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
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]