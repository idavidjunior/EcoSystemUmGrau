---
tipo: decisao
tags: [ecossistema, projeto, recuperacao, codigo-fonte, versionamento, git, compilar, ativo, todos-os-projetos, regra-geral]
data: 2026-09-03
contexto: Usuario consolidou que o SupermarketCalculator esta completo e funcional com todo o codigo-fonte versionado, e em seguida determinou que esta regra vale para TODOS os projetos desenvolvidos e a desenvolver, valendo imediatamente. O ecossistema nao deve redescobrir nem reconstruir nada: deve apenas guardar, lembrar e, quando pedido, recuperar o codigo pronto e compilar.
decisao: REGRA GERAL E IMEDIATA PARA TODOS OS PROJETOS. Todo projeto entregue e versionado passa a ser tratado como ATIVO A RECUPERAR, nunca como trabalho a redescobrir ou reconstruir do zero. Vale para todos os projetos existentes (ex.: SupermarketCalculator v1.5.9, BibliiaEstudoCompleta, Mp3Player, VoxUmGrau, StreamUmGrau, CellCleaner, aegis, Rob-Trader, roboumgrau, TradingAgents, WindowsMaintenanceSuite_v3, etc., conforme conhecimento/projetos-irmaos.json) e para qualquer projeto futuro. O codigo completo existe e esta guardado no git (PC local + GitHub + HD externo); nao ha nada a redescobrir. Se o usuario pedir para recriar/reconstruir/refazer um projeto, o ecossistema deve dizer que ja tem tudo, lembrar onde esta, indicar a localizacao exata (repo/submodulo/commit) e apenas recuperar do git (se necessario) e compilar com o build script/skill proprio de cada projeto.
impacto: Ao solicitar recriacao ou reconstrucao de QUALQUER projeto completo consolidado, o ecossistema NAO propoe recomecar do zero. Ele confirma que ja possui o codigo, indica a localizacao exata e executa a recuperacao (restaurar do git, se necessario) seguida do build (compilar e instalar via ADB/ferramenta propria). O conhecimento ja consolidado nao precisa ser redescoberto. O catalogo conhecimento/projetos-irmaos.json e a fonte canonica da localizacao/status/versao de cada projeto irmao.
```

## Conexoes

- [[2026-07-27-unificacao-completa-do-ecossistema]]
- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]