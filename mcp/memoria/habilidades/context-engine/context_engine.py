"""context-engine: motor de contexto do coordenador.

Modos (CLI):
  --buscar "query"        busca semantica unificada (BM25 + grafo + memoria + notas)
  --paralelo "a|b|c"      orquestracao paralela de subtarefas (pool + locks)
  --gravar "titulo" "ctx" grava memoria episodica em conhecimento/episodios.json
  --episodio "assunto"    consulta memorias episodicas por assunto
  --drift                 detecta desvios entre estado atual e especificacoes
  --impacto "arquivo"     sintese proativa: quem referencia o alvo (cascata)

Python puro, sem dependencias externas (Clausula Petrea).
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

_base = Path(__file__).resolve().parent
while not (_base / "ler-runtime").is_dir() and _base.parent != _base:
    _base = _base.parent
ROOT = _base  # raiz do ecossistema (contem ler-runtime/ e conhecimento/)
CONH = ROOT / "conhecimento"
EPISODIOS = CONH / "episodios.json"
NOTAS = CONH / "notas"
LER_KNOWLEDGE = ROOT / "ler-runtime" / "knowledge" / "knowledge_graph.json"
MEMORIES = CONH / "memoria" / "memories.json"


# --------------------------------------------------------------------------
# 1) CONTEXTO SEMANTICO UNIFICADO
# --------------------------------------------------------------------------
def tokenize(text):
    return re.findall(r'[a-zA-Z\u00C0-\u024F]+|\d+', text.lower())


def bm25(query, docs, k1=1.5, b=0.75, top=12):
    q_tokens = tokenize(query)
    if not q_tokens:
        return []
    N = len(docs)
    avgdl = sum(len(tokenize(d)) for _, d in docs) / max(N, 1)
    idf = {}
    for qt in set(q_tokens):
        n = sum(1 for _, d in docs if qt in tokenize(d))
        idf[qt] = __import__("math").log((N - n + 0.5) / (n + 0.5) + 1)
    scored = []
    for doc_id, text in docs:
        tokens = tokenize(text)
        dl = len(tokens)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        score = 0
        for qt in q_tokens:
            if qt in tf:
                score += idf.get(qt, 0) * (tf[qt] * (k1 + 1)) / (tf[qt] + k1 * (1 - b + b * dl / avgdl))
        scored.append((score, doc_id, text))
    scored.sort(key=lambda x: -x[0])
    return [d for s, d, t in scored[:top] if s > 0]


def _load_corpus():
    docs = []
    if LER_KNOWLEDGE.exists():
        try:
            g = json.loads(LER_KNOWLEDGE.read_text(encoding="utf-8"))
            for cat in ("patterns", "decisions", "bug_fixes", "cognitive_patterns", "heuristics", "frameworks"):
                for item in g.get(cat, []):
                    title = item.get("title", item.get("decision", item.get("name", cat)))
                    docs.append((f"kg:{cat}/{str(title)[:50]}", json.dumps(item, ensure_ascii=False)[:2000]))
        except Exception:
            pass
    if MEMORIES.exists():
        try:
            mems = json.loads(MEMORIES.read_text(encoding="utf-8"))
            items = mems if isinstance(mems, list) else mems.get("memories", mems.get("items", []))
            for m in items:
                t = m.get("titulo") or m.get("title", "")
                s = m.get("resumo") or m.get("summary", "")
                docs.append((f"mem:{str(t)[:50]}", f"{t} {s}"))
        except Exception:
            pass
    if NOTAS.is_dir():
        for p in NOTAS.rglob("*.md"):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                docs.append((f"nota:{p.relative_to(NOTAS)}", txt[:2000]))
            except Exception:
                pass
    return docs


def cmd_buscar(query):
    docs = _load_corpus()
    hits = bm25(query, docs)
    print(f"== Contexto sobre: {query} ==")
    if not hits:
        print("  (sem resultados)")
        return
    for h in hits:
        print(f"  [{h}]")
    print(f"\n({len(hits)} resultados | corpus {len(docs)} itens)")


# --------------------------------------------------------------------------
# 2) ORQUESTRACAO PARALELA
# --------------------------------------------------------------------------
def cmd_paralelo(pipe):
    tasks = [t.strip() for t in pipe.split("|") if t.strip()]
    disp = ROOT / "scripts" / "parallel_dispatcher.py"
    if not disp.exists():
        print("ERRO: parallel_dispatcher.py nao encontrado em scripts/")
        return 1
    print(f"== Orquestracao paralela: {len(tasks)} subtarefas (pool=4) ==")
    # cada subtarefa vira um job que roda um comando via shell
    jobs = []
    for i, t in enumerate(tasks, 1):
        jobs.append({
            "name": f"tarefa-{i}",
            "command": t,
            "cwd": str(ROOT),
            "read_files": [],
            "write_files": [],
            "depends_on": [],
        })
    tmp = ROOT / "context" / "tarefas_paralelas.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    r = subprocess.run([sys.executable, str(disp), str(tmp)],
                       capture_output=True, text=True, timeout=600)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr[:300])
    return r.returncode


# --------------------------------------------------------------------------
# 3) MEMORIA EPISODICA
# --------------------------------------------------------------------------
def _load_episodios():
    if EPISODIOS.exists():
        try:
            return json.loads(EPISODIOS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def cmd_gravar(titulo, contexto):
    eps = _load_episodios()
    eps.append({
        "titulo": titulo,
        "contexto": contexto,
        "ts": __import__("time").time(),
    })
    EPISODIOS.write_text(json.dumps(eps, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] memoria episodica gravada ({len(eps)} episodios): {titulo}")


def cmd_episodio(assunto):
    eps = _load_episodios()
    qt = set(tokenize(assunto))
    hits = [e for e in eps if qt & set(tokenize(e.get("titulo", "") + " " + e.get("contexto", "")))]
    print(f"== Episodios sobre: {assunto} ==")
    if not hits:
        print("  (nenhum episodio encontrado)")
        return
    for e in hits[-10:]:
        print(f"  - {e.get('titulo')}: {e.get('contexto', '')[:200]}")


# --------------------------------------------------------------------------
# 4) DETECCAO DE DRIFT
# --------------------------------------------------------------------------
def cmd_drift():
    print("== Deteccao de drift vs especificacao ==")
    alertas = []
    specs = [ROOT / "ler-runtime" / "SYSTEM_SPEC.md", ROOT / "ler-runtime" / "CONHECIMENTO.md"]
    for sp in specs:
        if not sp.exists():
            alertas.append(f"ESPECIFICACAO AUSENTE: {sp.name}")
            continue
        txt = sp.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'(?:scripts|mcp|ler-runtime)/([\w\-.]+)\.(?:py|ps1|md|jsonc)', txt):
            ref = m.group(0)
            # resolve referencias simples a caminhos que deveriam existir
            parts = ref.split("/")
            cand = ROOT.joinpath(*parts) if len(parts) == 2 else None
            if cand and not cand.exists():
                alertas.append(f"DRIFT: {ref} referenciado na spec mas nao existe")
    # manifesto_geral.json na raiz (contrato de habilidades)
    if not (ROOT / "manifesto_geral.json").exists():
        alertas.append("MANIFESTO: manifesto_geral.json nao existe (contrato de habilidades ausente)")
    if alertas:
        for a in alertas:
            print(f"  ! {a}")
    else:
        print("  sem desvios detectados")
    return 0


# --------------------------------------------------------------------------
# 5) SINTESE PROATIVA (impacto em cascata)
# --------------------------------------------------------------------------
def cmd_impacto(alvo):
    print(f"== Impacto em cascata de: {alvo} ==")
    alvo = alvo.lower()
    refs = []
    for p in list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.jsonc")):
        if "node_modules" in str(p) or "backups" in str(p) or ".git" in str(p):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if alvo in txt.lower():
            refs.append(p.relative_to(ROOT))
    if not refs:
        print("  nenhum arquivo referencia o alvo")
        return
    for r in refs[:25]:
        print(f"  - {r}")
    print(f"({len(refs)} referencias)")


def main():
    ap = argparse.ArgumentParser(description="context-engine: motor de contexto do coordenador")
    ap.add_argument("--buscar")
    ap.add_argument("--paralelo")
    ap.add_argument("--gravar", nargs=2, metavar=("TITULO", "CONTEXTO"))
    ap.add_argument("--episodio")
    ap.add_argument("--drift", action="store_true")
    ap.add_argument("--impacto")
    args = ap.parse_args()

    if args.buscar:
        return cmd_buscar(args.buscar)
    if args.paralelo:
        return cmd_paralelo(args.paralelo)
    if args.gravar:
        return cmd_gravar(args.gravar[0], args.gravar[1])
    if args.episodio:
        return cmd_episodio(args.episodio)
    if args.drift:
        return cmd_drift()
    if args.impacto:
        return cmd_impacto(args.impacto)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
