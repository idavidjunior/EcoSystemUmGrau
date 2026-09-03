---
tags: [adb, decisao, instalar, necessario, opencode, seguida]
aliases: [projeto completo e ativo a recuperar]
date: 2026-09-03
---

# projeto completo e ativo a recuperar

**Fonte:** opencode

---
tipo: decisao
tags: [ecossistema, projeto, recuperacao, codigo-fonte, versionamento, git, compilar, smc, ativo]
data: 2026-09-03
contexto: Usuario consolidou que o SupermarketCalculator esta completo e funcional, com todo o codigo-fonte versionado do inicio ao fim. O ecossistema nao deve redescobrir nem reconstruir nada: deve apenas guardar, lembrar e, quando pedido, recuperar o codigo pronto e compilar.
decisao: Projeto entregue e versionado passa a ser tratado como ATIVO A RECUPERAR, nao como trabalho a redescobrir. SMC (SupermarketCalculator) esta na versao 1.5.9, commit do submodulo 485dd9f, repo eco e7a5b7aee, sincronizado em PC local, GitHub (branch opencode/mighty-meadow) e HD externo (E:\Default Project\EcoSystemUmGrau). O codigo completo existe e esta guardado; nao ha nada a redescobrir. Se o usuario pedir para recriar/reconstruir, o ecossistema deve dizer que ja tem tudo, lembrar onde esta e apenas recuperar do git e compilar (build.ps1 / skill android-pure-sdk).
impacto: Ao solicitar recriacao ou reconstrucao de um projeto completo consolidado, o ecossistema NAO propoe recomecar do zero. Ele confirma que ja possui o codigo, indica a localizacao exata (repo/submodulo/commit), e executa a recuperacao (restaurar do git, se necessario) seguida do build (compilar e instalar via ADB). O conhecimento ja consolidado nao precisa ser redescoberto.
```

## Conexoes
- [[smc-acrescimo-resultado-grande]]
- [[smc-ab5-calculadora-simples]]
- [[2026-08-09-projetos-irmaos-registro]]
- [[2026-08-08-backup-apks-e-fontes-no-github]]
- [[2026-08-08-persistencia-carrinho-supermarketcalculator]]

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]