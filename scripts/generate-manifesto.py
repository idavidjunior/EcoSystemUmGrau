"""Gera manifesto_geral.json (contrato de habilidades) a partir de mcp/<dominio>/habilidades/.

Escaneia cada subpasta com skill.md/SKILL.md, extrai frontmatter (name/description),
e registra id, categoria (dominio), entrypoint e triggers. Sempre que uma skill for
adicionada/removida, rode: python scripts/generate-manifesto.py
"""
import json, os, re, sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
ROOT = Path(BASE)
MCP_DIR = ROOT / "mcp"
OUT = ROOT / "manifesto_geral.json"

CATEGORIA = {
    "android": "tecnica",
    "desenvolvimento": "tecnica",
    "internet": "ponte",
    "memoria": "memoria",
    "comportamentais": "comportamental",
    "multimidia": "multimidia",
}


def parse_frontmatter(text):
    """Extrai dicionario do frontmatter YAML simples (--- ... ---)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            fm[k] = v
    return fm


def main():
    manifest = {"_meta": {
        "fonte": "mcp/<dominio>/habilidades/",
        "gerado_por": "scripts/generate-manifesto.py",
        "contrato": "Se nao esta no manifesto, nao existe para o Jarvis.",
    }, "habilidades": []}

    if not MCP_DIR.is_dir():
        print("ERRO: mcp/ nao encontrado")
        return 1

    for dominio_dir in sorted(MCP_DIR.iterdir()):
        if not dominio_dir.is_dir():
            continue
        hab = dominio_dir / "habilidades"
        if not hab.is_dir():
            continue
        dominio = dominio_dir.name
        for sk in sorted(hab.iterdir()):
            if not sk.is_dir():
                continue
            skill_md = None
            for name in ("skill.md", "SKILL.md"):
                cand = sk / name
                if cand.exists():
                    skill_md = cand
                    break
            fm = {}
            if skill_md:
                fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="ignore"))
            entry = None
            for e in ("skill.md", "SKILL.md"):
                if (sk / e).exists():
                    entry = f"mcp/{dominio}/habilidades/{sk.name}/{e}"
                    break
            script = None
            for e in sorted(sk.glob("*.py")):
                script = f"mcp/{dominio}/habilidades/{sk.name}/{e.name}"
                break
            manifest["habilidades"].append({
                "id": sk.name,
                "categoria": CATEGORIA.get(dominio, "tecnica"),
                "dominio": dominio,
                "nome": fm.get("name", sk.name),
                "descricao": fm.get("description", ""),
                "entrypoint": entry,
                "script": script,
                "triggers": [t.strip() for t in fm.get("description", "").split('"') if t.strip()][:8],
            })

    manifest["habilidades"].sort(key=lambda h: (h["categoria"], h["id"]))
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] manifesto_geral.json gerado: {len(manifest['habilidades'])} habilidades")


if __name__ == "__main__":
    sys.exit(main())
