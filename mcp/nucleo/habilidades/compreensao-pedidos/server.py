"""MCP server — Compreensão de Pedidos.

Transforma pedidos do usuário em entendimento estruturado (objetivo, ações,
contexto, conceitos, restrições, ambiguidades, critérios, plano) e conecta ao
acervo do ecossistema (memória, skills, projetos, scripts). Sem DSPy; refino
com LLM é opcional e fail-soft (usa a LLM disponível).

Transporte: MCP stdio padrão (Content-Length framing).

Tools:
  - compreender_pedido    — entendimento completo de um pedido
  - avaliar_clareza       — score de clareza estático + lacunas
  - refinar_entendimento  — compreensão + refino opcional com a LLM disponível
  - resolver_conceitos    — resolve termos do pedido no acervo do ecossistema
  - detectar_desperdicio  — riscos de desperdício e atalhos (repetição, escopo)
"""
import json
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)

import compreensao as cp  # noqa: E402

TOOLS = [
    {
        "name": "compreender_pedido",
        "description": "Analisa um pedido do usuário e devolve o entendimento estruturado: objetivo, ações esperadas, contexto, conceitos, restrições, ambiguidades, critérios de sucesso, riscos, plano sugerido e score de clareza. Use SEMPRE que um pedido chegar, para evitar ambiguidade e desperdício.\n\nTrigger keywords: entender pedido, compreender, o que foi pedido, objetivo, plano de ação, interpretar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido/fala/comando do usuário", "minLength": 1}
            },
            "required": ["pedido"]
        },
    },
    {
        "name": "avaliar_clareza",
        "description": "Avalia estaticamente a clareza de um pedido (0-100) e lista lacunas/ambiguidades que custam tempo se ignoradas. Não usa LLM — custo zero.\n\nTrigger keywords: clareza, está claro, lacunas, ambiguidade, falta informação.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido a avaliar", "minLength": 1}
            },
            "required": ["pedido"]
        },
    },
    {
        "name": "refinar_entendimento",
        "description": "Executa a compreensão completa e refina com UMA chamada de LLM (a que estiver disponível: NVIDIA/OpenAI/Anthropic). Fail-soft: sem chave/modelo, retorna o entendimento estático com o motivo. Use para pedidos críticos/complexos.\n\nTrigger keywords: refinar entendimento, pedido crítico, validar interpretação, ambiguidade alta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido a compreender e refinar", "minLength": 1}
            },
            "required": ["pedido"]
        },
    },
    {
        "name": "resolver_conceitos",
        "description": "Resolve termos/conceitos do pedido contra o acervo do ecossistema: memória (BM25), skills MCP, projetos e scripts. Conecta 'o que foi dito' ao 'que o ecossistema sabe fazer'.\n\nTrigger keywords: conceito, significado, o que sabemos sobre, resolver termo, entidade.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conceitos": {"type": "array", "items": {"type": "string"}, "description": "Lista de conceitos/termos a resolver"},
                "pedido": {"type": "string", "description": "Opcional: pedido original (extrai conceitos automaticamente)"}
            },
            "required": []
        },
    },
    {
        "name": "detectar_desperdicio",
        "description": "Analisa riscos de desperdício de um pedido: pedido repetido (vs última tarefa), escopo inflado, pedido sem entregável claro, e sugere atalhos (skills/scripts existentes).\n\nTrigger keywords: desperdício, repetido, escopo, atalho, já pedi, otimizar tempo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido a analisar", "minLength": 1}
            },
            "required": ["pedido"]
        },
    },
]


def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-compreensao-pedidos", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)

    return None


def handle_tool(tool, args, rid):
    try:
        if tool == "compreender_pedido":
            pedido = args.get("pedido", "")
            result = cp.compreender(pedido)
        elif tool == "avaliar_clareza":
            pedido = args.get("pedido", "")
            ent = cp.compreender(pedido)
            result = {
                "tool": "avaliar_clareza",
                "score_entendimento": ent["score_entendimento"],
                "julgamento": ent["julgamento"],
                "ambiguidades": ent["ambiguidades"],
                "acoes_detectadas": len(ent["acoes"]),
            }
        elif tool == "refinar_entendimento":
            pedido = args.get("pedido", "")
            result = cp.compreender(pedido, refinar=True)
            result["tool"] = "refinar_entendimento"
        elif tool == "resolver_conceitos":
            conceitos = list(args.get("conceitos") or [])
            if not conceitos and args.get("pedido"):
                conceitos = cp._extrair_conceitos(args.get("pedido", ""))
            result = {"tool": "resolver_conceitos", "resolucoes": cp.resolver_conceitos(conceitos)}
        elif tool == "detectar_desperdicio":
            pedido = args.get("pedido", "")
            result = cp.detectar_desperdicio(pedido)
            result["tool"] = "detectar_desperdicio"
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"erro": str(e)}, ensure_ascii=False, indent=2)}]}}

    return {"jsonrpc": "2.0", "id": rid, "result": {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


def _read_frame(stream):
    """Lê UMA mensagem JSON-RPC de um stream stdio.

    Suporta os dois protocolos do ecossistema:
      - Framing MCP oficial (Content-Length: <n>\\r\\n\\r\\n<body>) — usado pelo opencode.
      - JSON por linha (sem header) — usado por preflight_check.py e servidores legados.
    """
    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if first.startswith(b"Content-Length:"):
        headers = {}
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
    else:
        # protocolo por linha: a linha lida já é o JSON
        body = first
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(b"Content-Length: " + str(len(data)).encode("ascii") + b"\r\n\r\n" + data)
    stream.flush()


if __name__ == "__main__":
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = _read_frame(stdin)
        if req is None:
            break
        resp = handle(req)
        if resp is not None:
            _write_frame(stdout, resp)
