---
tipo: padrao
tags: [flutter, supabase, mvp, streaming, catalogo]
data: 2026-08-08
contexto: Criacao da primeira parte do MVP de streaming/catalogo de midias (StreamUmGrau) dentro do ecossistema.
decisao: Gerar manualmente a estrutura Dart do projeto Flutter (lib/core, models, views, widgets) porque o Flutter nao esta instalado na maquina. Padrao de pastas: core/ (config, services, theme), models/, views/, widgets/.
impacto: Projeto StreamUmGrau em Projetos/StreamUmGrau com midia_model.dart mapeando tabela midias do Supabase e HomeView com GridView 2 colunas em tema escuro. Quando Flutter for instalado, basta rodar flutter create . para gerar o scaffold de plataformas.
pendente: Rodar flutter create . + flutter pub get + flutter analyze quando o SDK Flutter estiver disponivel.
