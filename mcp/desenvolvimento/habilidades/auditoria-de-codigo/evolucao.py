"""evolucao.py - cerebro da skill auditoria-de-codigo.

Alimenta a skill com aprendizados VALIDADOS (gates anti-lixo: evidencia
obrigatoria, dedup por similaridade, acionabilidade e anti-overfitting) e
revisa o SKILL.md quando padroes elegiveis acumulam. Fecha o loop com o
ecossistema via memory_engine (o ecossistema aprende da skill).

Comandos:
  add <titulo> <licao> [--tipo padrao|erro|episodio]
                       [--evidencia <caminho>] [--impacto alto|medio|baixo]
                       [--no-memoria] [--forcar]
  review               absorve padroes elegiveis no checklist do SKILL.md
  stats                painel de evolucao da skill
  prune [--dias 90]    limpeza periodica (rejeitados e padroes mortos)

Variaveis de ambiente:
  AUDITORIA_DIR   diretorio de dados da skill (padrao: pasta da propria skill).
                  Usado nos testes para rodar em diretorio isolado.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(os.environ.get("AUDITORIA_DIR", str(Path(__file__).resolve().parent)))

APRENDIZADOS = SKILL_DIR / "aprendizados.json"
REJEITADOS = SKILL_DIR / "rejeitados.json"
REVISOES = SKILL_DIR / "revisoes.json"
EVOLUCAO_MD = SKILL_DIR / "evolucao.md"
SKILL_MD = SKILL_DIR / "skill.md"

CHECKLIST_HEADING = "## Checklist de armadilhas conhecidas"
SIMILARIDADE_LIMITE = 0.80
ELIGIVEIS_MINIMO = 3
ACIONAVEIS = [
    "sempre", "nunca", "use", "usar", "evite", "verific", "valid", "cheque",
    "check", "corrig", "faca", "faça", "adicion", "remov", "teste", "deve",
    "precisa", "rebuild", "roda", "rode", "use ",
]
IMPACTOS = ("alto", "medio", "baixo")
TIPOS = ("padrao", "erro", "episodio")

_TOKEN_RE = re.compile(r"[^0-9a-zA-Z\u00c0-\u024f]+")


def hoje():
    return date.today().isoformat()


def ler_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def gravar_json(path, dados):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(path))


def tokenizar(texto):
    return set(t for t in _TOKEN_RE.sub(" ", texto.lower()).split() if len(t) > 1)


def similaridade(a, b):
    ta, tb = tokenizar(a), tokenizar(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def curto(texto, limite=160):
    texto = " ".join(texto.split())
    return texto[:limite] + ("..." if len(texto) > limite else "")


def acionavel(texto):
    base = texto.lower()
    return any(k in base for k in AACIONAVEIS)


def cmd_add(args):
    aprendizados = ler_json(APRENDIZADOS, [])
    rejeitados = ler_json(REJEITADOS, [])
    texto = args.titulo + " " + args.licao
    for a in aprendizados:
        if similaridade(a["titulo"] + " " + a["licao"], texto) >= SIMILARIDADE_LIMITE:
            a["recorrencias"] += 1
            a["ultima_ocorrencia"] = hoje()
            gravar_json(APRENDIZADOS, aprendizados)
            print(f"[dup] recorrência registrada em '{a['titulo']}' (total {a['recorrencias']})")
            return 0
    evidencia = args.evidencia
    if not evidencia and not args.forcar:
        _rejeitar(rejeitados, args, "evidencia obrigatoria")
        return 0
    if evidencia and evidencia != "auto":
        p = Path(evidencia)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists() and not args.forcar:
            _rejeitar(rejeitados, args, f"evidencia nao existe: {evidencia}")
            return 0
    acion = acionavel(texto)
    impacto = args.impacto if args.impacto in IMPACTOS else "medio"
    entry = {
        "id": hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12],
        "titulo": args.titulo,
        "licao": args.licao,
        "tipo": args.tipo if args.tipo in TIPOS else "padrao",
        "evidencia": evidencia or "(auto)",
        "impacto": impacto,
        "acionavel": acion,
        "recorrencias": 1,
        "primeira_ocorrencia": hoje(),
        "ultima_ocorrencia": hoje(),
        "em_checklist": False,
    }
    aprendizados.append(entry)
    gravar_json(APRENDIZADOS, aprendizados)
    status = "acao" if acion else "observacao (nao vira regra ate recorrer)"
    print(f"[ok] aprendizado aceito como {status}: {args.titulo}")
    if not args.no_memoria:
        _registrar_memoria(args)
    return 0


def _rejeitar(rejeitados, args, motivo):
    rejeitados.append({
        "titulo": args.titulo,
        "licao": args.licao,
        "motivo": motivo,
        "data": hoje(),
    })
    gravar_json(REJEITADOS, rejeitados)
    print(f"[rej] {motivo}: {args.titulo}")


def _registrar_memoria(args):
    script = ROOT / "scripts" / "memory_engine.py"
    if not script.exists():
        print("  ! memory_engine.py nao encontrado; memoria nao registrada")
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "add", args.titulo, args.licao, args.tipo or "padrao"],
            cwd=str(ROOT), timeout=60, check=False,
        )
    except Exception as e:
        print(f"  ! falha ao registrar memoria: {e}")


def cmd_review(args):
    aprendizados = ler_json(APRENDIZADOS, [])
    elegiveis = [
        a for a in aprendizados
        if a["acionavel"] and not a["em_checklist"]
        and (a["recorrencias"] >= 2 or a["impacto"] == "alto")
    ]
    if len(elegiveis) < ELIGIVEIS_MINIMO:
        print(f"[review] {len(elegiveis)} elegiveis (minimo {ELIGIVEIS_MINIMO}) - nada a absorver")
        return 0
    if not SKILL_MD.exists():
        print(f"[review] SKILL.md nao encontrado em {SKILL_MD}")
        return 1
    texto = SKILL_MD.read_text(encoding="utf-8")
    backup = SKILL_MD.with_suffix(".md.bak")
    backup.write_text(texto, encoding="utf-8")
    novos = [
        f"- [ ] {a['titulo']}: {curto(a['licao'], 140)}"
        for a in elegiveis
    ]
    idx = texto.find(CHECKLIST_HEADING)
    if idx >= 0:
        fim = texto.find("\n## ", idx + 1)
        if fim == -1:
            fim = len(texto)
        ins = texto.find("\n", idx) + 1
        bloco = "\n".join(novos) + "\n"
        novo = texto[:ins] + bloco + texto[ins:]
    else:
        novo = texto.rstrip() + "\n\n" + CHECKLIST_HEADING + "\n" + "\n".join(novos) + "\n"
    SKILL_MD.write_text(novo, encoding="utf-8")
    for a in elegiveis:
        a["em_checklist"] = True
    gravar_json(APRENDIZADOS, aprendizados)
    revisoes = ler_json(REVISOES, [])
    revisoes.append({
        "data": hoje(),
        "qtd": len(elegiveis),
        "itens": [a["titulo"] for a in elegiveis],
    })
    gravar_json(REVISOES, revisoes)
    _append_evolucao(f"review {hoje()} | absorvidos {len(elegiveis)} padroes no checklist | backup: {backup.name}")
    print(f"[review] {len(elegiveis)} padroes absorvidos no checklist do SKILL.md")
    return 0


def _append_evolucao(linha):
    try:
        with open(EVOLUCAO_MD, "a", encoding="utf-8") as f:
            f.write("- " + linha + "\n")
    except Exception as e:
        print(f"  ! nao foi possivel registrar em evolucao.md: {e}")


def cmd_stats(args):
    aprendizados = ler_json(APRENDIZADOS, [])
    rejeitados = ler_json(REJEITADOS, [])
    revisoes = ler_json(REVISOES, [])
    acionaveis = [a for a in aprendizados if a["acionavel"]]
    elegiveis = [
        a for a in acionaveis
        if not a["em_checklist"] and (a["recorrencias"] >= 2 or a["impacto"] == "alto")
    ]
    duplicados = sum(a["recorrencias"] - 1 for a in aprendizados)
    print("== Evolucao da skill auditoria-de-codigo ==")
    print(f"  aprendizados:        {len(aprendizados)}")
    print(f"  acionaveis:          {len(acionaveis)}")
    print(f"  em_checklist:        {len([a for a in aprendizados if a['em_checklist']])}")
    print(f"  elegiveis p/ review: {len(elegiveis)} (min {ELIGIVEIS_MINIMO})")
    print(f"  recorrencias(dup):   {duplicados}")
    print(f"  rejeitados:          {len(rejeitados)}")
    print(f"  revisoes:            {len(revisoes)}")
    if revisoes:
        print(f"  ultima revisao:      {revisoes[-1]['data']} ({revisoes[-1]['qtd']} itens)")
    for a in sorted(acionaveis, key=lambda x: -x["recorrencias"])[:5]:
        mark = "x" if a["em_checklist"] else " "
        print(f"  [{mark}] {a['titulo']} (x{a['recorrencias']}, {a['impacto']})")
    return 0


def cmd_prune(args):
    rejeitados = ler_json(REJEITADOS, [])
    aprendizados = ler_json(APRENDIZADOS, [])
    limite = date.today() - timedelta(days=args.dias)
    mantidos_r = []
    for r in rejeitados:
        try:
            d = datetime.strptime(r["data"], "%Y-%m-%d").date()
            if d >= limite:
                mantidos_r.append(r)
        except Exception:
            mantidos_r.append(r)
    removidos_r = len(rejeitados) - len(mantidos_r)
    gravar_json(REJEITADOS, mantidos_r)
    mantidos_a = []
    for a in aprendizados:
        try:
            d = datetime.strptime(a["ultima_ocorrencia"], "%Y-%m-%d").date()
            if a["em_checklist"] or d >= limite:
                mantidos_a.append(a)
        except Exception:
            mantidos_a.append(a)
    removidos_a = len(aprendizados) - len(mantidos_a)
    gravar_json(APRENDIZADOS, mantidos_a)
    print(f"[prune] rejeitados removidos: {removidos_r}; padroes mortos removidos: {removidos_a}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="cerebro de auto-evolucao da skill auditoria-de-codigo")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("titulo")
    p_add.add_argument("licao")
    p_add.add_argument("--tipo", choices=TIPOS, default="padrao")
    p_add.add_argument("--evidencia", default=None)
    p_add.add_argument("--impacto", choices=IMPACTOS, default="medio")
    p_add.add_argument("--no-memoria", action="store_true")
    p_add.add_argument("--forcar", action="store_true")
    p_add.set_defaults(fn=cmd_add)
    p_rev = sub.add_parser("review")
    p_rev.set_defaults(fn=cmd_review)
    p_sta = sub.add_parser("stats")
    p_sta.set_defaults(fn=cmd_stats)
    p_pru = sub.add_parser("prune")
    p_pru.add_argument("--dias", type=int, default=90)
    p_pru.set_defaults(fn=cmd_prune)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
