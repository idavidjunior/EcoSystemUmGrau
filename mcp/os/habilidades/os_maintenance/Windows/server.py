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

    # Cache Tiering handlers
    async def cache_list_pools(self) -> Dict[str, Any]:
        return self.wm.cache.list_pools()

    async def cache_list_tiers(self, pool_name: str) -> Dict[str, Any]:
        return self.wm.cache.list_tiers(pool_name)

    async def cache_create_pool(self, pool_name: str, physical_disks: List[str], resiliency: str = "Simple") -> Dict[str, Any]:
        try:
            return self.wm.cache.create_pool_with_tiers(pool_name, physical_disks, resiliency=resiliency)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_create_vdisk(self, pool_name: str, vdisk_name: str, size: str,
                                  ssd_tier_size: str = None, hdd_tier_size: str = None,
                                  resiliency: str = "Simple", write_cache: str = "On") -> Dict[str, Any]:
        try:
            return self.wm.cache.create_tiered_virtual_disk(pool_name, vdisk_name, size,
                                                              ssd_tier_size, hdd_tier_size, resiliency, write_cache)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_set_write_cache(self, vdisk_name: str, policy: str = "On") -> Dict[str, Any]:
        try:
            return self.wm.cache.set_write_cache_policy(vdisk_name, policy)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_optimize(self, pool_name: str = None, vdisk_name: str = None) -> Dict[str, Any]:
        try:
            return self.wm.cache.optimize_tier(pool_name, vdisk_name)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_metrics(self, vdisk_name: str = None) -> Dict[str, Any]:
        return self.wm.cache.get_tier_metrics(vdisk_name)

    async def cache_enable_writeback(self, physical_disk: str) -> Dict[str, Any]:
        try:
            return self.wm.cache.enable_write_back_cache(physical_disk)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_ramdisk(self, size_gb: int, drive_letter: str = "R:") -> Dict[str, Any]:
        try:
            return self.wm.cache.create_ram_disk(size_gb, drive_letter)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_remove_ramdisk(self, drive_letter: str = "R:") -> Dict[str, Any]:
        try:
            return self.wm.cache.remove_ram_disk(drive_letter)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}

    async def cache_warm(self, paths: List[str], priority: str = "Normal") -> Dict[str, Any]:
        return self.wm.cache.warm_cache(paths, priority)

    async def cache_superfetch_status(self) -> Dict[str, Any]:
        return self.wm.cache.get_superfetch_status()

    async def cache_set_superfetch(self, enable_prefetch: int, enable_superfetch: int) -> Dict[str, Any]:
        try:
            return self.wm.cache.set_superfetch(enable_prefetch, enable_superfetch)
        except AdminRequired as e:
            return {"error": str(e), "requires_admin": True}


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
    "win_cache_list_pools": {
        "description": "Lista Storage Pools com tiers",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.cache_list_pools
    },
    "win_cache_list_tiers": {
        "description": "Lista tiers de um Storage Pool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pool_name": {"type": "string", "description": "Nome do pool"}
            },
            "required": ["pool_name"]
        },
        "handler": mcp.cache_list_tiers
    },
    "win_cache_create_pool": {
        "description": "Cria Storage Pool com tiers SSD+HDD (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pool_name": {"type": "string", "description": "Nome do pool"},
                "physical_disks": {"type": "array", "items": {"type": "string"}, "description": "Lista de discos físicos"},
                "resiliency": {"type": "string", "enum": ["Simple", "Mirror", "Parity"], "default": "Simple"}
            },
            "required": ["pool_name", "physical_disks"]
        },
        "handler": mcp.cache_create_pool
    },
    "win_cache_create_vdisk": {
        "description": "Cria Virtual Disk tiered no pool (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pool_name": {"type": "string", "description": "Nome do pool"},
                "vdisk_name": {"type": "string", "description": "Nome do Virtual Disk"},
                "size": {"type": "string", "description": "Tamanho (ex: 500GB)"},
                "ssd_tier_size": {"type": "string", "description": "Tamanho tier SSD"},
                "hdd_tier_size": {"type": "string", "description": "Tamanho tier HDD"},
                "resiliency": {"type": "string", "enum": ["Simple", "Mirror", "Parity"], "default": "Simple"},
                "write_cache": {"type": "string", "enum": ["On", "Off", "Auto"], "default": "On"}
            },
            "required": ["pool_name", "vdisk_name", "size"]
        },
        "handler": mcp.cache_create_vdisk
    },
    "win_cache_set_write_cache": {
        "description": "Define política write cache do Virtual Disk (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vdisk_name": {"type": "string", "description": "Nome do Virtual Disk"},
                "policy": {"type": "string", "enum": ["On", "Off", "Auto"], "default": "On"}
            },
            "required": ["vdisk_name"]
        },
        "handler": mcp.cache_set_write_cache
    },
    "win_cache_optimize": {
        "description": "Otimiza placement de dados entre tiers (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pool_name": {"type": "string", "description": "Nome do pool (opcional)"},
                "vdisk_name": {"type": "string", "description": "Nome do VDisk (opcional)"}
            }
        },
        "handler": mcp.cache_optimize
    },
    "win_cache_metrics": {
        "description": "Métricas de uso dos tiers (hit ratio, espaço, utilização)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vdisk_name": {"type": "string", "description": "Nome do VDisk (opcional)"}
            }
        },
        "handler": mcp.cache_metrics
    },
    "win_cache_enable_writeback": {
        "description": "Habilita write-back cache no disco físico (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "physical_disk": {"type": "string", "description": "Nome do disco físico"}
            },
            "required": ["physical_disk"]
        },
        "handler": mcp.cache_enable_writeback
    },
    "win_cache_ramdisk": {
        "description": "Cria RAM Disk via ImDisk (requer Admin + ImDisk instalado)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "size_gb": {"type": "integer", "description": "Tamanho em GB"},
                "drive_letter": {"type": "string", "description": "Letra da unidade", "default": "R:"}
            },
            "required": ["size_gb"]
        },
        "handler": mcp.cache_ramdisk
    },
    "win_cache_remove_ramdisk": {
        "description": "Remove RAM Disk (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drive_letter": {"type": "string", "description": "Letra da unidade", "default": "R:"}
            },
            "required": ["drive_letter"]
        },
        "handler": mcp.cache_remove_ramdisk
    },
    "win_cache_warm": {
        "description": "Pré-carrega arquivos no cache do sistema (Standby list)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "items": {"type": "string"}, "description": "Paths para aquecer"},
                "priority": {"type": "string", "enum": ["Low", "Normal", "High"], "default": "Normal"}
            },
            "required": ["paths"]
        },
        "handler": mcp.cache_warm
    },
    "win_cache_superfetch_status": {
        "description": "Status do SysMain (Superfetch/Prefetcher)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.cache_superfetch_status
    },
    "win_cache_set_superfetch": {
        "description": "Configura Prefetcher/Superfetch (requer Admin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enable_prefetch": {"type": "integer", "description": "0=Off, 1=App, 2=Boot, 3=Both", "minimum": 0, "maximum": 3, "default": 3},
                "enable_superfetch": {"type": "integer", "description": "0=Off, 1=App, 2=Boot, 3=Both", "minimum": 0, "maximum": 3, "default": 3}
            },
            "required": ["enable_prefetch", "enable_superfetch"]
        },
        "handler": mcp.cache_set_superfetch
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