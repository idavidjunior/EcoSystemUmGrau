---
tags: [cldr, localizacao, neutra, one, padrao, regra]
aliases: [Localização de software: placeholders, plurais, gênero e esp]
date: 2026-08-15
---

# Localização de software: placeholders, plurais, gênero e espaço de UI

**Fonte:** localizacao

Localizar software exige projetar para que qualquer língua funcione. Use placeholders nomeados ({nome}) em vez de posicionais (%s): eles permitem reordenar as palavras: "{nome} salvou {arquivo}" flui em pt-BR, o que concatenação fixa não permite.

Plurais: não existe "{n} item(s)". O pt-BR tem três formas (1 item, 2 itens, muitos), implementadas via ICU MessageFormat ou a regra "one/other" do CLDR. Gênero: "novo arquivo" x "nova pasta" exigem variantes (selects do MessageFormat) ou reescrita neutra: "Você tem 3 arquivos".

Espaço: textos em pt-BR crescem ~20-30%; use botões elásticos e teste com strings longas. Armadilhas: hard-coded, datas/números concatenados e strings compostas que quebram em outra língua. Use Gettext/.po ou Transifex/Crowdin com contextos.
## Conexoes

- [[cluster-hub-traducao]]
- [[datas-horas-e-fuso-horário-no-brasil-ddmmaaaa-24h-brt]]
- [[localização-l10n-vs-internacionalização-i18n-vs-transcreatio]]
- [[números-moedas-r-e-percentuais-no-pt-br]]
- [[padrao-hub-padroes]]
- [[unidades-de-medida-e-convenções-brasileiras-m-kg-c-telefone-]]