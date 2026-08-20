---
tags: [localizacao, miles, padrao, parênteses, rejeitam, rígidas]
aliases: [Unidades de medida e convenções brasileiras (m, kg, °C, tele]
date: 2026-08-20
---

# Unidades de medida e convenções brasileiras (m, kg, °C, telefone, endereço)

**Fonte:** localizacao

O Brasil usa o SI: metros (m), quilogramas (kg), litros (L) e grau Celsius (°C) — inclusive em interfaces. Velocidade em km/h é obrigatória. Altura usa vírgula decimal: "1,75 m".

Telefone: formato nacional (11) 91234-5678, com DDD e 9 nos celulares; internacional +55 11 91234-5678. Endereço segue a ordem: logradouro, número, complemento, bairro, cidade — UF, CEP 00000-000. Não assuma formato norte-americano.

Armadilhas: converter unidades sem necessidade, usar "lbs" ou "miles", e regex rígidas de telefone que rejeitam +55 ou parênteses. Valide com regex flexível e normalize armazenando apenas dígitos. Nunca force formato de data/endereço de outro país em formulários brasileiros.
## Conexoes

- [[cluster-hub-traducao]]
- [[datas-horas-e-fuso-horário-no-brasil-ddmmaaaa-24h-brt]]
- [[localização-de-software-placeholders-plurais-gênero-e-espaço]]
- [[localização-l10n-vs-internacionalização-i18n-vs-transcreatio]]
- [[números-moedas-r-e-percentuais-no-pt-br]]
- [[padrao-hub-padroes]]