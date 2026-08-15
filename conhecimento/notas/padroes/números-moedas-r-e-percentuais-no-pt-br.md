---
tags: [1234, ambíguo, iso, localizacao, localizada, padrao]
aliases: [Números, moedas (R$) e percentuais no pt-BR]
date: 2026-08-15
---

# Números, moedas (R$) e percentuais no pt-BR

**Fonte:** localizacao

No pt-BR, o separador decimal é a vírgula e o de milhares, o ponto: 1.234,56. "1,234.56" é erro clássico de interface não localizada e vira mais de 1234 em vez de 1,23. Moeda: o símbolo R$ vem ANTES, sem espaço: R$ 1.234,56. Em sistemas multi-moeda use o código ISO "BRL 1.234,56". Percentual: 23,5%.

Use Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'}) em vez de concatenar strings. Armadilha de casas decimais: 0,5 deve aparecer como R$ 0,50 — nunca omita centavos. Em código, o ponto decimal em pt-BR é erro grave: "1.5" vira 150% se interpretado como milhar. Em textos corridos, evite o ponto de milhar quando ambíguo: "mais de 1200 pessoas".
## Conexoes

- [[cluster-hub-traducao]]
- [[datas-horas-e-fuso-horário-no-brasil-ddmmaaaa-24h-brt]]
- [[localização-de-software-placeholders-plurais-gênero-e-espaço]]
- [[localização-l10n-vs-internacionalização-i18n-vs-transcreatio]]
- [[padrao-hub-padroes]]
- [[unidades-de-medida-e-convenções-brasileiras-m-kg-c-telefone-]]