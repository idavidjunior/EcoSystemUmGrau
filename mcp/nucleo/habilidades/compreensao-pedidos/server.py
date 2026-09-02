"""MCP server — Compreensão de Pedidos.

Transforma pedidos do usuário em entendimento estruturado (objetivo, ações,
contexto, conceitos, restrições, ambiguidades, critérios, plano) e conecta ao
acervo do ecossistema (memória, skills, projetos, scripts). Sem DSPy; refino
com LLM é opcional e fail-soft (LLM do opencode como primária, NVIDIA/OpenAI/Anthropic de backup).

Transporte: MCP stdio padrão (Content-Length framing).

Tools:
  - compreender_pedido    — entendimento completo de um pedido
  - avaliar_clareza       — score de clareza estático + lacunas
  - refinar_entendimento  — compreensão + refino com a LLM do opencode (fallback NVIDIA/OpenAI/Anthropic)
  - resolver_conceitos    — resolve termos do pedido no acervo do ecossistema
  - detectar_desperdicio  — riscos de desperdício e atalhos (repetição, escopo)
  - veto_pedido           — checklist de entrega + gate de veto (APROVADO/BLOQUEADO) antes de executar
  - gerar_spec            — gera e salva a spec em specs/<slug>.spec.md
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
        "description": "Executa a compreensão completa e refina com a LLM do opencode (primária; se não responder, backup NVIDIA → OpenAI → Anthropic). Fail-soft: sem LLM disponível, retorna o entendimento estático com o motivo. Use para pedidos críticos/complexos.\n\nTrigger keywords: refinar entendimento, pedido crítico, validar interpretação, ambiguidade alta.",
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
    {
        "name": "veto_pedido",
        "description": "Gate consultável de entrega e veto (Fase 1): monta o checklist de 'pronto e finalizado' de um pedido e diz se ele está APROVADO ou BLOQUEADO, listando o que está proibido (vetos) dentro do escopo do ecossistema. Consulte ANTES de executar um pedido.\n\nTrigger keywords: veto, checklist, bloqueado, aprovado, gate de execução, posso executar, está proibido.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido a examinar antes de executar", "minLength": 1}
            },
            "required": ["pedido"]
        },
    },
    {
        "name": "gerar_spec",
        "description": "Gera e salva a spec (SDD) de um pedido em specs/<slug>.spec.md com escrita atômica. Usa o entendimento estruturado (objetivo, ações, critérios) e a heurística de componente (script:/skill:/projeto).\n\nTrigger keywords: gerar spec, spec, especificação, sdd, documentar requisito.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "O pedido/requisito a transformar em spec", "minLength": 1},
                "destino": {"type": "string", "description": "Opcional: caminho de destino; padrão specs/<slug>.spec.md"}
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
        elif tool == "veto_pedido":
            pedido = args.get("pedido", "")
            result = cp.gerar_checklist(pedido)
            result["tool"] = "veto_pedido"
        elif tool == "gerar_spec":
            pedido = args.get("pedido", "")
            destino = args.get("destino")
            ent = cp.compreender(pedido)
            if destino:
                result = cp.salvar_spec(pedido, destino=destino, entendimento=ent)
            else:
                result = cp.salvar_spec(pedido, entendimento=ent)
            result["tool"] = "gerar_spec"
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
    # Peek first byte to detect protocol
    peek = stream.peek(1)
    if not peek:
        return None

    # If starts with '{', it's line-delimited JSON (most common in this ecosystem)
    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # Otherwise, try Content-Length framing
    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        # Not a recognized protocol
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
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
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
