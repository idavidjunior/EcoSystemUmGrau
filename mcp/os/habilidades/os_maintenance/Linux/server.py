#!/usr/bin/env python3
"""
MCP Server para Linux Native Maintenance
Expõe ferramentas de manutenção nativa do Linux via MCP.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linux_maintenance import (
    LinuxMaintenance,
    RootRequired,
    ToolNotFound,
    DistroNotSupported,
)

# MCP Server implementation
class LinuxMaintenanceMCP:
    def __init__(self):
        self.lm = LinuxMaintenance()

    async def health_check(self) -> Dict[str, Any]:
        """Health check completo não invasivo."""
        report = self.lm.full_health_check()
        return {
            "status": report.overall_status,
            "timestamp": report.timestamp,
            "recommendations": report.recommendations,
            "errors": report.errors,
            "checks": report.checks
        }

    async def disk_list(self) -> Dict[str, Any]:
        """Lista discos com info SMART."""
        try:
            disks = self.lm.disk.get_disks()
            return {"disks": [{"device": d.device, "size": d.size, "fstype": d.fstype, "mountpoint": d.mountpoint, "model": d.model, "serial": d.serial, "health": d.health, "smart_available": d.smart_available} for d in disks]}
        except Exception as e:
            return {"error": str(e)}

    async def disk_smart(self, device: str) -> Dict[str, Any]:
        """SMART health completo."""
        try:
            return self.lm.disk.smart_health(device)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def disk_smart_test(self, device: str, test_type: str = "short") -> Dict[str, Any]:
        """Inicia teste SMART."""
        try:
            return self.lm.disk.smart_test(device, test_type)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def disk_fsck(self, device: str, dry_run: bool = True, fstype: str = None) -> Dict[str, Any]:
        """Verifica/repara filesystem."""
        try:
            return self.lm.disk.fsck_check(device, dry_run, fstype)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def disk_trim(self, mountpoint: str = "/") -> Dict[str, Any]:
        """TRIM no mountpoint."""
        try:
            return self.lm.disk.trim_filesystem(mountpoint)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def disk_trim_all(self) -> Dict[str, Any]:
        """TRIM em todos os filesystems."""
        try:
            return self.lm.disk.trim_all()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def disk_nvme(self, device: str = None) -> Dict[str, Any]:
        """NVMe health."""
        try:
            return self.lm.disk.nvme_health(device)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Uso de disco."""
        try:
            return self.lm.disk.disk_usage(path)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def systemd_services(self, name_filter: str = None) -> Dict[str, Any]:
        """Lista serviços systemd."""
        try:
            return self.lm.systemd.service_status(name_filter)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def systemd_failed(self) -> Dict[str, Any]:
        """Serviços falhados."""
        try:
            return self.lm.systemd.failed_services()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def systemd_restart(self, name: str) -> Dict[str, Any]:
        """Reinicia serviço."""
        try:
            return self.lm.systemd.restart_service(name)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def systemd_enable(self, name: str, now: bool = False) -> Dict[str, Any]:
        """Habilita serviço."""
        try:
            return self.lm.systemd.enable_service(name, now)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def journal_errors(self, since: str = "7 days ago", priority: int = 3, unit: str = None) -> Dict[str, Any]:
        """Erros do journalctl."""
        try:
            return self.lm.systemd.journal_errors(since, priority, unit)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def boot_analysis(self) -> Dict[str, Any]:
        """Análise de boot."""
        try:
            return self.lm.systemd.boot_analysis()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def kernel_dmesg(self, level: str = "err,crit,alert,emerg") -> Dict[str, Any]:
        """Erros do kernel."""
        try:
            return self.lm.kernel.dmesg_errors(level)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def kernel_sysctl(self, pattern: str = None) -> Dict[str, Any]:
        """Parâmetros kernel."""
        try:
            return self.lm.kernel.sysctl_show(pattern)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def kernel_sysctl_set(self, param: str, value: str) -> Dict[str, Any]:
        """Define parâmetro kernel."""
        try:
            return self.lm.kernel.sysctl_set(param, value)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def kernel_grub(self, output: str = "/boot/grub/grub.cfg") -> Dict[str, Any]:
        """Regenera GRUB."""
        try:
            return self.lm.kernel.grub_config(output)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def kernel_efi(self) -> Dict[str, Any]:
        """Lista entradas EFI."""
        try:
            return self.lm.kernel.efibootmgr_list()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def kernel_initramfs(self, kernel: str = "all") -> Dict[str, Any]:
        """Reconstrói initramfs."""
        try:
            return self.lm.kernel.initramfs_rebuild(kernel)
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def packages_check(self) -> Dict[str, Any]:
        """Verifica atualizações."""
        try:
            return self.lm.packages.update_check()
        except (DistroNotSupported, ToolNotFound) as e:
            return {"error": str(e)}

    async def packages_upgrade(self, dry_run: bool = True) -> Dict[str, Any]:
        """Atualiza pacotes."""
        try:
            return self.lm.packages.upgrade(dry_run)
        except (RootRequired, DistroNotSupported, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def packages_clean(self) -> Dict[str, Any]:
        """Limpa cache."""
        try:
            return self.lm.packages.clean_cache()
        except (RootRequired, DistroNotSupported, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def packages_verify(self) -> Dict[str, Any]:
        """Verifica integridade."""
        try:
            return self.lm.packages.verify_packages()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def logs_export(self, days: int = 7, priority: int = 3, output: str = None, unit: str = None) -> Dict[str, Any]:
        """Exporta erros do journalctl."""
        try:
            return self.lm.logs.export_errors(days, priority, output, unit)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def logs_audit(self) -> Dict[str, Any]:
        """Resumo auditd."""
        try:
            return self.lm.logs.audit_summary()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def logs_logins(self, failed_only: bool = False) -> Dict[str, Any]:
        """Histórico de login."""
        try:
            return self.lm.logs.login_history(failed_only)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_interfaces(self) -> Dict[str, Any]:
        """Interfaces de rede."""
        try:
            return self.lm.network.interfaces()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_sockets(self, listening: bool = True, tcp: bool = True, udp: bool = True) -> Dict[str, Any]:
        """Sockets."""
        try:
            return self.lm.network.sockets(listening, tcp, udp)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_dns(self, domain: str, record: str = "A") -> Dict[str, Any]:
        """DNS lookup."""
        try:
            return self.lm.network.dns_lookup(domain, record)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_http(self, url: str, timeout_sec: int = 10) -> Dict[str, Any]:
        """HTTP check."""
        try:
            return self.lm.network.http_check(url, timeout_sec)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_ping(self, target: str, count: int = 4) -> Dict[str, Any]:
        """Ping test."""
        try:
            return self.lm.network.ping_test(target, count)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def network_firewall(self) -> Dict[str, Any]:
        """Status firewall."""
        try:
            return self.lm.network.firewall_status()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def hardware_sensors(self) -> Dict[str, Any]:
        """Sensores lm-sensors."""
        try:
            return self.lm.hardware.sensors_read()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def hardware_pci(self) -> Dict[str, Any]:
        """Dispositivos PCI."""
        try:
            return self.lm.hardware.pci_devices()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def hardware_usb(self) -> Dict[str, Any]:
        """Dispositivos USB."""
        try:
            return self.lm.hardware.usb_devices()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def hardware_smbios(self) -> Dict[str, Any]:
        """SMBIOS (root)."""
        try:
            return self.lm.hardware.smbios_info()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def hardware_cpu(self) -> Dict[str, Any]:
        """Info CPU."""
        try:
            return self.lm.processes.cpu_info()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def processes_top(self, count: int = 20, sort: str = "cpu") -> Dict[str, Any]:
        """Top processos."""
        try:
            return self.lm.processes.top_processes(count, sort)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def processes_memory(self) -> Dict[str, Any]:
        """Info memória."""
        try:
            return self.lm.processes.memory_info()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def processes_vmstat(self, interval: int = 1, count: int = 5) -> Dict[str, Any]:
        """VM stats."""
        try:
            return self.lm.processes.vmstat_stats(interval, count)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def processes_iostat(self, interval: int = 1, count: int = 5) -> Dict[str, Any]:
        """I/O stats."""
        try:
            return self.lm.processes.disk_io_stats(interval, count)
        except ToolNotFound as e:
            return {"error": str(e)}

    async def security_ssh(self) -> Dict[str, Any]:
        """SSH config check."""
        try:
            return self.lm.security.ssh_config_check()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def security_apparmor(self) -> Dict[str, Any]:
        """AppArmor status."""
        try:
            return self.lm.security.apparmor_status()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}

    async def security_selinux(self) -> Dict[str, Any]:
        """SELinux status."""
        try:
            return self.lm.security.selinux_status()
        except ToolNotFound as e:
            return {"error": str(e)}

    async def security_lynis(self) -> Dict[str, Any]:
        """Lynis audit."""
        try:
            return self.lm.security.lynis_audit()
        except (RootRequired, ToolNotFound) as e:
            return {"error": str(e), "requires_root": isinstance(e, RootRequired)}


# MCP Protocol handlers
mcp = LinuxMaintenanceMCP()

TOOLS = {
    "linux_health_check": {
        "description": "Health check completo do Linux (não invasivo, sem root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.health_check
    },
    "linux_disk_list": {
        "description": "Lista discos com info SMART",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.disk_list
    },
    "linux_disk_smart": {
        "description": "SMART health completo do disco",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "Device (ex: /dev/sda)"}
            },
            "required": ["device"]
        },
        "handler": mcp.disk_smart
    },
    "linux_disk_smart_test": {
        "description": "Inicia teste SMART (short/long/conveyance)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "Device"},
                "test_type": {"type": "string", "enum": ["short", "long", "conveyance"], "default": "short"}
            },
            "required": ["device"]
        },
        "handler": mcp.disk_smart_test
    },
    "linux_disk_fsck": {
        "description": "Verifica filesystem (fsck). Dry-run por padrão.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "Device"},
                "dry_run": {"type": "boolean", "default": True},
                "fstype": {"type": "string", "description": "Tipo FS (ext4, xfs, etc.)"}
            },
            "required": ["device"]
        },
        "handler": mcp.disk_fsck
    },
    "linux_disk_trim": {
        "description": "TRIM no mountpoint (fstrim)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mountpoint": {"type": "string", "default": "/"}
            }
        },
        "handler": mcp.disk_trim
    },
    "linux_disk_trim_all": {
        "description": "TRIM em todos os filesystems",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.disk_trim_all
    },
    "linux_disk_nvme": {
        "description": "NVMe health via nvme-cli",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "Device opcional (ex: /dev/nvme0)"}
            }
        },
        "handler": mcp.disk_nvme
    },
    "linux_disk_usage": {
        "description": "Uso de disco (df)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "/"}
            }
        },
        "handler": mcp.disk_usage
    },
    "linux_systemd_services": {
        "description": "Lista serviços systemd",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_filter": {"type": "string"}
            }
        },
        "handler": mcp.systemd_services
    },
    "linux_systemd_failed": {
        "description": "Serviços falhados",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.systemd_failed
    },
    "linux_systemd_restart": {
        "description": "Reinicia serviço (root)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        },
        "handler": mcp.systemd_restart
    },
    "linux_systemd_enable": {
        "description": "Habilita serviço (root)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "now": {"type": "boolean", "default": False}
            },
            "required": ["name"]
        },
        "handler": mcp.systemd_enable
    },
    "linux_journal_errors": {
        "description": "Erros do journalctl",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {"type": "string", "default": "7 days ago"},
                "priority": {"type": "integer", "default": 3},
                "unit": {"type": "string"}
            }
        },
        "handler": mcp.journal_errors
    },
    "linux_boot_analysis": {
        "description": "Análise de boot (systemd-analyze)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.boot_analysis
    },
    "linux_kernel_dmesg": {
        "description": "Erros do kernel (dmesg)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "default": "err,crit,alert,emerg"}
            }
        },
        "handler": mcp.kernel_dmesg
    },
    "linux_kernel_sysctl": {
        "description": "Parâmetros kernel (sysctl)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"}
            }
        },
        "handler": mcp.kernel_sysctl
    },
    "linux_kernel_sysctl_set": {
        "description": "Define parâmetro kernel (root)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["param", "value"]
        },
        "handler": mcp.kernel_sysctl_set
    },
    "linux_kernel_grub": {
        "description": "Regenera GRUB (root)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "default": "/boot/grub/grub.cfg"}
            }
        },
        "handler": mcp.kernel_grub
    },
    "linux_kernel_efi": {
        "description": "Lista entradas EFI boot (root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.kernel_efi
    },
    "linux_kernel_initramfs": {
        "description": "Reconstrói initramfs (root)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kernel": {"type": "string", "default": "all"}
            }
        },
        "handler": mcp.kernel_initramfs
    },
    "linux_packages_check": {
        "description": "Verifica atualizações de pacotes",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.packages_check
    },
    "linux_packages_upgrade": {
        "description": "Atualiza pacotes (dry-run por padrão)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dry_run": {"type": "boolean", "default": True}
            }
        },
        "handler": mcp.packages_upgrade
    },
    "linux_packages_clean": {
        "description": "Limpa cache de pacotes (root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.packages_clean
    },
    "linux_packages_verify": {
        "description": "Verifica integridade de pacotes",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.packages_verify
    },
    "linux_logs_export": {
        "description": "Exporta erros do journalctl",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 7},
                "priority": {"type": "integer", "default": 3},
                "output": {"type": "string"},
                "unit": {"type": "string"}
            }
        },
        "handler": mcp.logs_export
    },
    "linux_logs_audit": {
        "description": "Resumo de auditoria (auditd)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.logs_audit
    },
    "linux_logs_logins": {
        "description": "Histórico de login (last/lastb)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "failed_only": {"type": "boolean", "default": False}
            }
        },
        "handler": mcp.logs_logins
    },
    "linux_network_interfaces": {
        "description": "Interfaces de rede",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.network_interfaces
    },
    "linux_network_sockets": {
        "description": "Sockets listening/established",
        "inputSchema": {
            "type": "object",
            "properties": {
                "listening": {"type": "boolean", "default": True},
                "tcp": {"type": "boolean", "default": True},
                "udp": {"type": "boolean", "default": True}
            }
        },
        "handler": mcp.network_sockets
    },
    "linux_network_dns": {
        "description": "DNS lookup (dig)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "record": {"type": "string", "default": "A"}
            },
            "required": ["domain"]
        },
        "handler": mcp.network_dns
    },
    "linux_network_http": {
        "description": "HTTP check (curl)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout_sec": {"type": "integer", "default": 10}
            },
            "required": ["url"]
        },
        "handler": mcp.network_http
    },
    "linux_network_ping": {
        "description": "Ping test",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "count": {"type": "integer", "default": 4}
            },
            "required": ["target"]
        },
        "handler": mcp.network_ping
    },
    "linux_network_firewall": {
        "description": "Status firewall (nftables/iptables/ufw/firewalld)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.network_firewall
    },
    "linux_hardware_sensors": {
        "description": "Sensores (lm-sensors)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.hardware_sensors
    },
    "linux_hardware_pci": {
        "description": "Dispositivos PCI (lspci)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.hardware_pci
    },
    "linux_hardware_usb": {
        "description": "Dispositivos USB (lsusb)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.hardware_usb
    },
    "linux_hardware_smbios": {
        "description": "SMBIOS/DMI (dmidecode, root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.hardware_smbios
    },
    "linux_hardware_cpu": {
        "description": "Info CPU (lscpu, /proc/cpuinfo)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.hardware_cpu
    },
    "linux_processes_top": {
        "description": "Top processos (ps)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 20},
                "sort": {"type": "string", "enum": ["cpu", "mem", "time", "pid"], "default": "cpu"}
            }
        },
        "handler": mcp.processes_top
    },
    "linux_processes_memory": {
        "description": "Info memória (free, /proc/meminfo)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.processes_memory
    },
    "linux_processes_vmstat": {
        "description": "VM stats (vmstat)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "interval": {"type": "integer", "default": 1},
                "count": {"type": "integer", "default": 5}
            }
        },
        "handler": mcp.processes_vmstat
    },
    "linux_processes_iostat": {
        "description": "I/O stats (iostat)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "interval": {"type": "integer", "default": 1},
                "count": {"type": "integer", "default": 5}
            }
        },
        "handler": mcp.processes_iostat
    },
    "linux_security_ssh": {
        "description": "SSH config hardening check",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.security_ssh
    },
    "linux_security_apparmor": {
        "description": "AppArmor status (root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.security_apparmor
    },
    "linux_security_selinux": {
        "description": "SELinux status",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.security_selinux
    },
    "linux_security_lynis": {
        "description": "Lynis security audit (root)",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": mcp.security_lynis
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
                "serverInfo": {"name": "linux-maintenance", "version": "1.0.0"}
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }


async def main():
    """Main loop para stdio transport."""
    print("Linux Maintenance MCP Server started", file=sys.stderr)
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