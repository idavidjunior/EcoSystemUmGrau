#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Client Real — Cliente stdio JSON-RPC para servidores MCP.

Substitui simulações por chamadas MCP reais via stdio JSON-RPC.
"""

import json
import subprocess
import sys
import os
import time
from typing import Any, Dict, Optional, List
from pathlib import Path
from threading import Lock
from datetime import datetime


class MCPClient:
    """Cliente MCP stdio JSON-RPC para servidores MCP locais."""
    
    def __init__(self, server_path: str, server_name: str = "mcp-server"):
        self.server_path = server_path
        self.server_name = server_name
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self._lock = Lock()
        self._initialized = False
        self._tools_cache: Optional[List[Dict]] = None
    
    def _next_id(self) -> int:
        with self._lock:
            self.request_id += 1
            return self.request_id
    
    def start(self) -> bool:
        """Inicia o processo do servidor MCP."""
        if self.process and self.process.poll() is None:
            return True  # já rodando
        
        try:
            # Garante que o script tem permissão de execução
            server_script = Path(self.server_path)
            if not server_script.exists():
                raise FileNotFoundError(f"Servidor MCP não encontrado: {self.server_path}")
            
            # Inicia processo com stdio pipes
            self.process = subprocess.Popen(
                [sys.executable, str(server_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,  # line buffered
            )
            
            # Aguarda inicialização
            time.sleep(0.5)
            
            # Verifica se processo ainda vivo
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                raise RuntimeError(f"Processo MCP morreu na inicialização: {stderr}")
            
            # Inicializa protocolo MCP
            self._initialize()
            return True
            
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Falha ao iniciar MCP {self.server_name}: {e}")
    
    def _initialize(self) -> bool:
        """Inicializa protocolo MCP (initialize + initialized)."""
        # initialize
        resp = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ecosystem-client", "version": "1.0.0"}
        })
        if "error" in resp:
            raise RuntimeError(f"Falha no initialize: {resp['error']}")
        
        # notifications/initialized
        self._send_notification("notifications/initialized", {})
        
        self._initialized = True
        return True
    
    def _send_request(self, method: str, params: Dict = None) -> Dict:
        """Envia request JSON-RPC e aguarda response."""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Processo MCP não está rodando")
        
        req_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        
        request_line = json.dumps(request) + "\n"
        
        try:
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Pipe quebrado - processo MCP morreu")
        
        # Lê response (pode vir em múltiplas linhas)
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("Sem resposta do servidor MCP")
        
        try:
            response = json.loads(response_line.strip())
        except json.JSONDecodeError as e:
            # Tenta ler mais linhas se JSON incompleto
            extra = self.process.stdout.readline()
            try:
                response = json.loads((response_line + extra).strip())
            except json.JSONDecodeError:
                raise RuntimeError(f"Resposta JSON inválida do MCP: {response_line[:200]}")
        
        if "error" in response:
            return {"error": response["error"]}
        return response.get("result", {})
    
    def _send_notification(self, method: str, params: Dict = None):
        """Envia notification (sem aguardar response)."""
        if not self.process or self.process.poll() is not None:
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        try:
            self.process.stdin.write(json.dumps(notification) + "\n")
            self.process.stdin.flush()
        except BrokenPipeError:
            pass
    
    def list_tools(self) -> List[Dict]:
        """Lista ferramentas disponíveis (skills)."""
        if not self._initialized:
            self.start()
        
        if self._tools_cache is not None:
            return self._tools_cache
        
        result = self._send_request("tools/list")
        if "error" in result:
            raise RuntimeError(f"Erro listando tools: {result['error']}")
        
        self._tools_cache = result.get("tools", [])
        return self._tools_cache
    
    def call_skill(self, skill_name: str, arguments: str = "") -> Dict:
        """Chama uma skill via MCP tool call.
        
        Args:
            skill_name: Nome da skill (ex: 'pensador-critico', 'conservador', 'code-reviewer')
            arguments: String com argumentos para a skill
            
        Returns:
            Dict com resultado da skill
        """
        if not self._initialized:
            self.start()
        
        tool_name = f"skill-{skill_name}"
        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": {"argumentos": arguments}
        })
        
        if "error" in result:
            raise RuntimeError(f"Erro chamando skill {skill_name}: {result['error']}")
        
        # O servidor MCP retorna content como lista de objetos text
        content = result.get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "") if content else ""
            return {"text": text, "raw": result}
        
        return {"text": str(result), "raw": result}
    
    def stop(self):
        """Para o processo MCP."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process = None
        self._initialized = False
        self._tools_cache = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
    
    def __del__(self):
        self.stop()


class MCPClientPool:
    """Pool de clientes MCP para reuso de conexões."""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._lock = Lock()
    
    def get_client(self, domain: str) -> MCPClient:
        """Obtém ou cria cliente para domínio."""
        with self._lock:
            if domain not in self._clients:
                # BASE é a raiz do projeto (onde está o mcp/)
                base = Path(__file__).resolve().parent.parent
                server_path = base / "mcp" / domain / "server.py"
                self._clients[domain] = MCPClient(str(server_path), f"mcp-{domain}")
            return self._clients[domain]
    
    def call_skill(self, domain: str, skill_name: str, arguments: str = "") -> Dict:
        """Chama skill em domínio específico."""
        client = self.get_client(domain)
        return client.call_skill(skill_name, arguments)
    
    def stop_all(self):
        for client in self._clients.values():
            client.stop()
        self._clients.clear()


# Instância global do pool
MCP_POOL = MCPClientPool()


# Mapeamento de Conselheiro -> (domínio, skill_name)
CONSELHEIRO_SKILL_MAP = {
    "cetico.analise-riscos": ("comportamentais", "pensador-critico"),
    "etica.conformidade": ("comportamentais", "conservador"),
    "revisor.qualidade": ("comportamentais", "code-reviewer"),
    # Fase 2 - skills podem não existir ainda, placeholder
    "estrategista.direcao-estrategica": ("comportamentais", "pensador-critico"),  # placeholder
    "realista.viabilidade": ("comportamentais", "conservador"),  # placeholder
    "futuro.evolucao-tecnologica": ("comportamentais", "pensador-critico"),  # placeholder
    "recursos.reuso": ("comportamentais", "ponytail"),  # placeholder
    "criativo.inovacao": ("comportamentais", "pensador-critico"),  # placeholder
    "revisor.qualidade": ("comportamentais", "code-reviewer"),
}


def chamar_skill_conselheiro(seam_name: str, argumentos: str = "") -> Dict:
    """Função helper para chamar skill de um conselheiro via MCP real.
    
    Args:
        seam_name: Nome do seam (ex: 'cetico.analise-riscos')
        argumentos: String com argumentos para a skill
        
    Returns:
        Dict com resultado da skill ou fallback estruturado
    """
    if seam_name not in CONSELHEIRO_SKILL_MAP:
        return {
            "error": True,
            "seam": seam_name,
            "error_message": f"Seam não mapeado: {seam_name}",
            "fallback": True,
        }
    
    domain, skill_name = CONSELHEIRO_SKILL_MAP[seam_name]
    
    try:
        return MCP_POOL.call_skill(domain, skill_name, "")
    except Exception as e:
        # Fallback estruturado em caso de erro
        return {
            "error": True,
            "seam": seam_name,
            "error_message": str(e),
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 1:
        seam = sys.argv[1]
        args = sys.argv[2] if len(sys.argv) > 2 else ""
        result = chamar_skill_conselheiro(seam, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Lista skills disponíveis
        print("Mapeamentos de Conselheiro -> Skill:")
        for seam, (domain, skill) in CONSELHEIRO_SKILL_MAP.items():
            print(f"  {seam} -> {domain}/{skill}")