---
tags: [brst, localizacao, obsoleto, padrao, tarde, usar]
aliases: [Datas, horas e fuso horário no Brasil (dd/mm/aaaa, 24h, BRT)]
date: 2026-08-21
---

# Datas, horas e fuso horário no Brasil (dd/mm/aaaa, 24h, BRT)

**Fonte:** localizacao

O padrão brasileiro de data é dia/mês/ano: 10/08/2026 — jamais 08/10/2026 (seria outubro). Em texto corrido: "10 de agosto de 2026". ISO 8601 (2026-08-10) é aceitável em sistemas, não em interface de usuário.

Hora: formato de 24 horas em contextos formais e digitais ("18h30"), embora o coloquial use "6h30 da tarde". Fuso padrão: horário de Brasília, BRT (UTC-3); o horário de verão foi extinto em 2019, não assuma DST. Amazonas (UTC-4) e Acre (UTC-5) têm fusos próprios; Fernando de Noronha usa UTC-2.

Armadilhas: gravar hora local sem fuso (prefira UTC + timezone), confundir BRST (obsoleto) com BRT e usar am/pm. Use Intl.DateTimeFormat('pt-BR') e armazene instantes em UTC, exibindo no fuso do usuário.
## Conexoes

- [[cluster-hub-traducao]]
- [[localização-de-software-placeholders-plurais-gênero-e-espaço]]
- [[localização-l10n-vs-internacionalização-i18n-vs-transcreatio]]
- [[números-moedas-r-e-percentuais-no-pt-br]]
- [[padrao-hub-padroes]]
- [[unidades-de-medida-e-convenções-brasileiras-m-kg-c-telefone-]]