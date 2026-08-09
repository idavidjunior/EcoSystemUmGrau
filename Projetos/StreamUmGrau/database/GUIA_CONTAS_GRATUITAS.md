# StreamUmGrau — Guia das contas gratuitas (Fase A)

Para ligar o catálogo real você precisa criar **2 contas gratuitas** (sem cartão).
Leva ~5 minutos. Siga a ordem: **Supabase** primeiro, depois **TMDB**.

---

## 1. Supabase (banco + backend) — ~3 min

1. Acesse https://supabase.com e clique em **Start your project** / **Sign up**.
2. Crie a conta com e-mail + senha (ou Google/GitHub).
3. Após entrar, clique em **New project**:
   - **Name**: `stream-um-grau`
   - **Database Password**: crie uma senha (guarde — pode ser precisa depois)
   - **Region**: escolha a mais próxima (ex.: `South America (São Paulo)` ou `us-east-1`)
   - **Plan**: Free (padrão)
4. Aguarde ~1-2 min até o projeto ficar pronto (indicador verde).
5. No painel esquerdo, clique em **SQL Editor** → **New query**.
6. Cole o conteúdo de `database/schema_midias.sql` e clique em **Run**.
   → Deve criar a tabela `midias`, os índices, a RLS e o seed de 4 obras.
7. No painel esquerdo, **Settings** (engrenagem) → **API**:
   - Copie o **Project URL** (ex.: `https://xxxx.supabase.co`) → é a `SUPABASE_URL`
   - Copie o **anon public key** (começa com `eyJ...`) → é a `SUPABASE_ANON_KEY`

> A chave `anon` é pública por design (segura, pois o RLS protege a tabela).
> **Nunca** use a `service_role` no app.

---

## 2. TMDB (fonte do catálogo) — ~2 min

1. Acesse https://www.themoviedb.org/signup e crie uma conta gratuita.
2. Confirme o e-mail.
3. Acesse https://www.themoviedb.org/settings/api → **Create** / **Request an API key**:
   - Tipo: **Developer**
   - Application type: **Desktop** (ou Education — tanto faz)
   - Nome: `StreamUmGrau`
4. Copie a **API Key (v3 auth)** → é a `TMDB_API_KEY`.
   A chave é gratuita e não exige cartão.

---

## 3. Como me entregar

Basta me informar, em qualquer conversa:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
TMDB_API_KEY=chave_v3_aqui
```

Com isso eu executo o resto automaticamente:

1. `python scripts/fetch_tmdb_catalog.py --api-key <TMDB_API_KEY> --por-tipo 20`
2. Gero o `seed_tmdb.sql` com ~45-60 obras reais
3. Você roda o SQL no SQL Editor (ou eu gero um comando `curl` para o Supabase)
4. Build local com `--dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=...`
5. Instalo no Redmi e validamos o catálogo real

> Se preferir não compartilhar a chave TMDB: me avise — eu gero o seed via TMDB
> com a chave na própria máquina, sem ela ficar no histórico da conversa.
> Ou seguimos com a **lista curada** (sem TMDB) que eu já montei no mock.
