"""MCP server generico por dominio. Expoe cada habilidade do dominio como uma
ferramenta que instrui a IA a carregar a skill (SKILL.md/skill.md).

Servidor Python puro, sem dependencias externas (Clausula Petrea: proibido npx).
Uso: python mcp/<dominio>/server.py

Otimização: Lazy loading — skills são descobertas e lidas sob demanda,
não no import time. Evita 76+ read_text() bloqueantes no startup.
"""
import json
import sys
import os
from pathlib import Path
from functools import lru_cache

BASE = str(Path(__file__).resolve().parent.parent.parent)
DOMINIO = Path(__file__).resolve().parent.name

HAB_DIR = Path(__file__).resolve().parent / "habilidades"

# Cache para skills descobertas (evita re-leitura)
_skills_cache = None
_skills_mtime = None

def _discover_skills():
    """Descobre skills disponíveis no diretório de habilidades.
    Retorna lista de dicts: {id, name, description, has_md, md_preview}
    """
    global _skills_cache, _skills_mtime
    
    # Verifica se o cache é válido (baseado em mtime do diretório)
    try:
        current_mtime = HAB_DIR.stat().st_mtime
        if _skills_cache is not None and _skills_mtime == current_mtime:
            return _skills_cache
    except OSError:
        pass
    
    skills = []
    if HAB_DIR.exists():
        for sk_dir in sorted(HAB_DIR.iterdir()):
            if not sk_dir.is_dir():
                continue
            skill_id = sk_dir.name
            skill_md = None
            for name in ("SKILL.md", "skill.md"):
                cand = sk_dir / name
                if cand.exists():
                    skill_md = cand
                    break
            
            has_md = skill_md is not None
            md_preview = ""
            if has_md:
                try:
                    md_preview = skill_md.read_text(encoding="utf-8", errors="ignore")[:800]
                except OSError:
                    pass
            
            skills.append({
                "id": skill_id,
                "name": f"skill-{skill_id}",
                "description": f"Habilidade '{skill_id}' do dominio {DOMINIO}. Instrui a execucao da skill. {md_preview}",
                "has_md": has_md,
            })
    
    _skills_cache = skills
    _skills_mtime = current_mtime if 'current_mtime' in locals() else 0
    return skills


def _get_tools():
    """Retorna lista de tools no formato MCP, usando descoberta lazy."""
    skills = _discover_skills()
    return [
        {
            "name": s["name"],
            "description": s["description"],
            "inputSchema": {
                "type": "object",
                "properties": {"argumentos": {"type": "string", "description": "Argumentos opcionais do skill"}},
            },
        }
        for s in skills
    ]


@lru_cache(maxsize=128)
def _read_skill_md(skill_id: str) -> str:
    """Lê o conteúdo completo de um SKILL.md (cached)."""
    sk_dir = HAB_DIR / skill_id
    for name in ("SKILL.md", "skill.md"):
        cand = sk_dir / name
        if cand.exists():
            try:
                return cand.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return ""
    return ""


def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})
    
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": f"mcp-{DOMINIO}", "version": "1.0.0"},
            "capabilities": {"tools": {}}}}
    
    if method == "notifications/initialized":
        return None
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": _get_tools()}}
    
    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)
    
    return None


def handle_tool(tool, args, rid):
    # Valida se a tool existe (usa descoberta lazy)
    skills = _discover_skills()
    skill_map = {s["name"]: s for s in skills}
    
    if tool not in skill_map:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    
    sk_id = tool.replace("skill-", "", 1)
    md = _read_skill_md(sk_id)
    argstr = args.get("argumentos", "")
    
    text = f"[skill:{sk_id}] dominio {DOMINIO}.\n"
    text += md[:6000]
    if argstr:
        text += "\n\n[argumentos]: " + str(argstr)
    
    return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}}


if __name__ == "__main__":
    from sys import stdin
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle(req)
            if resp is not None:
                print(json.dumps(resp), flush=True)
        except json.JSONDecodeError:
            pass