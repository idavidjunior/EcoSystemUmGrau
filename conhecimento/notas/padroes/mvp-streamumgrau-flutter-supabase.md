---
tags: [escuro, lib, maquina, nao, opencode, padrao]
aliases: [mvp streamumgrau flutter supabase]
date: 2026-08-08
---

# mvp streamumgrau flutter supabase

**Fonte:** opencode

Tipo: padrao

Tags: [flutter, supabase, mvp, streaming, catalogo]

Data: 2026-08-08

Contexto: Criacao da primeira parte do MVP de streaming/catalogo de midias (StreamUmGrau) dentro do ecossistema.

Decisão: Gerar manualmente a estrutura Dart do projeto Flutter (lib/core, models, views, widgets) porque o Flutter nao esta instalado na maquina. Padrao de pastas: core/ (config, services, theme), models/, views/, widgets/.

Impacto: Projeto StreamUmGrau em Projetos/StreamUmGrau com midia_model.dart mapeando tabela midias do Supabase e HomeView com GridView 2 colunas em tema escuro. Quando Flutter for instalado, basta rodar flutter create . para gerar o scaffold de plataformas.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]