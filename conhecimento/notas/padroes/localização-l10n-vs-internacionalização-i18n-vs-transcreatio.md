---
tags: [custo, erros, localizacao, padrao, parametrizados, qualidade]
aliases: [Localização (l10n) vs internacionalização (i18n) vs transcre]
date: 2026-08-17
---

# Localização (l10n) vs internacionalização (i18n) vs transcreation

**Fonte:** localizacao

Internacionalização (i18n) é a engenharia que prepara o produto para qualquer língua: código separado das strings, suporte a Unicode, plurais e formatos parametrizados. Localização (l10n) é a adaptação a um mercado: tradução, moeda, leis e convenções. Transcreation é recriar a mensagem para o mesmo efeito emocional — típica de marketing.

A regra de ouro: sem boa i18n, a l10n vira retrabalho. Sistema com textos embutidos no código exige recompilar por idioma; com locales (pt-BR, en-US), troca-se idioma sem tocar no código.

Exemplo: "{n} item(s)" é i18n ruim; a correta usa regras de plural do CLDR (pt-BR: um/outros). Localizar bem exige o mercado: dd/mm/aaaa, vírgula decimal, R$, país "BR". Saber onde termina a l10n e começa a transcreation evita erros de custo e qualidade.
## Conexoes

- [[cluster-hub-traducao]]
- [[datas-horas-e-fuso-horário-no-brasil-ddmmaaaa-24h-brt]]
- [[localização-de-software-placeholders-plurais-gênero-e-espaço]]
- [[números-moedas-r-e-percentuais-no-pt-br]]
- [[padrao-hub-padroes]]
- [[unidades-de-medida-e-convenções-brasileiras-m-kg-c-telefone-]]