#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""skill_recorrente.py -- Automatiza a criacao/atualizacao de skills por recorrencia.

Principio (igual a deduplicacao de memoria):
  Se um pedido se repete 3+ vezes, o ecossistema nao deve resolver do zero toda vez.
  Antes de criar uma skill nova, busca skill similar ja existente no acervo.
    - Se existir similar (>= limiar): ATUALIZA (adiciona exemplo/uso) em vez de duplicar.
    - Se nao existir: CRIA nova skill no dominio mais adequado e registra no inventario.

Objetivos:
  - Registrar recorrencia de um pedido/atividade (contador persistente em runtime).
  - Ao atingir o limiar (padrao 3), processar: buscar similar -> atualizar ou criar.
  - Respeitar utilidade: so cria/atualiza quando ha repeticoes reais, nao inventa.

Uso:
    python scripts/skill_recorrente.py register "<pedido>" [--dominio X] [--limiar 3]
    python scripts/skill_recorrente.py process "<pedido>" [--dominio X] [--forca]
    python scripts/skill_recorrente.py status
    python scripts/skill_recorrente.py reset "<pedido>"

Seguranca:
  - Desligavel via env SKILL_RECURRENT=0.
  - Escrita atomica (tmp + os.replace) em todos os arquivos.
  - Nunca lança em falha de indice/busca: degrada para criar novo de forma segura.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
RECORRENCIA_FILE = RUNTIME / "skill_recorrencias.json"
ACERVO_HABILIDADES = ROOT / "mcp"
INVENTARIO = ROOT / "config" / "inventario_estruturas.json"

ENABLED = os.environ.get("SKILL_RECURRENT", "1") == "1"
LIMIAR_SIMILARIDADE = float(os.environ.get("SKILL_SIMILAR_MIN", "0.70"))


def _atomic_write_json(path: Path, data):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _ler_recorrencias() -> dict:
    if RECORRENCIA_FILE.exists():
        try:
            return json.loads(RECORRENCIA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _slug(texto: str) -> str:
    norm = _normalizar(texto)
    norm = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    return norm or ("skill-" + hashlib.md5(texto.encode("utf-8")).hexdigest()[:8])


def _chave_pedido(pedido: str) -> str:
    return _normalizar(pedido)


def _scan_acervo() -> list:
    """Varre todas as skills existentes (skill.md) no acervo mcp.
    Retorna lista de dicts: {id, dominio, path, titulo, description}."""
    itens = []
    if not ACERVO_HABILIDADES.exists():
        return itens
    for dominio_dir in sorted(ACERVO_HABILIDADES.iterdir()):
        if not dominio_dir.is_dir():
            continue
        dominio = dominio_dir.name
        hab_dir = dominio_dir / "habilidades"
        if not hab_dir.is_dir():
            continue
        for skill_dir in sorted(hab_dir.iterdir()):
            md = skill_dir / "skill.md"
            if md.exists():
                texto = md.read_text(encoding="utf-8", errors="replace")
                itens.append({
                    "id": skill_dir.name,
                    "dominio": dominio,
                    "path": str(md.relative_to(ROOT)),
                    "titulo": skill_dir.name.replace("-", " "),
                    "texto": texto,
                })
    return itens


def _similaridade(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalizar(a), _normalizar(b)).ratio()


_STOPWORDS = {"o", "a", "os", "as", "um", "uma", "de", "da", "do", "das", "dos",
              "e", "em", "no", "na", "nos", "nas", "para", "que", "com", "por",
              "ao", "aos", "se", "como", "sobre", "antes", "depois"}


def _trigger_keywords(texto: str) -> list:
    """Extrai os trigger keywords do frontmatter description de um skill.md,
    caso existam (padrao 'Trigger keywords: ...'). Filtra keywords curtas e
    stopwords para evitar falsos positivos."""
    try:
        m = re.search(r"Trigger keywords:\s*([^.\n]+)", texto, re.IGNORECASE)
        if not m:
            return []
        raw = m.group(1).strip().strip("'\"")
        keywords = []
        for k in re.split(r"[,;]", raw):
            k = k.strip().strip("'\"").strip().lower()
            if len(k) >= 3 and k not in _STOPWORDS:
                keywords.append(k)
        return keywords
    except Exception:
        return []


def _buscar_similar(pedido: str, acervo: list) -> dict | None:
    """Busca skill existente cujo titulo/triggers seja suficientemente similar ao pedido.
    Combina similaridade lexical (difflib), sobreposicao de tokens sem stopwords e
    compatibilidade de trigger keywords por substring. Retorna o item ou None."""
    p_norm = _normalizar(pedido)
    tokens_pedido = {t for t in p_norm.split() if t not in _STOPWORDS}
    melhor = None
    melhor_score = 0.0
    for item in acervo:
        score_titulo = _similaridade(pedido, item["titulo"])
        score_texto = _similaridade(pedido, item["texto"][:400])
        score = max(score_titulo, score_texto)
        # Bonus por sobreposicao de tokens (sem stopwords).
        tokens_conteudo = {t for t in _normalizar(item["texto"][:800]).split() if t not in _STOPWORDS}
        tokens_comuns = tokens_pedido & tokens_conteudo
        if tokens_pedido and tokens_comuns:
            score = min(score + min(len(tokens_comuns) / max(len(tokens_pedido), 1), 0.35), 1.0)
        # Trigger keywords: marca similar se (A) 2+ palavras-trigger significativas
        # coincidem no pedido, OU (B) 1 palavra-trigger coincide E ela identifica a
        # propria skill (aparece no titulo/id). Isso reconhece equivalencia conceitual
        # e identidade direta sem cair em falsos positivos de termos genericos.
        palavras_trigger = set()
        for kw in _trigger_keywords(item["texto"]):
            for pal in kw.split():
                if len(pal) >= 4 and pal not in _STOPWORDS:
                    palavras_trigger.add(pal)
        coincidencias = 0
        pal_trig_forte = None
        for pal in palavras_trigger:
            if re.search(r"\b" + re.escape(pal) + r"\b", p_norm):
                coincidencias += 1
                if pal in item["titulo"]:
                    pal_trig_forte = pal
        if coincidencias >= 2 or (coincidencias >= 1 and pal_trig_forte):
            score = max(score, 0.75)
        if score >= LIMIAR_SIMILARIDADE and score > melhor_score:
            melhor_score = score
            melhor = item
    return melhor


def _dominio_sugerido(pedido: str) -> str:
    """Sugere o dominio MCP mais provavel pelo conteudo do pedido."""
    p = _normalizar(pedido)
    mapa = {
        "desenvolvimento": ["código", "code", "api", "função", "classe", "script", "refator", "bug", "teste", "deploy", "backend", "frontend", "database", "android", "flutter", "react", "python", "server", "docker"],
        "nucleo": ["pedido", "objetivo", "plano", "compreender", "contexto", "memória", "memoria", "aprendizado", "governança", "governanca", "regra", "cláusula", "clausula", "jurisprudência", "jurisprudencia"],
        "internet": ["web", "site", "url", "busca", "buscar", "pesquisa", "scrap", "navegar", "clima", "google", "drive"],
        "multimidia": ["áudio", "audio", "vídeo", "video", "imagem", "mp3", "tts", "voz", "transcrever", "stream"],
        "android": ["celular", "adb", "app", "apk", "tela", "xingomi", "escrcpy", "device"],
        "os": ["windows", "arquivo", "pasta", "processo", "disco", "rede", "comando"],
        "comportamentais": ["revisão", "revisao", "conservador", "crítico", "critico", "pensador", "revisor"],
        "memoria": ["rememória", "memoria", "significado", "conceito", "o que sabemos", "última vez", "ultima vez"],
    }
    for dominio, chaves in mapa.items():
        for chave in chaves:
            if chave in p:
                return dominio
    return "nucleo"


def _criar_atualizar_skill(pedido: str, dominio: str, acervo: list, forca: bool = False) -> dict:
    """Cria (se nao existe similar) ou atualiza (se existe) uma skill para o pedido."""
    similar = _buscar_similar(pedido, acervo) if not forca else None

    if similar:
        # ATUALIZA a skill existente: adiciona um exemplo/uso, sem duplicar.
        path = ROOT / similar["path"]
        try:
            conteudo = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            conteudo = ""
        exemplo_linha = f"\n- Recorrência registrada em {datetime.now().strftime('%Y-%m-%d')}: {pedido}\n"
        if pedido not in conteudo:
            novo = conteudo.rstrip() + exemplo_linha
            tmp = path.with_suffix(".tmp")
            tmp.write_text(novo, encoding="utf-8")
            tmp.replace(path)
        return {"acao": "atualizada", "id": similar["id"], "dominio": similar["dominio"], "path": similar["path"]}

    # CRIA nova skill
    skill_id = _slug(pedido)
    dominio_uso = dominio or _dominio_sugerido(pedido)
    pasta = ACERVO_HABILIDADES / dominio_uso / "habilidades" / skill_id
    pasta.mkdir(parents=True, exist_ok=True)
    md = pasta / "skill.md"
    if md.exists():
        # Ja existe no disco mas nao foi achada por similaridade: atualiza.
        try:
            conteudo = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            conteudo = ""
        if pedido not in conteudo:
            tmp = md.with_suffix(".tmp")
            tmp.write_text(conteudo.rstrip() + f"\n- Uso: {pedido}\n", encoding="utf-8")
            tmp.replace(md)
        return {"acao": "existia", "id": skill_id, "dominio": dominio_uso, "path": str(md.relative_to(ROOT))}

    titulo = pedido.strip()[:80]
    descricao = f"Skill automatica gerada por recorrencia de pedidos. Trigger keywords: '{pedido}'. Atualizada pelo ecossistema sempre que o mesmo pedido se repetir."
    corpo = f"""---
name: {skill_id}
description: "{descricao}"
---

# {titulo}

Habilidade criada automaticamente pelo ecossistema (skill_recorrente.py).

## Quando usar

Quando o pedido a seguir se repete:

"{pedido}"

## Origem

- Gerada por recorrencia (3+ repeticoes) em {datetime.now().strftime('%Y-%m-%d')}.
- Atualizada automaticamente se o mesmo pedido voltar a se repetir.
"""
    tmp = md.with_suffix(".tmp")
    tmp.write_text(corpo, encoding="utf-8")
    tmp.replace(md)

    # Registra no inventario (só se ainda nao estiver)
    _registrar_inventario(dominio_uso, skill_id)
    return {"acao": "criada", "id": skill_id, "dominio": dominio_uso, "path": str(md.relative_to(ROOT))}


def _registrar_inventario(dominio: str, skill_id: str):
    try:
        data = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    except Exception:
        return
    secoes = data.get("mcp_habilidades", {})
    lista = secoes.setdefault(dominio, [])
    if skill_id not in lista:
        lista.append(skill_id)
        data["mcp_habilidades"] = secoes
        data["atualizado_em"] = datetime.now().isoformat()
        _atomic_write_json(INVENTARIO, data)


def _cmd_register(args) -> int:
    if not ENABLED:
        print("[skill] desativado via SKILL_RECURRENT=0")
        return 0
    rec = _ler_recorrencias()
    chave = _chave_pedido(args.pedido)
    entry = rec.get(chave, {"pedido": args.pedido, "contagem": 0, "ultima_vez": None})
    entry["pedido"] = args.pedido
    entry["contagem"] = int(entry.get("contagem", 0)) + 1
    entry["ultima_vez"] = datetime.now().isoformat()
    rec[chave] = entry
    _atomic_write_json(RECORRENCIA_FILE, rec)
    contagem = entry["contagem"]
    print(f"[skill] recorrencia {contagem}x para: {args.pedido}")

    limiar = args.limiar
    if contagem >= limiar:
        acervo = _scan_acervo()
        dominio = _dominio_sugerido(args.pedido) if not args.dominio else args.dominio
        res = _criar_atualizar_skill(args.pedido, dominio, acervo)
        # zera o contador depois de processar (evita re-processar o mesmo pedido)
        entry["contagem"] = 0
        rec[chave] = entry
        _atomic_write_json(RECORRENCIA_FILE, rec)
        print(f"[skill] {res['acao'].upper()} -> id={res['id']} dominio={res['dominio']} path={res['path']}")
    return 0


def _cmd_process(args) -> int:
    acervo = _scan_acervo()
    dominio = args.dominio or _dominio_sugerido(args.pedido)
    res = _criar_atualizar_skill(args.pedido, dominio, acervo, forca=args.forca)
    print(f"[skill] {res['acao'].upper()} (forca={args.forca}) -> id={res['id']} dominio={res['dominio']} path={res['path']}")
    return 0


def _cmd_status(args) -> int:
    rec = _ler_recorrencias()
    if not rec:
        print("[skill] nenhuma recorrencia registrada.")
        return 0
    print(f"[skill] {len(rec)} recorrencias em rastreamento:")
    for chave, e in sorted(rec.items(), key=lambda x: x[1].get("contagem", 0), reverse=True):
        print(f"  {e.get('contagem', 0)}x  {e.get('pedido', chave)}")
    return 0


def _cmd_reset(args) -> int:
    rec = _ler_recorrencias()
    chave = _chave_pedido(args.pedido)
    if chave in rec:
        del rec[chave]
        _atomic_write_json(RECORRENCIA_FILE, rec)
        print(f"[skill] recorrencia removida para: {args.pedido}")
    else:
        print(f"[skill] nada a remover: {args.pedido}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Criacao/atualizacao de skills por recorrencia")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_reg = sub.add_parser("register")
    p_reg.add_argument("pedido")
    p_reg.add_argument("--dominio", default="")
    p_reg.add_argument("--limiar", type=int, default=3)
    p_reg.set_defaults(func=_cmd_register)

    p_pro = sub.add_parser("process")
    p_pro.add_argument("pedido")
    p_pro.add_argument("--dominio", default="")
    p_pro.add_argument("--forca", action="store_true")
    p_pro.set_defaults(func=_cmd_process)

    p_sta = sub.add_parser("status")
    p_sta.set_defaults(func=_cmd_status)

    p_res = sub.add_parser("reset")
    p_res.add_argument("pedido")
    p_res.set_defaults(func=_cmd_reset)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
