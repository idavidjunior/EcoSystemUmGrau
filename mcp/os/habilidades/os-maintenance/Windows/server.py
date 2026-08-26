#!/usr/bin/env python3
"""
MCP Server para Windows Native Maintenance
Expõe ferramentas de manutenção nativa do Windows via MCP.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from windows_maintenance import (
    WindowsMaintenance,
    AdminRequired,
)

# MCP Server implementation
class WindowsMaintenanceMCP:
    def __init__(self):
        self.wm = WindowsMaintenance()

    async def health_check(self) -> Dict[str, Any]:
        """Health check completo não invasivo."""
        report = self.wm.full_health_check()
        return {
            "status": report.overall_status,
            "timestamp": report.timestamp,
            "recommendations": report.recommendations,
            "errors": report.errors,
            "checks": report.checks
        }

    async def disk_analyze(self, drive: str = "C:") -> Dict[str, Any]:
        """Analisa volume (chkdsk /scan)."""
        return self.wm.disk.analyze_volume(drive)

    async def disk_repair(self, drive: str = "C:", offline: bool = False) -> Dict[str, Any]:
        """Repara volume. Requer Admin."""
        try:
            return self.wm.disk.repair_volume(drive, offline=offline)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def disk_optimize(self, drive: str = "C:", operation: str = "Optimize") -> Dict[str, Any]:
        """Otimiza volume."""
        return self.wm.disk.optimize_volume(drive, operation)

    async def disk_health(self) -> Dict[str, Any]:
        """Relatório Storage Health (SMART)."""
        return self.wm.disk.get_storage_health()

    async def system_sfc(self) -> Dict[str, Any]:
        """Executa sfc /scannow. Requer Admin."""
        try:
            return self.wm.system.run_sfc()
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def system_dism_restore(self) -> Dict[str, Any]:
        """DISM RestoreHealth. Requer Admin."""
        try:
            return self.wm.system.run_dism_restore_health()
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def system_dism_cleanup(self) -> Dict[str, Any]:
        """DISM Component Cleanup. Requer Admin."""
        try:
            return self.wm.system.run_dism_component_cleanup()
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def logs_export_errors(self, days: int = 7, logs: List[str] = None) -> Dict[str, Any]:
        """Exporta erros dos logs de eventos."""
        return self.wm.logs.export_errors(days=days, logs=logs)

    async def boot_backup_bcd(self) -> Dict[str, Any]:
        """Backup do BCD. Requer Admin."""
        try:
            return self.wm.boot.backup_bcd()
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def boot_enum_bcd(self, verbose: bool = False) -> Dict[str, Any]:
        """Lista entradas BCD."""
        return self.wm.boot.enum_bcd(verbose=verbose)

    async def update_get_log(self) -> Dict[str, Any]:
        """Gera log Windows Update."""
        return self.wm.update.get_update_log()

    async def update_scan(self) -> Dict[str, Any]:
        """USOClient StartScan."""
        return self.wm.update.uso_client_scan()

    async def drivers_problems(self) -> Dict[str, Any]:
        """Dispositivos com problema."""
        return self.wm.drivers.find_problem_drivers()

    async def services_list(self, name_filter: str = None, status: str = None) -> Dict[str, Any]:
        """Lista serviços."""
        return self.wm.services.list_services(name_filter=name_filter, status=status)

    async def network_test(self, target: str, port: int = None) -> Dict[str, Any]:
        """Testa conectividade."""
        return self.wm.network.test_connection(target, port)

    async def winfr_recover(self, source: str, dest: str, mode: str = "regular", filters: List[str] = None, file_types: List[str] = None) -> Dict[str, Any]:
        """Windows File Recovery."""
        try:
            return self.wm.disk.winfr_recover(source, dest, mode, filters, file_types)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def winfr_check(self) -> Dict[str, Any]:
        """Verifica se winfr está instalado."""
        return self.wm.disk.winfr_check_installed()


# MCP Protocol handlers
mcp = WindowsMaintenanceMCP()

TOOLS = {
    "win_health_check": {
        "description": "Health check completo do Windows (não invasivo, sem Admin)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.health_check
    },
    "win_disk_analyze": {
        "description": "Analisa volume com chkdsk /scan (online, read-only)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drive": {"type": "string", "description": "Drive letter (ex: C:)", "default": "C:"}
            }
        },
        "handler": mcp.disk_analyze
    },
    "win_disk_repair": {
        "description": "Repara volume (chkdsk /f /r ou Repair-Volume). Requer Admin.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drive": {"type": "string", "description": "Drive letter", "default": "C:"},
                "offline": {"type": "boolean", "description": "Reparo offline (requer reinicialização para C:)", "default": False}
            }
        },
        "handler": mcp.disk_repair
    },
    "win_disk_optimize": {
        "description": "Otimiza volume (defrag/trim/retim/tier).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drive": {"type": "string", "description": "Drive letter", "default": "C:"},
                "operation": {"type": "string", "enum": ["Analyze", "Defrag", "Retrim", "TierOptimize", "BootOptimize", "SlabConsolidate", "FreespaceConsolidate", "Optimize"], "default": "Optimize"}
            }
        },
        "handler": mcp.disk_optimize
    },
    "win_disk_health": {
        "description": "Relatório de saúde de armazenamento (SMART/NVMe via PowerShell Storage)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.disk_health
    },
    "win_system_sfc": {
        "description": "System File Checker (sfc /scannow). Requer Admin.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.system_sfc
    },
    "win_system_dism_restore": {
        "description": "DISM RestoreHealth (repara component store). Requer Admin.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.system_dism_restore
    },
    "win_system_dism_cleanup": {
        "description": "DISM Component Store Cleanup. Requer Admin.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.system_dism_cleanup
    },
    "win_logs_export_errors": {
        "description": "Exporta erros dos logs System/Application dos últimos N dias",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 7},
                "logs": {"type": "array", "items": {"type": "string"}, "default": ["System", "Application"]}
            }
        },
        "handler": mcp.logs_export_errors
    },
    "win_boot_backup_bcd": {
        "description": "Backup do BCD (Boot Configuration Data). Requer Admin.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.boot_backup_bcd
    },
    "win_boot_enum_bcd": {
        "description": "Lista entradas do BCD",
        "inputSchema": {
            "type": "object",
            "properties": {
                "verbose": {"type": "boolean", "default": False}
            }
        },
        "handler": mcp.boot_enum_bcd
    },
    "win_update_get_log": {
        "description": "Gera log legível do Windows Update",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.update_get_log
    },
    "win_update_scan": {
        "description": "Força scan de updates (USOClient)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.update_scan
    },
    "win_drivers_problems": {
        "description": "Lista dispositivos com problema (Error/Unknown/Degraded)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.drivers_problems
    },
    "win_services_list": {
        "description": "Lista serviços do Windows",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_filter": {"type": "string"},
                "status": {"type": "string", "enum": ["Running", "Stopped", "Paused"]}
            }
        },
        "handler": mcp.services_list
    },
    "win_network_test": {
        "description": "Testa conectividade de rede (Test-NetConnection)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Host ou IP"},
                "port": {"type": "integer", "description": "Porta TCP opcional"}
            },
            "required": ["target"]
        },
        "handler": mcp.network_test
    },
    "win_winfr_recover": {
        "description": "Windows File Recovery - recupera arquivos deletados (requer Admin + winfr instalado via Microsoft Store)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Drive origem (ex: C:)"},
                "dest": {"type": "string", "description": "Drive destino (ex: D:)"},
                "mode": {"type": "string", "enum": ["regular", "extensive", "segment"], "default": "regular"},
                "filters": {"type": "array", "items": {"type": "string"}, "description": "Filtros de arquivo (ex: *.docx, *.pdf)"},
                "file_types": {"type": "array", "items": {"type": "string"}, "description": "Tipos: doc, pic, vid, aud, zip, etc."}
            },
            "required": ["source", "dest"]
        },
        "handler": mcp.winfr_recover
    },
    "win_winfr_check": {
        "description": "Verifica se winfr (Windows File Recovery) está instalado",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.winfr_check
    },
}


async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Processa requisição MCP."""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
                    for name, spec in TOOLS.items()
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
            }

        try:
            handler = TOOLS[tool_name]["handler"]
            result = await handler(**arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Tool execution error: {str(e)}"}
            }

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "windows-maintenance", "version": "1.0.0"}
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }


async def main():
    """Main loop para stdio transport."""
    print("Windows Maintenance MCP Server started", file=sys.stderr)
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = await handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Server error: {str(e)}"}
            }), flush=True)


if __name__ == "__main__":
    asyncio.run(main())