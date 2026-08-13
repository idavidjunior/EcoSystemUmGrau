---
tags: [decisao, dentro, multiline, opencode, sessão, strings]
aliases: [Fase A concluída: catálogo real no Supabase (64 obras via TM]
date: 2026-08-13
---

# Fase A concluída: catálogo real no Supabase (64 obras via TMDB)

**Fonte:** opencode

---
tipo: decisao
tags: [supabase, tmdb, catalogo, streamumgrau, fase-a, seed]
data: 2026-08-08
contexto: Fase A do StreamUmGrau - conectar catalogo real ao Supabase via TMDB
decisao: Catalogo real no ar com 64 obras (22 filmes, 21 series, 21 doramas) via TMDB -> Supabase -> app
impacto: App mostra dados reais; repositorio tem schema + script regeneravel + seed versionado
---

# Fase A concluída: catálogo real no Supabase (64 obras via TMDB)

## O que foi feito

1. **Supabase configurado**: projeto `asanytdwhbsiujuppeth` (região sa-east-1), tabela `midias`
   criada via conexão Postgres direta (pooler `aws-0-sa-east-1.pooler.supabase.com:6543`,
   usuário `postgres.<ref>`, senha = senha completa do projeto, incluindo prefixo `Family/...`).
2. **RLS ativa**: leitura pública (anon), escrita só autenticada. App usa a **publishable key**
   (`sb_publishable_...`), nunca a secret (`sb_secret_...`).
3. **Script `scripts/fetch_tmdb_catalog.py`**: gera seed SQL a partir da TMDB API v3.
   Lições do script:
   - Doramas NÃO vêm de `tv/popular` (duplica séries americanas). Corrigido com
     `discover/tv?with_original_language=ko`.
   - Sinopses da TMDB podem conter quebras de linha/multiline dentro de strings SQL
     (quebram o INSERT). Corrigido com `" ".join(sinopse.split())`.
4. **Seed executado**: 60 obras + 4 do schema = 64 no banco. Verificado por REST com a
   publishable key (HTTP 200, 64 registros).

## Segurança

- Chave secret (`sb_secret_...`) foi exposta no chat pelo usuário — orientado a rotacionar
  (Settings -> API -> Recreate secret).
- Credenciais vão via `--dart-define` no build; NUNCA versionadas no código.
- A senha do banco tem prefixo `Family/` — armazenada apenas localmente/na sessão.

## Fluxo de build com credenciais

```
flutter build apk --debug \
  --dart-define=SUPABASE_URL=https://<ref>.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=sb_publishable_...
```

## Validação no dispositivo

- Instalado no Redmi (wireless 100.64.71.9:5555), app rodando (PID 28058), sem FATAL,
  sem erros de rede no logcat.

## Regra de processo do usuário (novo padrão)

**Sempre** antes de commit/push: compilar -> instalar -> testar -> validar. Só depois subir.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]