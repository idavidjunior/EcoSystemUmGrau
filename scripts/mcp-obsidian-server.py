#!/usr/bin/env python3
"""Obsidian MCP Server — Python puro.
Expõe o vault Obsidian (pastas docs/, conhecimento/, documentos/) como MCP tools.
"""
import json, sys, os, re
from pathlib import Path

VAULT_DIRS = ["docs", "conhecimento", "documentos"]
ECO_ROOT = str(Path(__file__).resolve().parent.parent)
MAX_RESULTS = 50
MAX_EXCERPT = 300

def safe_resolve(rel_path):
    """Resolve path dentro do vault, bloqueia traversal."""
    if not rel_path:
        return Path(ECO_ROOT)
    base = Path(ECO_ROOT).resolve()
    target = (base / rel_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise PermissionError(f"Path fora do ecossistema: {rel_path}")
    return target

def list_vault(rel_dir="", recursive=False, max_depth=6):
    """Lista arquivos .md no vault."""
    abs_dir = safe_resolve(rel_dir)
    if not abs_dir.exists() or not abs_dir.is_dir():
        return {"error": f"Diretório não encontrado: {rel_dir}"}
    
    items = []
    def walk(root, depth):
        if depth > max_depth:
            return
        try:
            for e in root.iterdir():
                if e.name in (".git", ".obsidian", "node_modules", "__pycache__"):
                    continue
                if e.is_dir():
                    items.append({"name": e.name, "type": "directory", "path": str(e.relative_to(ECO_ROOT))})
                    walk(e, depth + 1)
                elif e.suffix.lower() == ".md":
                    items.append({"name": e.name, "type": "file", "path": str(e.relative_to(ECO_ROOT)), "size": e.stat().st_size})
        except Exception:
            pass
    
    if recursive:
        walk(abs_dir, 0)
    else:
        try:
            for e in abs_dir.iterdir():
                if e.name in (".git", ".obsidian", "node_modules", "__pycache__"):
                    continue
                if e.is_dir():
                    items.append({"name": e.name, "type": "directory", "path": str(e.relative_to(ECO_ROOT))})
                elif e.suffix.lower() == ".md":
                    items.append({"name": e.name, "type": "file", "path": str(e.relative_to(ECO_ROOT)), "size": e.stat().st_size})
        except Exception:
            pass
    return {"vault_root": rel_dir or "/", "count": len(items), "items": items}

def read_note(path, offset=0, limit=2000):
    """Lê uma nota .md do vault."""
    abs_path = safe_resolve(path)
    if not abs_path.exists() or not abs_path.is_file():
        return {"error": f"Arquivo não encontrado: {path}"}
    if abs_path.suffix.lower() != ".md":
        return {"error": "Apenas arquivos .md são permitidos"}
    try:
        content = abs_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        start = max(0, offset)
        end = start + limit
        excerpt = "\n".join(lines[start:end])
        return {
            "path": path,
            "total_lines": len(lines),
            "content": excerpt,
            "truncated": len(lines) > end
        }
    except UnicodeDecodeError:
        return {"error": "Arquivo não é UTF-8 válido"}

def search_vault(query, limit=20):
    """Busca BM25 simples no vault."""
    if not query or not query.strip():
        return {"error": "Query vazia"}
    
    q_terms = set(re.findall(r"[a-zà-ÿ0-9]{2,}", query.lower()))
    if not q_terms:
        return {"results": []}
    
    results = []
    for vault_dir in VAULT_DIRS:
        abs_dir = Path(ECO_ROOT) / vault_dir
        if not abs_dir.exists():
            continue
        for md_file in abs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = content.split("\n")
            score = 0
            excerpts = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                line_terms = set(re.findall(r"[a-zà-ÿ0-9]{2,}", line_lower))
                match_score = len(q_terms & line_terms)
                if match_score > 0:
                    score += match_score
                    excerpts.append({"line": i + 1, "text": line.strip()[:MAX_EXCERPT]})
            if score > 0:
                results.append({
                    "source": vault_dir,
                    "path": str(md_file.relative_to(ECO_ROOT)),
                    "score": score,
                    "excerpts": excerpts[:5]
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"query": query, "total_hits": len(results), "results": results[:limit]}

def vault_summary():
    """Resumo estatístico do vault."""
    total = 0
    by_dir = {}
    for d in VAULT_DIRS:
        abs_dir = Path(ECO_ROOT) / d
        if abs_dir.exists():
            md_files = list(abs_dir.rglob("*.md"))
            by_dir[d] = len(md_files)
            total += len(md_files)
        else:
            by_dir[d] = 0
    return {"total_notes": total, "by_directory": by_dir, "vault_dirs": VAULT_DIRS}

TOOLS = [
    {
        "name": "list-vault",
        "description": "Lista diretórios e arquivos .md no vault Obsidian.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho relativo dentro do vault (ex: 'conhecimento/aprendizados')"},
                "recursive": {"type": "boolean", "description": "Listar recursivamente"},
                "max_depth": {"type": "integer", "description": "Profundidade máxima se recursive=true", "default": 6}
            }
        }
    },
    {
        "name": "read-note",
        "description": "Lê o conteúdo de uma nota .md do vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho relativo da nota (ex: 'conhecimento/aprendizados/2026-07-27-1.md')"},
                "offset": {"type": "integer", "description": "Linha inicial", "default": 0},
                "limit": {"type": "integer", "description": "Máximo de linhas", "default": 2000}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search-vault",
        "description": "Busca textual (BM25 simples) nas notas do vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termos de busca"},
                "limit": {"type": "integer", "description": "Máximo de resultados", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "vault-summary",
        "description": "Retorna estatísticas do vault (contagem de notas por diretório).",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})
    
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "eco-obsidian", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}
    
    if method in ("notifications/initialized",):
        return {"jsonrpc": "2.0", "id": rid, "result": {}} if rid else None
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "tools": [{"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]} for t in TOOLS]
        }}
    
    if method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            if tool_name == "list-vault":
                result = list_vault(args.get("path", ""), args.get("recursive", False), args.get("max_depth", 6))
            elif tool_name == "read-note":
                result = read_note(args.get("path", ""), args.get("offset", 0), args.get("limit", 2000))
            elif tool_name == "search-vault":
                result = search_vault(args.get("query", ""), args.get("limit", 20))
            elif tool_name == "vault-summary":
                result = vault_summary()
            else:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}}
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(e)}}
    
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    return None

def main():
    for line in sys.stdin:
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

if __name__ == "__main__":
    main()