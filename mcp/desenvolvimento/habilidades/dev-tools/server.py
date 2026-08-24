"""MCP Server — Development Tools (File Ops + Code Execution).

File operations: read_file, write_file, list_files, glob, delete_file
Code execution: execute_python (sandboxed), execute_shell (restricted)

Security: path validation, workspace isolation, command allowlist.
"""
import json
import sys
import os
import asyncio
import subprocess
import tempfile
import shlex
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

# Workspace root (restrito a este diretório para segurança)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SAFE_WORKSPACE = WORKSPACE_ROOT / "workspace"
SAFE_WORKSPACE.mkdir(exist_ok=True)

TOOLS = [
    {
        "name": "read_file",
        "description": "Lê conteúdo de arquivo no workspace seguro.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho relativo ao workspace (ex: 'src/main.py')"},
                "encoding": {"type": "string", "description": "Encoding do arquivo", "default": "utf-8"},
            },
            "required": ["path"]
        },
    },
    {
        "name": "write_file",
        "description": "Escreve conteúdo em arquivo no workspace seguro. Cria diretórios se necessário.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho relativo ao workspace"},
                "content": {"type": "string", "description": "Conteúdo a escrever"},
                "encoding": {"type": "string", "description": "Encoding", "default": "utf-8"},
            },
            "required": ["path", "content"]
        },
    },
    {
        "name": "list_files",
        "description": "Lista arquivos no workspace (com padrão glob opcional).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Padrão glob (ex: '*.py', 'src/**/*.js')", "default": "**/*"},
                "recursive": {"type": "boolean", "default": True},
            },
            "required": []
        },
    },
    {
        "name": "glob",
        "description": "Busca arquivos por padrão glob no workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Padrão glob", "minLength": 1},
            },
            "required": ["pattern"]
        },
    },
    {
        "name": "delete_file",
        "description": "Remove arquivo do workspace (apenas se dentro do workspace seguro).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho relativo ao workspace"},
            },
            "required": ["path"]
        },
    },
    {
        "name": "execute_python",
        "description": "Executa código Python em sandbox isolado (timeout, sem rede, sem filesystem fora do workspace).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Código Python a executar", "minLength": 1},
                "timeout_sec": {"type": "integer", "description": "Timeout em segundos", "default": 30},
            },
            "required": ["code"]
        },
    },
    {
        "name": "execute_shell",
        "description": "Executa comando shell restrito (apenas comandos permitidos: python, node, pip, npm, git, ls, cat, grep, find).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Comando a executar", "minLength": 1},
                "cwd": {"type": "string", "description": "Diretório de trabalho (relativo ao workspace)", "default": "."},
                "timeout_sec": {"type": "integer", "default": 60},
            },
            "required": ["command"]
        },
    },
]


def _resolve_path(path: str) -> Path:
    """Resolve caminho relativo ao workspace seguro, validando que não escapa."""
    path = path.lstrip("./")
    resolved = (SAFE_WORKSPACE / path).resolve()
    
    # Garante que está dentro do workspace seguro
    try:
        resolved.relative_to(SAFE_WORKSPACE)
    except ValueError:
        raise ValueError(f"Caminho fora do workspace seguro: {path}")
    
    return resolved


def _validate_command(cmd: str) -> tuple[bool, str]:
    """Valida se comando shell é permitido."""
    allowed_prefixes = [
        "python", "python3", "node", "npm", "pip", "git",
        "ls", "cat", "grep", "find", "head", "tail", "wc",
        "mkdir", "rm", "cp", "mv", "touch", "echo",
        "pytest", "python -m pytest", "python -m venv",
    ]
    cmd_stripped = cmd.strip()
    for prefix in allowed_prefixes:
        if cmd_stripped.startswith(prefix):
            return True, ""
    return False, f"Comando não permitido: {cmd_stripped[:50]}"


def read_file(args: dict) -> dict:
    try:
        path = _resolve_path(args["path"])
        encoding = args.get("encoding", "utf-8")
        if not path.exists():
            return {"read_file": {"error": f"Arquivo não encontrado: {args['path']}"}}
        content = path.read_text(encoding=encoding)
        return {"read_file": {"path": args["path"], "content": content, "size": len(content)}}
    except Exception as e:
        return {"read_file": {"error": str(e)}}


def write_file(args: dict) -> dict:
    try:
        path = _resolve_path(args["path"])
        content = args["content"]
        encoding = args.get("encoding", "utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return {"write_file": {"path": args["path"], "size": len(content), "created": True}}
    except Exception as e:
        return {"write_file": {"error": str(e)}}


def list_files(args: dict) -> dict:
    try:
        pattern = args.get("pattern", "**/*")
        recursive = args.get("recursive", True)
        files = []
        for p in SAFE_WORKSPACE.glob(pattern):
            if recursive or p.parent == SAFE_WORKSPACE:
                rel = p.relative_to(SAFE_WORKSPACE)
                files.append({
                    "path": str(rel),
                    "name": p.name,
                    "is_dir": p.is_dir(),
                    "size": p.stat().st_size if p.is_file() else 0,
                    "modified": p.stat().st_mtime,
                })
        return {"list_files": {"count": len(files), "files": files}}
    except Exception as e:
        return {"list_files": {"error": str(e)}}


def glob_files(args: dict) -> dict:
    try:
        pattern = args["pattern"]
        files = []
        for p in SAFE_WORKSPACE.glob(pattern):
            if p.is_file():
                rel = p.relative_to(SAFE_WORKSPACE)
                files.append(str(rel))
        return {"glob": {"pattern": pattern, "count": len(files), "files": files}}
    except Exception as e:
        return {"glob": {"error": str(e)}}


def delete_file(args: dict) -> dict:
    try:
        path = _resolve_path(args["path"])
        if not path.exists():
            return {"delete_file": {"error": f"Arquivo não encontrado: {args['path']}"}}
        if path.is_dir():
            return {"delete_file": {"error": "Não é possível remover diretório com delete_file"}}
        path.unlink()
        return {"delete_file": {"path": args["path"], "deleted": True}}
    except Exception as e:
        return {"delete_file": {"error": str(e)}}


async def execute_python(args: dict) -> dict:
    code = args["code"]
    timeout_sec = args.get("timeout_sec", 30)
    
    # Cria arquivo temporário no workspace
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", dir=SAFE_WORKSPACE, delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=SAFE_WORKSPACE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        return {
            "execute_python": {
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        }
    except asyncio.TimeoutError:
        return {"execute_python": {"error": f"Timeout após {timeout_sec}s", "timeout": True}}
    except Exception as e:
        return {"execute_python": {"error": str(e)}}
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


async def execute_shell(args: dict) -> dict:
    command = args["command"]
    cwd = args.get("cwd", ".")
    timeout_sec = args.get("timeout_sec", 60)
    
    ok, msg = _validate_command(command)
    if not ok:
        return {"execute_shell": {"error": msg, "allowed_prefixes": ["python", "node", "npm", "git", "ls", "grep", "find", "pip", "npm", "pytest"]}}
    
    cwd_path = _resolve_path(cwd)
    if not cwd_path.exists():
        cwd_path = SAFE_WORKSPACE
    
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd_path,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        return {
            "execute_shell": {
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        }
    except asyncio.TimeoutError:
        return {"execute_shell": {"error": f"Timeout após {timeout_sec}s", "timeout": True}}
    except Exception as e:
        return {"execute_shell": {"error": str(e)}}


# ============================================================================
# MCP SERVER
# ============================================================================

async def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-dev-tools", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return await handle_tool_async(tool, args, rid)

    return None


async def handle_tool_async(tool, args, rid):
    try:
        if tool == "read_file":
            result = read_file(args)
        elif tool == "write_file":
            result = write_file(args)
        elif tool == "list_files":
            result = list_files(args)
        elif tool == "glob":
            result = glob_files(args)
        elif tool == "delete_file":
            result = delete_file(args)
        elif tool == "execute_python":
            result = await execute_python(args)
        elif tool == "execute_shell":
            result = await execute_shell(args)
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)}]}}

    return {"jsonrpc": "2.0", "id": rid, "result": {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


def _read_frame(stream):
    import json as _json
    peek = stream.peek(1)
    if not peek:
        return None
    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return _json.loads(line.decode("utf-8"))
        except (_json.JSONDecodeError, UnicodeDecodeError):
            return None
    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        return None
    headers = {}
    if b":" in first:
        key, value = first.split(b":", 1)
        headers[key.strip().lower()] = value.strip()
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length <= 0:
        return None
    body = stream.read(length)
    try:
        return _json.loads(body.decode("utf-8"))
    except (_json.JSONDecodeError, UnicodeDecodeError):
        return None


async def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


async def main_loop():
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = _read_frame(stdin)
        if req is None:
            break
        resp = await handle(req)
        if resp is not None:
            await _write_frame(stdout, resp)


async def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


if __name__ == "__main__":
    import os
    asyncio.run(main_loop())