-- ============================================================
-- StreamUmGrau — Tabela de catalogo de midias
-- Execute no SQL Editor do Supabase para criar a tabela e a RLS.
-- ============================================================

create extension if not exists "pgcrypto";

create table if not exists public.midias (
  id                   uuid primary key default gen_random_uuid(),
  titulo               text not null,
  tipo                 text not null default 'filme',       -- filme | serie | dorama
  categoria            text not null default 'outros',
  sinopse              text not null default '',
  capa_url             text not null default '',
  banner_url           text not null default '',
  ano                  integer not null default 0,
  idioma_tipo          text not null default 'DUB',         -- DUB | LEG | DUAL
  classificacao_etaria integer not null default 0,
  criado_em            timestamptz not null default now(),
  atualizado_em        timestamptz not null default now()
);

create index if not exists idx_midias_tipo  on public.midias (tipo);
create index if not exists idx_midias_ano   on public.midias (ano);

-- Acesso leitura anonimo (catalogo publico) + escrita autenticada.
alter table public.midias enable row level security;

create policy "midias_leitura_publica"
  on public.midias
  for select
  using (true);

create policy "midias_escrita_autenticada"
  on public.midias
  for all
  using (auth.uid() is not null)
  with check (auth.uid() is not null);

-- ============================================================
-- Seed de exemplo para visualizar o catalogo (opcional).
-- ============================================================
insert into public.midias (titulo, tipo, categoria, sinopse, capa_url, banner_url, ano, idioma_tipo, classificacao_etaria)
values
  ('Interestelar', 'filme', 'Ficção Científica', 'A exploração de buracos de minhoca em busca de um novo lar para a humanidade.', 'https://image.tmdb.org/t/p/w500/nCbkOyOMTEgEVqbz0U1ekYqkpLy.jpg', 'https://image.tmdb.org/t/p/w1280/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg', 2014, 'DUB', 10),
  ('Breaking Bad', 'serie', 'Drama', 'Um professor de química vira produtor de metanfetamina.', 'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg', 'https://image.tmdb.org/t/p/w1280/5FiO4cTUyQHDw2jJQ4qAVMfNGJX.jpg', 2008, 'LEG', 16),
  ('Vagabond', 'dorama', 'Ação', 'Um homem investiga a queda de um avião que envolve seu sobrinho.', 'https://image.tmdb.org/t/p/w500/d7tDnYNN6cXb0Hpq0SJAIzkVX4u.jpg', 'https://image.tmdb.org/t/p/w1280/6qh4xH8eEIDnEQQnZxWjO3CVJQx.jpg', 2019, 'DUAL', 16),
  ('O Rei Leão', 'filme', 'Animação', 'Um leãozinho herdeiro do trono foge de casa.', 'https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpRsd6Q.jpg', 'https://image.tmdb.org/t/p/w1280/wFwspdCbKVwPjAtMsHUO8qVm3qW.jpg', 1994, 'DUB', 0)
on conflict (id) do nothing;
