"""
ProviderManager MCP Server — Exposes LLM provider + server management to OpenCode via MCP.

This allows OpenCode to:
- Send completion requests through the ProviderManager (with auto-failover)
- Query provider status (/provider-status)
- Get model lists per provider
- Receive automatic failover when a provider errors
- Manage multiple OpenCode server instances (primary+secondary)
- Automatic server failover when the primary server goes down
- Automatic return to primary when it recovers

Protocol: JSON-RPC 2.0 over stdin/stdout (MCP standard transport)
"""

import sys
import os
import json
import traceback
import atexit
import threading
import time
from datetime import datetime

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from provider_manager import ProviderManager
from provider_manager.models import CompletionRequest
from provider_manager.status import generate_status, status_as_dict
from provider_manager.server_manager import ServerManager


class ProviderMCPServer:
    """MCP server exposing ProviderManager + ServerManager to OpenCode."""

    def __init__(self):
        self.pm = ProviderManager(BASE_DIR)
        self.pm.initialize()

        # ServerManager — gerencia multiplas instancias OpenCode
        self.sm = ServerManager()
        self.sm.initialize()

        self.request_id = 0

    def handle_request(self, request: dict):
        """Process a JSON-RPC 2.0 request.
        Returns a response dict, or None for notifications (no id).
        """
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        # Notifications (no id) must not receive a response
        if req_id is None:
            # Silently accept initialized notification
            return None

        try:
            # ── MCP Protocol ──
            if method == "initialize":
                return self._handle_initialize(params, req_id)
            elif method in ("tools/list", "mcp.tools.list"):
                return self._handle_tools_list(params, req_id)
            elif method == "tools/call":
                return self._handle_tools_call(params, req_id)

            # ── Provider (LLM) ──
            elif method == "complete":
                return self._handle_complete(params, req_id)
            elif method == "provider_status":
                return self._handle_status(params, req_id)
            elif method == "provider_status_json":
                return self._handle_status_json(params, req_id)
            elif method == "list_models":
                return self._handle_list_models(params, req_id)
            elif method == "check_health":
                return self._handle_check_health(params, req_id)
            elif method == "set_priority":
                return self._handle_set_priority(params, req_id)
            elif method == "get_stats":
                return self._handle_get_stats(params, req_id)

            # ── Server (OpenCode instances) ──
            elif method == "server_status":
                return self._handle_server_status(params, req_id)
            elif method == "server_status_json":
                return self._handle_server_status_json(params, req_id)
            elif method == "server_start":
                return self._handle_server_start(params, req_id)
            elif method == "server_stop":
                return self._handle_server_stop(params, req_id)
            elif method == "server_failover_test":
                return self._handle_server_failover_test(params, req_id)
            elif method == "server_set_primary":
                return self._handle_server_set_primary(params, req_id)

            # ── Utility ──
            elif method == "ping":
                return self._make_response(req_id, {"status": "pong", "provider_manager": True})
            else:
                return self._make_error(req_id, -32601, f"Method not found: {method}")
        except Exception as e:
            return self._make_error(req_id, -32603, f"Internal error: {e}\n{traceback.format_exc()}")

    def _handle_initialize(self, params, req_id):
        """MCP initialize handshake — required by OpenCode v1.17+."""
        proto_version = params.get("protocolVersion", "2024-11-05")
        return self._make_response(req_id, {
            "protocolVersion": proto_version,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "experimental": {}
            },
            "serverInfo": {
                "name": "provider-manager",
                "version": "1.0.0"
            }
        })

    def _handle_tools_list(self, params, req_id):
        """MCP tools/list — expose ProviderManager + ServerManager operations."""
        tools = [
            # ── Provider (LLM) Tools ──
            {
                "name": "provider-complete",
                "description": "Send a completion request to the active LLM provider with automatic failover",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            },
                            "description": "Chat messages"
                        },
                        "model": {"type": "string", "description": "Optional model override"},
                        "provider": {"type": "string", "description": "Optional provider override"},
                        "temperature": {"type": "number", "description": "Optional (default 0.7)"},
                        "max_tokens": {"type": "integer", "description": "Optional (default 4096)"}
                    }
                }
            },
            {
                "name": "provider-status",
                "description": "Get provider status as formatted text",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "provider-status-json",
                "description": "Get provider status as structured JSON",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "provider-check-health",
                "description": "Run health checks against all providers or a specific one",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "description": "Optional specific provider name"}
                    }
                }
            },
            {
                "name": "provider-list-models",
                "description": "List available models from all providers or a specific one",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "description": "Optional specific provider name"}
                    }
                }
            },
            # ── Server (OpenCode instances) Tools ──
            {
                "name": "server-status",
                "description": "Get server failover status as formatted text",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "server-status-json",
                "description": "Get server failover status as structured JSON",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "server-start",
                "description": "Start a specific server instance (e.g., 'secondary')",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Server name: 'primary' or 'secondary'"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "server-stop",
                "description": "Stop a specific server instance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Server name to stop"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "server-failover-test",
                "description": "Simulate primary server failure to test failover to secondary",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "server-set-primary",
                "description": "Manually set which server is primary for auto-return",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Server name to set as primary"}
                    },
                    "required": ["name"]
                }
            }
        ]
        return self._make_response(req_id, {"tools": tools})

    def _handle_tools_call(self, params, req_id):
        """MCP tools/call — route tool name to the appropriate handler."""
        name = params.get("name", "")
        args = params.get("arguments", {})

        mapping = {
            "provider-complete": self._handle_complete,
            "provider-status": self._handle_status,
            "provider-status-json": self._handle_status_json,
            "provider-check-health": self._handle_check_health,
            "provider-list-models": self._handle_list_models,
            "server-status": self._handle_server_status,
            "server-status-json": self._handle_server_status_json,
            "server-start": self._handle_server_start,
            "server-stop": self._handle_server_stop,
            "server-failover-test": self._handle_server_failover_test,
            "server-set-primary": self._handle_server_set_primary,
            "set_priority": self._handle_set_priority,
            "get_stats": self._handle_get_stats,
        }

        handler = mapping.get(name)
        if handler is None:
            return self._make_error(req_id, -32601, f"Unknown tool: {name}")
        return handler(args, req_id)

    def _handle_complete(self, params, req_id):
        """Send a completion request with automatic failover.

        Params:
            messages: list of {"role": "...", "content": "..."}
            model: optional model override
            provider: optional provider override
            temperature: optional (default 0.7)
            max_tokens: optional (default 4096)
        """
        messages = params.get("messages", [])
        if not messages:
            return self._make_error(req_id, -32602, "messages required")

        request = CompletionRequest(
            messages=messages,
            model=params.get("model"),
            provider=params.get("provider"),
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 4096),
            stream=params.get("stream", False),
        )
        response = self.pm.complete(request)
        return self._make_response(req_id, {
            "success": response.success,
            "provider": response.provider,
            "model": response.model,
            "content": response.content,
            "error": response.error,
            "error_type": response.error_type,
            "latency_ms": response.latency_ms,
            "token_count_input": response.token_count_input,
            "token_count_output": response.token_count_output,
        })

    def _handle_status(self, params, req_id):
        """Return /provider-status as formatted text."""
        output = generate_status(self.pm)
        return self._make_response(req_id, {"status_text": output})

    def _handle_status_json(self, params, req_id):
        """Return provider status as structured JSON."""
        status = status_as_dict(self.pm)
        return self._make_response(req_id, status)

    def _handle_list_models(self, params, req_id):
        """List available models from all providers or a specific one."""
        provider = params.get("provider")
        models = self.pm.get_models(provider)
        result = {}
        for prov, model_list in models.items():
            result[prov] = [
                {"id": m.id, "context_window": m.context_window,
                 "supports_vision": m.supports_vision,
                 "supports_tools": m.supports_tools}
                for m in model_list
            ]
        return self._make_response(req_id, {"models": result})

    def _handle_check_health(self, params, req_id):
        """Run health checks against all providers or a specific one."""
        provider = params.get("provider")
        if provider:
            health = self.pm.check_provider_health(provider)
            return self._make_response(req_id, {
                provider: {"online": health.online, "latency_ms": health.latency_ms,
                          "error": health.error}
            })
        results = self.pm.check_all_health()
        serialized = {}
        for prov, health in results.items():
            serialized[prov] = {"online": health.online, "latency_ms": health.latency_ms,
                               "error": health.error}
        return self._make_response(req_id, serialized)

    def _handle_set_priority(self, params, req_id):
        """Update provider priority order at runtime."""
        priority = params.get("priority", [])
        if not priority:
            return self._make_error(req_id, -32602, "priority list required")
        self.pm.set_priority(priority)
        return self._make_response(req_id, {
            "success": True,
            "active_provider": self.pm.get_active_provider_name(),
            "priority": self.pm.get_priority_order(),
        })

    def _handle_get_stats(self, params, req_id):
        """Return usage statistics for all providers."""
        return self._make_response(req_id, {"stats": self.pm.get_stats()})

    # ─── Server Management Handlers ─────────────────────────────────

    def _handle_server_status(self, params, req_id):
        return self._make_response(req_id, {"status_text": self.sm.summary_text()})

    def _handle_server_status_json(self, params, req_id):
        return self._make_response(req_id, self.sm.summary())

    def _handle_server_start(self, params, req_id):
        name = params.get("name", "")
        if not name:
            return self._make_error(req_id, -32602, "server name required")
        success = self.sm.start_server(name)
        return self._make_response(req_id, {
            "success": success,
            "server": name,
            "status": self.sm.summary(),
        })

    def _handle_server_stop(self, params, req_id):
        name = params.get("name", "")
        if not name:
            return self._make_error(req_id, -32602, "server name required")
        success = self.sm.stop_server(name)
        return self._make_response(req_id, {
            "success": success,
            "status": self.sm.summary(),
        })

    def _handle_server_failover_test(self, params, req_id):
        """Simulate primary failure to validate server failover works."""
        results = {}
        primary = self.sm.get_server("primary")
        if primary and primary.status != "down":
            results["simulated"] = self.sm.stop_server("primary")
        results["status"] = self.sm.summary()
        results["health"] = self.sm.check_all_health()
        return self._make_response(req_id, results)

    def _handle_server_set_primary(self, params, req_id):
        name = params.get("name", "")
        if not name:
            return self._make_error(req_id, -32602, "server name required")
        self.sm._primary_name = name
        return self._make_response(req_id, {
            "success": True,
            "primary": name,
            "status": self.sm.summary(),
        })

    def _make_response(self, req_id, result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _make_error(self, req_id, code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _log(self, msg):
        """Write diagnostic message to stderr for visibility in parent process logs."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[MCP {ts}] {msg}\n")
        sys.stderr.flush()

    def _heartbeat_loop(self):
        """Log alive signal to stderr every 60s so parent can detect hang."""
        while True:
            time.sleep(60)
            self._log("heartbeat OK")

    def run(self):
        """Read JSON-RPC requests from stdin, write responses to stdout."""
        pid = os.getpid()
        self._log(f"started PID={pid}")

        # Heartbeat thread (daemon = dies with main thread)
        hb = threading.Thread(target=self._heartbeat_loop, daemon=True)
        hb.start()

        # Register shutdown hook
        def _on_exit():
            self._log(f"shutdown PID={pid}")
        atexit.register(_on_exit)

        request_count = 0
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                request_count += 1
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    if response is not None:
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()
                except json.JSONDecodeError:
                    error = self._make_error(None, -32700, "Parse error")
                    sys.stdout.write(json.dumps(error) + "\n")
                    sys.stdout.flush()
                except Exception:
                    error = self._make_error(None, -32603, traceback.format_exc())
                    sys.stdout.write(json.dumps(error) + "\n")
                    sys.stdout.flush()
        except Exception:
            self._log(f"FATAL: {traceback.format_exc()}")
            raise


if __name__ == "__main__":
    server = ProviderMCPServer()
    server.run()
