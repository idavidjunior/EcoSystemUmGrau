---
tags: [decisao, dentro, family, multiline, opencode, strings]
aliases: [Fase A concluída: catálogo real no Supabase (64 obras via TM]
date: 2026-08-08
---

# Fase A concluída: catálogo real no Supabase (64 obras via TMDB)

**Fonte:** opencode

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

- Chave 
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]