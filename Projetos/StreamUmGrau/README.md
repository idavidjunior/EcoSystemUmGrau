# StreamUmGrau

MVP de aplicativo de streaming de mídia e catálogo de vídeos (filmes, séries e
doramas) em Flutter, com catálogo conectado ao **Supabase**.

## Estrutura

```
lib/
├── main.dart                    # inicialização do app
├── core/
│   ├── config/app_config.dart   # URL e chave anon do Supabase
│   ├── services/supabase_service.dart  # conexão + consultas
│   └── theme/app_theme.dart     # tema escuro padrão
├── models/
│   └── midia_model.dart         # mapeamento da tabela `midias`
├── views/
│   └── home_view.dart           # tela inicial (catálogo em grade)
└── widgets/
    └── midia_card.dart          # card vertical da mídia
```

## Configuração

1. Instale o Flutter (https://flutter.dev) e rode `flutter doctor`.
2. Crie um projeto no Supabase e execute o script
   `database/schema_midias.sql` no SQL Editor (cria a tabela `midias` + seed).
3. Execute o app informando as credenciais:

```bash
flutter pub get
flutter run \
  --dart-define=SUPABASE_URL=https://SEU_PROJETO.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=SUA_CHAVE_ANON
```

> A chave anon é pública por design (protegida por RLS). Nunca exponha a
> `service_role` no app.

## Tabela `midias`

| Coluna                | Tipo    | Descrição                         |
|-----------------------|---------|-----------------------------------|
| `id`                  | UUID PK | Identificador                     |
| `titulo`              | text    | Título da obra                    |
| `tipo`                | text    | `filme`, `serie`, `dorama`        |
| `categoria`           | text    | Gênero/categoria                  |
| `sinopse`             | text    | Resumo                            |
| `capa_url`            | text    | URL da capa (poster)              |
| `banner_url`          | text    | URL do banner                     |
| `ano`                 | integer | Ano de lançamento                 |
| `idioma_tipo`         | text    | `DUB`, `LEG`, `DUAL`              |
| `classificacao_etaria`| integer | Idade mínima (0 = livre)          |
