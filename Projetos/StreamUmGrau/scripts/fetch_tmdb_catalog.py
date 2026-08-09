#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_tmdb_catalog.py — Gera o seed SQL do catalogo StreamUmGrau a partir da TMDB API.

Uso:
    python fetch_tmdb_catalog.py --api-key SUA_CHAVE --saida database/seed_tmdb.sql
    python fetch_tmdb_catalog.py --api-key SUA_CHAVE --tipos filme,serie,dorama --por-tipo 20

Fonte: https://www.themoviedb.org (API gratuita; crie a chave em Settings -> API).

O script busca obras populares por tipo, mapeia para a tabela `midias` do
Supabase e gera um INSERT ... ON CONFLICT (id) DO NOTHING. Tambem imprime um
resumo do que foi gerado.
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE_POSTER = "https://image.tmdb.org/t/p/w500"
IMG_BASE_BACKDROP = "https://image.tmdb.org/t/p/w1280"

IDIOMA_PADRAO = {
    "filme": "DUB",
    "serie": "LEG",
    "dorama": "LEG",
}

# Tipos aceitos -> rota/parametros da API
TIPOS = {
    "filme": {"route": "movie/popular", "field": "title"},
    "serie": {"route": "tv/popular", "field": "name"},
    # Doramas = series com idioma original coreano (ko), via discover.
    "dorama": {
        "route": "discover/tv",
        "field": "name",
        "extra": "with_original_language=ko",
    },
}


def http_json(url, api_key):
    """Faz GET na API TMDB e retorna o JSON decodificado."""
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(
        f"{url}{sep}api_key={api_key}",
        headers={"Accept": "application/json", "User-Agent": "StreamUmGrau/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def classificacao_por_categoria(categoria):
    """Heuristica simples de classificacao etaria por genero."""
    mapa = {
        "animação": 0,
        "animacao": 0,
        "family": 0,
        "aventura": 10,
        "ação": 12,
        "acao": 12,
        "ficção científica": 12,
        "ficcao cientifica": 12,
        "terror": 16,
        "crime": 16,
        "guerra": 16,
    }
    chave = categoria.lower().strip()
    return mapa.get(chave, 12)


def extrair_obra(item, tipo, api_key):
    """Converte um item da TMDB no dict no formato da tabela `midias`."""
    campo_titulo = "title" if tipo == "filme" else "name"
    titulo = item.get(campo_titulo) or ""
    if not titulo:
        return None

    categoria = (item.get("genre_ids") or [])
    cat_nome = "outros"
    if categoria:
        try:
            # Pega o nome do genero via /genre/movie/list (cacheado por chamada)
            gen_list = http_json(f"{TMDB_BASE}/genre/{( 'movie' if tipo == 'filme' else 'tv')}/list", api_key)
            gen_map = {g["id"]: g["name"] for g in gen_list.get("genres", [])}
            cat_nome = gen_map.get(categoria[0], "outros")
        except Exception:
            cat_nome = "outros"

    poster = item.get("poster_path")
    backdrop = item.get("backdrop_path")
    capa_url = f"{IMG_BASE_POSTER}{poster}" if poster else ""
    banner_url = f"{IMG_BASE_BACKDROP}{backdrop}" if backdrop else capa_url

    sinopse = (item.get("overview") or "").strip()[:400]
    sinopse = " ".join(sinopse.split())
    ano = 0
    if tipo == "filme":
        try:
            ano = int((item.get("release_date") or "")[:4])
        except ValueError:
            ano = 0
    else:
        try:
            ano = int((item.get("first_air_date") or "")[:4])
        except ValueError:
            ano = 0

    idioma = IDIOMA_PADRAO.get(tipo, "LEG")
    idade = classificacao_por_categoria(cat_nome)
    popularidade = int(round(item.get("popularity") or 0)) or 0

    return {
        "titulo": titulo,
        "tipo": tipo,
        "categoria": cat_nome,
        "sinopse": sinopse,
        "capa_url": capa_url,
        "banner_url": banner_url,
        "ano": ano,
        "idioma_tipo": idioma,
        "classificacao_etaria": idade,
        "popularidade": min(popularidade, 100),
    }


def escapar(valor):
    """Escapa string para SQL single-quoted."""
    return str(valor).replace("'", "''")


def gerar_sql(obras):
    """Gera o bloco INSERT ... ON CONFLICT para as obras."""
    if not obras:
        return ""
    linhas = []
    for o in obras:
        linhas.append(
            "  ("
            f"'{escapar(o['titulo'])}', '{o['tipo']}', '{escapar(o['categoria'])}', "
            f"'{escapar(o['sinopse'])}', '{escapar(o['capa_url'])}', "
            f"'{escapar(o['banner_url'])}', {o['ano']}, "
            f"'{o['idioma_tipo']}', {o['classificacao_etaria']}, {o['popularidade']}"
            ")"
        )
    return (
        "-- Seed gerado por fetch_tmdb_catalog.py em "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        "insert into public.midias (titulo, tipo, categoria, sinopse, capa_url, banner_url, ano, idioma_tipo, classificacao_etaria, popularidade)\n"
        "values\n"
        + ",\n".join(linhas)
        + "\non conflict (id) do nothing;"
    )


def main():
    parser = argparse.ArgumentParser(description="Gera seed SQL do catalogo via TMDB.")
    parser.add_argument("--api-key", required=True, help="Chave de API v3 do TMDB")
    parser.add_argument("--tipos", default="filme,serie,dorama", help="Tipos separados por virgula")
    parser.add_argument("--por-tipo", type=int, default=15, help="Obras por tipo")
    parser.add_argument("--saida", default="database/seed_tmdb.sql", help="Arquivo SQL de saida")
    args = parser.parse_args()

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    obras = []
    falhas = []

    for tipo in tipos:
        if tipo not in TIPOS:
            print(f"[skip] tipo desconhecido: {tipo}")
            continue
        rota = TIPOS[tipo]["route"]
        extra = TIPOS[tipo].get("extra", "")
        pagina = 1
        coletadas = 0
        tentativas = 0
        print(f"[{tipo}] buscando em {rota}...")
        while coletadas < args.por_tipo and tentativas < 5:
            url = f"{TMDB_BASE}/{rota}?page={pagina}"
            if extra:
                url += f"&{extra}"
            try:
                dados = http_json(url, args.api_key)
            except Exception as e:
                print(f"  [erro] pagina {pagina}: {e}")
                tentativas += 1
                time.sleep(2)
                continue
            resultados = dados.get("results", [])
            if not resultados:
                break
            for item in resultados:
                obra = extrair_obra(item, tipo, args.api_key)
                if obra:
                    obras.append(obra)
                    coletadas += 1
                    if coletadas >= args.por_tipo:
                        break
            pagina += 1
            time.sleep(0.25)  # politesse: limite ~40 req/10s
            if pagina > 3:
                break
        print(f"  {coletadas} obras coletadas")

    if not obras:
        print("Nenhuma obra gerada. Verifique a chave de API.")
        sys.exit(1)

    sql = gerar_sql(obras)
    with open(args.saida, "w", encoding="utf-8") as f:
        f.write(sql + "\n")
    print(f"\nGerado: {args.saida} ({len(obras)} obras)")

    # Resumo por tipo
    for tipo in tipos:
        n = sum(1 for o in obras if o["tipo"] == tipo)
        print(f"  {tipo}: {n} obras")
    print("Copie o arquivo e rode no SQL Editor do Supabase (apos o schema_midias.sql).")


if __name__ == "__main__":
    main()
