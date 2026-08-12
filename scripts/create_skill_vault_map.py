#!/usr/bin/env python3
"""Cria mapa de conexão: Skill MCP ↔ Notas do Vault Obsidian."""
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VAULT_NOTAS = BASE / "conhecimento" / "notas"
SKILLS_DIR = BASE / "mcp"

# Carregar todas as notas do vault
def carregar_notas():
    notas = {}
    for md_file in VAULT_NOTAS.rglob("*.md"):
        rel = md_file.relative_to(VAULT_NOTAS)
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            # Extrair frontmatter e tags
            tags = []
            if content.startswith("---"):
                fm_end = content.find("---", 3)
                if fm_end > 0:
                    fm = content[3:fm_end]
                    for line in fm.split("\n"):
                        if line.strip().startswith("tags:"):
                            # tags: [a, b, c] ou tags: a, b, c
                            tags_str = line.split(":", 1)[1].strip()
                            tags_str = tags_str.strip("[]")
                            tags = [t.strip().strip('"\'') for t in tags_str.split(",") if t.strip()]
            # Extrair primeiro parágrafo como resumo
            body = content.split("---", 2)[-1] if content.startswith("---") else content
            resumo = ""
            for line in body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("["):
                    resumo = line[:200]
                    break
            notas[str(rel)] = {
                "path": str(rel),
                "tags": tags,
                "resumo": resumo,
                "stem": md_file.stem.lower(),
            }
        except Exception:
            pass
    return notas

# Carregar todas as skills
def carregar_skills():
    skills = {}
    for skill_dir in SKILLS_DIR.rglob("habilidades"):
        if not skill_dir.is_dir():
            continue
        for sk in skill_dir.iterdir():
            if not sk.is_dir():
                continue
            skill_id = sk.name
            skill_md = sk / "SKILL.md"
            if not skill_md.exists():
                skill_md = sk / "skill.md"
            if not skill_md.exists():
                continue
            try:
                content = skill_md.read_text(encoding="utf-8", errors="ignore")
                # Extrair frontmatter
                name = skill_id
                description = ""
                triggers = ""
                if content.startswith("---"):
                    fm_end = content.find("---", 3)
                    if fm_end > 0:
                        fm = content[3:fm_end]
                        for line in fm.split("\n"):
                            if line.strip().startswith("name:"):
                                name = line.split(":", 1)[1].strip().strip('"\'')
                            elif line.strip().startswith("description:"):
                                description = line.split(":", 1)[1].strip().strip('"\'')
                            elif line.strip().startswith("Trigger keywords:") or line.strip().startswith("trigger keywords:"):
                                triggers = line.split(":", 1)[1].strip().strip('"\'')
                # Tags do diretório pai (domínio)
                dominio = skill_dir.parent.name
                skills[skill_id] = {
                    "id": skill_id,
                    "name": name,
                    "dominio": dominio,
                    "description": description,
                    "triggers": triggers,
                    "path": str(skill_md.relative_to(BASE)),
                }
            except Exception:
                pass
    return skills

# Mapear skills para notas por similaridade de tags/palavras-chave
def mapear(skills, notas):
    mapa = {}
    
    # Indexar notas por tags e stem
    notas_por_tag = {}
    for npath, ndata in notas.items():
        for tag in ndata["tags"]:
            notas_por_tag.setdefault(tag.lower(), []).append(npath)
        # Também indexar por palavras do stem
        for word in re.findall(r"[a-z]+", ndata["stem"]):
            if len(word) > 3:
                notas_por_tag.setdefault(word, []).append(npath)
    
    for sid, sdata in skills.items():
        matches = []
        
        # 1. Tags da skill (se houver no frontmatter) - não tem, usar triggers
        keywords = set()
        if sdata["triggers"]:
            keywords.update(re.findall(r"[a-z]+", sdata["triggers"].lower()))
        if sdata["description"]:
            keywords.update(re.findall(r"[a-z]+", sdata["description"].lower()))
        keywords.update(re.findall(r"[a-z]+", sdata["id"].lower()))
        keywords.update(re.findall(r"[a-z]+", sdata["dominio"].lower()))
        
        # Filtrar palavras muito comuns
        stopwords = {"e", "o", "a", "de", "da", "do", "em", "para", "com", "por", "um", "uma", "os", "as", "na", "no", "se", "que", "como", "ou", "se", "mas", "the", "and", "or", "to", "in", "for", "with", "on", "at", "by", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once"}
        keywords = {k for k in keywords if k not in stopwords and len(k) > 2}
        
        # Buscar notas correspondentes
        score_notas = {}
        for kw in keywords:
            for npath in notas_por_tag.get(kw, []):
                score_notas[npath] = score_notas.get(npath, 0) + 1
        
        # Ordenar por score
        top = sorted(score_notas.items(), key=lambda x: x[1], reverse=True)[:10]
        matches = [{"nota": n, "score": s, "resumo": notas[n]["resumo"][:120], "tags": notas[n]["tags"]} for n, s in top]
        
        mapa[sid] = {
            "skill": sdata,
            "notas_relacionadas": matches,
        }
    
    return mapa

def main():
    print("Carregando notas do vault...")
    notas = carregar_notas()
    print(f"  {len(notas)} notas carregadas")
    
    print("Carregando skills...")
    skills = carregar_skills()
    print(f"  {len(skills)} skills carregadas")
    
    print("Mapeando...")
    mapa = mapear(skills, notas)
    
    # Salvar JSON
    out_json = BASE / "skill_vault_map.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=2)
    print(f"Mapa salvo em: {out_json}")
    
    # Gerar markdown legível
    out_md = BASE / "SKILL_VAULT_MAP.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Mapa Skill ↔ Vault\n\n")
        f.write(f"Gerado automaticamente. {len(skills)} skills ↔ {len(notas)} notas.\n\n")
        
        # Agrupar por domínio
        por_dominio = {}
        for sid, mdata in mapa.items():
            dom = mdata["skill"]["dominio"]
            por_dominio.setdefault(dom, []).append((sid, mdata))
        
        for dom in sorted(por_dominio.keys()):
            f.write(f"## {dom.upper()} ({len(por_dominio[dom])} skills)\n\n")
            for sid, mdata in sorted(por_dominio[dom]):
                s = mdata["skill"]
                f.write(f"### {s['name']} (`{sid}`)\n")
                f.write(f"**Domínio:** {s['dominio']}  \n")
                if s["description"]:
                    f.write(f"**Descrição:** {s['description'][:200]}  \n")
                if s["triggers"]:
                    f.write(f"**Triggers:** {s['triggers'][:200]}  \n")
                f.write(f"**Caminho:** `{s['path']}`  \n")
                
                if mdata["notas_relacionadas"]:
                    f.write("\n**Notas do vault relacionadas:**\n")
                    for nr in mdata["notas_relacionadas"][:5]:
                        f.write(f"- [[{nr['nota']}]] (score {nr['score']}) — {nr['resumo']}  \n")
                else:
                    f.write("\n*Sem notas relacionadas encontradas automaticamente*\n")
                f.write("\n---\n\n")
    
    print(f"Markdown salvo em: {out_md}")

if __name__ == "__main__":
    main()