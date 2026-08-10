"""desejo_aprendizado.py — Jarvis manifesta o que gostaria de aprender.

Coleta sinais REAIS do ecossistema e gera frases curtas e TTS-friendly que o
Jarvis diz "de vez em quando":

  1. Erros recorrentes  -> memorias kind=erro com mais acessos/reforco.
  2. Padroes em formacao -> aprendizados da skill auditoria-de-codigo com
                            >=2 ocorrencias e ainda fora do checklist.
  3. Descobertas recentes -> ultimos arquivos em conhecimento/aprendizados/.
  4. Dominios sub-cobertos -> categorias com menos skills no manifesto.

Anti-repeticao: cada desejo tem assinatura; a mesma assinatura so reaparece
depois de 3 manifestacoes diferentes. Historico em runtime/desejos_aprendizado.json.

Uso:
  python scripts/desejo_aprendizado.py [--voz] [--max N] [--linha-unica]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORICO = ROOT / "runtime" / "desejos_aprendizado.json"
REPETIR_APOS = 3
MAX_HISTORICO = 30
VOX = ROOT / "scripts" / "vox_audio.py"
AUDIT_LEARN = ROOT / "mcp" / "desenvolvimento" / "habilidades" / "auditoria-de-codigo" / "aprendizados.json"
MANIFESTO = ROOT / "manifesto_geral.json"
APRENDIZADOS_DIR = ROOT / "conhecimento" / "aprendizados"


def ler_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return default


def assinar(chave):
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()[:12]


def sinais_memoria(ignoradas):
    """Erros recorrentes: peso = acessos + forca."""
    dados = ler_json(ROOT / "conhecimento" / "memoria" / "memories.json", [])
    itens = dados if isinstance(dados, list) else dados.get("memories", [])
    erros = [m for m in itens if m.get("kind") == "erro"]
    erros.sort(key=lambda m: -(m.get("access_count", 0) + m.get("strength", 0)))
    frases = []
    for m in erros[:6]:
        chave = "erro:" + m.get("task", "")[:60]
        if assinar(chave) in ignoradas:
            continue
        task = " ".join((m.get("task") or "").split())
        if not task:
            continue
        peso = m.get("access_count", 0) + m.get("strength", 0)
        if peso < 1.5:
            continue
        frases.append((chave, f"evitar o erro recorrente de {task}."))
    return frases


def sinais_auditoria(ignoradas):
    """Padroes com >=2 ocorrencias ainda fora do checklist."""
    dados = ler_json(AUDIT_LEARN, [])
    frases = []
    for a in dados:
        if a.get("em_checklist") or a.get("recorrencias", 1) < 2:
            continue
        chave = "audit:" + a.get("titulo", "")[:60]
        if assinar(chave) in ignoradas:
            continue
        frases.append((chave, f"aprofundar o padrao {a.get('titulo')} que ja se repetiu {a.get('recorrencias')} vezes."))
    return frases


def sinais_recentes(ignoradas):
    """Ultimas descobertas registradas em conhecimento/aprendizados/."""
    if not APRENDIZADOS_DIR.is_dir():
        return []
    arquivos = sorted(APRENDIZADOS_DIR.glob("*.md"), key=lambda p: p.name, reverse=True)[:5]
    frases = []
    for p in arquivos:
        tema = p.stem.split("-", 3)[-1].replace("-", " ")
        if not tema:
            continue
        chave = "recente:" + p.name[:60]
        if assinar(chave) in ignoradas:
            continue
        frases.append((chave, f"explorar mais o tema {tema}."))
    return frases


def sinais_cobertura(ignoradas):
    """Categorias com menos skills no manifesto_geral.json."""
    manifest = ler_json(MANIFESTO, {"habilidades": []})
    por_cat = {}
    for h in manifest.get("habilidades", []):
        cat = h.get("categoria", "tecnica")
        por_cat[cat] = por_cat.get(cat, 0) + 1
    frases = []
    for cat, qtd in sorted(por_cat.items(), key=lambda kv: kv[1])[:3]:
        chave = "cobertura:" + cat
        if assinar(chave) in ignoradas:
            continue
        frases.append((chave, f"aprender mais sobre o dominio {cat}, que tem apenas {qtd} skills."))
    return frases


def carregar_historico():
    hist = ler_json(HISTORICO, [])
    return [h for h in hist if isinstance(h, dict)]


def salvar_historico(hist):
    try:
        HISTORICO.parent.mkdir(parents=True, exist_ok=True)
        tmp = HISTORICO.with_suffix(".tmp")
        tmp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(HISTORICO)
    except Exception as e:
        print(f"  ! historico nao salvo: {e}")


def gerar(limite, linhas_unica):
    hist = carregar_historico()
    usadas_recentes = [h["sig"] for h in hist[-REPETIR_APOS:]]
    candidatas = []
    for coletor in (sinais_memoria, sinais_auditoria, sinais_recentes, sinais_cobertura):
        candidatas.extend(coletor(set(usadas_recentes)))
    if not candidatas:
        return ["tenho tudo o que preciso por enquanto; quando descobrir algo novo, aviso."], hist
    if linhas_unica:
        escolhidas = candidatas[:limite]
    else:
        escolhidas = [c for c in candidatas if assinar(c[0]) not in usadas_recentes][:limite]
        if not escolhidas:
            escolhidas = candidatas[:limite]
    for chave, _ in escolhidas:
        hist.append({"data": date.today().isoformat(), "sig": assinar(chave), "chave": chave})
    if len(hist) > MAX_HISTORICO:
        hist = hist[-MAX_HISTORICO:]
    salvar_historico(hist)
    return [f for _, f in escolhidas], hist


def manifestar(linhas, com_voz, linha_unica):
    if linha_unica:
        texto = " ".join(linhas)
    else:
        partes = [f"{i+1}: {l}" for i, l in enumerate(linhas)]
        texto = " ".join(partes)
    print("[jarvis quer aprender] " + texto)
    if com_voz:
        try:
            subprocess.run([sys.executable, str(VOX), "falar", texto], timeout=90, check=False)
        except Exception as e:
            print(f"  ! voz falhou: {e}")


def main():
    ap = argparse.ArgumentParser(description="Jarvis manifesta o que gostaria de aprender")
    ap.add_argument("--voz", action="store_true", help="fala via TTS (vox_audio falar)")
    ap.add_argument("--max", type=int, default=3, help="maximo de desejos por manifestacao")
    ap.add_argument("--linha-unica", action="store_true", help="formato TTS de linha unica")
    args = ap.parse_args()
    linhas, _ = gerar(args.max, args.linha_unica)
    manifestar(linhas, args.voz, args.linha_unica)
    return 0


if __name__ == "__main__":
    sys.exit(main())
