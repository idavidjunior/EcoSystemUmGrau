"""MCP server generico por dominio. Expoe cada habilidade do dominio como uma
ferramenta que instrui a IA a carregar a skill (SKILL.md/skill.md).

Servidor Python puro, sem dependencias externas (Clausula Petrea: proibido npx).
Uso: python mcp/<dominio>/server.py
"""
import json, sys, os
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent.parent)
DOMINIO = Path(__file__).resolve().parent.name

HAB_DIR = Path(__file__).resolve().parent / "habilidades"

TOOLS = []
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
    desc = f"Habilidade '{skill_id}' do dominio {DOMINIO}. Instrui a execucao da skill."
    from_md = ""
    if skill_md:
        from_md = skill_md.read_text(encoding="utf-8", errors="ignore")[:800]
    TOOLS.append({
        "name": f"skill-{skill_id}",
        "description": f"Carrega e orienta a habilidade {skill_id}. {from_md}",
        "inputSchema": {
            "type": "object",
            "properties": {"argumentos": {"type": "string", "description": "Argumentos opcionais do skill"}},
        },
    })
DATA = {"tools": TOOLS}


def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": f"mcp-{DOMAIN}", "version": "1.0.0"},
            "capabilities": {"tools": {}}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": DATA["tools"]}}
    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)
    return None


def handle_tool(tool, args, rid):
    per = [t for t in DATA["tools"] if t["name"] == tool]
    if not per:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    sk_id = tool.replace("skill-", "", 1)
    sk_dir = HAB_DIR / sk_id
    md = ""
    for name in ("SKILL.md", "skill.md"):
        cand = sk_dir / name
        if cand.exists():
            md = cand.read_text(encoding="utf-8", errors="ignore")
            break
    argstr = args.get("argumentos", "")
    text = f"[skill:{sk_id}] dominio {DOMAIN}.\n"
    text += md[:6000]
    if argstr:
        text += "\n\n[argumentos]: " + str(argstr)
    return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}}


if __name__ == "__main__":
    from sys import stdin, stdout
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