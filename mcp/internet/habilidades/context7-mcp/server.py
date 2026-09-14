#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Context7 MCP Server — Documentação de bibliotecas atualizada injetada no contexto.
Wrapper Python para Context7 (https://github.com/upstash/context7-mcp).
Em produção, substituir por implementação nativa Python ou cliente HTTP para API Context7.
"""

import json
import sys
import os
from typing import Dict, Any, List

# MCP stdlib server pattern
class Context7MCP:
    def __init__(self):
        self.name = "context7"
        self.version = "1.0.0"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "resolve_library_id",
                "description": "Resolve o ID da biblioteca no Context7 a partir do nome",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "library_name": {"type": "string", "description": "Nome da biblioteca (ex: 'react', 'fastapi', 'pydantic')"}
                    },
                    "required": ["library_name"]
                }
            },
            {
                "name": "get_library_docs",
                "description": "Obtém documentação atualizada da biblioteca versão-específica",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "context7_library_id": {"type": "string", "description": "ID Context7 resolvido"},
                        "topic": {"type": "string", "description": "Tópico específico (opcional)"},
                        "tokens": {"type": "integer", "description": "Limite de tokens", "default": 8000}
                    },
                    "required": ["context7_library_id"]
                }
            }
        ]
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version}
            }
        elif method == "tools/list":
            return {"tools": self.get_tools()}
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            return self._call_tool(tool_name, args)
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}
    
    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar chamadas reais para API Context7 via HTTP
        # Por enquanto retorna stub indicando que precisa implementação
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"[STUB] Context7 tool '{name}' chamado com args: {json.dumps(args, ensure_ascii=False)}.\nImplementar chamadas HTTP para https://api.context7.com"
                }
            ],
            "isError": True
        }

def main():
    server = Context7MCP()
    # STDIN/STDOUT JSON-RPC loop
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response), flush=True)
        except Exception as e:
            print(json.dumps({"error": {"code": -32603, "message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()