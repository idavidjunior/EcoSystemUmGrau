#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o mock_midia_repository.dart a partir do seed_tmdb.sql (espelho do catalogo real).

Usa UUID v5 determinístico (namespace + titulo + tipo) para que os IDs sejam
estáveis entre regenerações — favoritos locais não são invalidados.
"""
import hashlib
import re
import uuid

SEED = "database/seed_tmdb.sql"
SAIDA = "lib/core/services/mock_midia_repository.dart"
NAMESPACE = uuid.UUID("9e6a1c9e-8b10-4a10-8f10-123456789abc")


def parse_linha(linha):
    """Extrai os 10 campos de uma linha `  ('a', 'b', ...),`."""
    m = re.match(r"^  \(", linha)
    if not m:
        return None
    corpo = linha.strip()
    corpo = corpo[1:]  # remove '(' inicial
    corpo = corpo.rstrip(",")  # remove ',' final (se houver)
    corpo = corpo.rstrip(")")  # remove ')' final (se houver)
    campos = []
    atual = ""
    em_string = False
    i = 0
    while i < len(corpo):
        c = corpo[i]
        if c == "'" and not em_string:
            em_string = True
            atual += "'"
        elif c == "'" and em_string:
            if i + 1 < len(corpo) and corpo[i + 1] == "'":
                atual += "''"  # aspas escapada mantida p/ camada seguinte
                i += 1
            else:
                em_string = False
                atual += "'"
        elif c == "," and not em_string:
            campos.append(atual.strip())
            atual = ""
        else:
            atual += c
        i += 1
    if atual.strip():
        campos.append(atual.strip())
    if len(campos) != 10:
        return None
    return campos


def limpar_aspas(valor):
    """Converte aspas SQL ('') em aspas simples (')."""
    return valor.replace("''", "'")


def para_dart_string(valor):
    """Escapa string para um literal Dart com aspas simples."""
    v = limpar_aspas(valor).strip("'")
    v = v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return v


def main():
    obras = []
    with open(SEED, encoding="utf-8") as f:
        for linha in f:
            campos = parse_linha(linha)
            if campos is None:
                continue
            titulo, tipo, categoria, sinopse, capa, banner, ano, idioma, idade, pop = campos
            obras.append(
                {
                    "titulo": limpar_aspas(titulo).strip("'"),
                    "tipo": limpar_aspas(tipo).strip("'"),
                    "categoria": limpar_aspas(categoria).strip("'"),
                    "sinopse": limpar_aspas(sinopse).strip("'"),
                    "capa": limpar_aspas(capa).strip("'"),
                    "banner": limpar_aspas(banner).strip("'"),
                    "ano": int(ano),
                    "idioma": limpar_aspas(idioma).strip("'"),
                    "idade": int(idade),
                    "pop": int(pop),
                }
            )

    if not obras:
        raise SystemExit("Nenhuma obra extraída do seed.")

    linhas = []
    linhas.append("import '../../models/midia_model.dart';")
    linhas.append("import 'midia_repository.dart';")
    linhas.append("")
    linhas.append(
        "/// Repositorio local espelhado do catalogo real (gerado a partir de"
    )
    linhas.append(
        "/// database/seed_tmdb.sql via scripts/_espelhar_mock.py). Permite"
    )
    linhas.append(
        "/// desenvolver, testar e operar em fallback sem depender do Supabase."
    )
    linhas.append(
        "/// IDs sao UUID v5 deterministicos (estaveis entre regeneracoes)."
    )
    linhas.append("class MockMidiaRepository implements MidiaRepository {")
    linhas.append("  const MockMidiaRepository();")
    linhas.append("")
    linhas.append("  static const List<Map<String, dynamic>> _seed = [")
    for o in obras:
        mid = uuid.uuid5(NAMESPACE, f"{o['titulo']}|{o['tipo']}")
        linhas.append("    {")
        linhas.append(f"      'id': '{mid}',")
        linhas.append(f"      'titulo': '{para_dart_string(o['titulo'])}',")
        linhas.append(f"      'tipo': '{para_dart_string(o['tipo'])}',")
        linhas.append(f"      'categoria': '{para_dart_string(o['categoria'])}',")
        linhas.append(f"      'sinopse': '{para_dart_string(o['sinopse'])}',")
        linhas.append(f"      'capa_url': '{para_dart_string(o['capa'])}',")
        linhas.append(f"      'banner_url': '{para_dart_string(o['banner'])}',")
        linhas.append(f"      'ano': {o['ano']},")
        linhas.append(f"      'idioma_tipo': '{para_dart_string(o['idioma'])}',")
        linhas.append(f"      'classificacao_etaria': {o['idade']},")
        linhas.append(f"      'popularidade': {o['pop']},")
        linhas.append("    },")
    linhas.append("  ];")
    linhas.append("")
    linhas.append("  @override")
    linhas.append("  Future<List<Midia>> fetchMidias() async {")
    linhas.append("    await Future<void>.delayed(const Duration(milliseconds: 200));")
    linhas.append("    return _seed.map(Midia.fromJson).toList();")
    linhas.append("  }")
    linhas.append("")
    linhas.append("  @override")
    linhas.append("  Future<List<Midia>> fetchMidiasPorTipo(String tipo) async {")
    linhas.append("    await Future<void>.delayed(const Duration(milliseconds: 200));")
    linhas.append("    return _seed")
    linhas.append("        .where((m) => m['tipo'] == tipo)")
    linhas.append("        .map(Midia.fromJson)")
    linhas.append("        .toList();")
    linhas.append("  }")
    linhas.append("}")
    linhas.append("")

    with open(SAIDA, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(linhas))

    tipos = {}
    for o in obras:
        tipos[o["tipo"]] = tipos.get(o["tipo"], 0) + 1
    print(f"Gerado: {SAIDA} ({len(obras)} obras)")
    for t, n in sorted(tipos.items()):
        print(f"  {t}: {n}")


if __name__ == "__main__":
    main()
