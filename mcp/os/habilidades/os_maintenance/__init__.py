"""
os-maintenance — Núcleo Unificado de Manutenção Windows + Linux
EcoSystemUmGrau

Ferramentas nativas completas para diagnóstico, reparo, otimização e saúde do sistema.
Zero dependências externas — apenas built-ins do SO.
"""

import sys
import os

# Add subdirectories to path for imports
_base = os.path.dirname(os.path.abspath(__file__))
_win = os.path.join(_base, "Windows")
_lin = os.path.join(_base, "Linux")

for p in (_win, _lin):
    if p not in sys.path:
        sys.path.insert(0, p)


# Unified interface - detects OS at runtime
def get_maintenance():
    """Retorna instância apropriada para o SO atual."""
    if sys.platform.startswith("win32"):
        from windows_maintenance import WindowsMaintenance
        return WindowsMaintenance()
    else:
        from linux_maintenance import LinuxMaintenance
        return LinuxMaintenance()


def get_mcp_server():
    """Retorna classe do MCP server para o SO atual."""
    if sys.platform.startswith("win32"):
        from server import WindowsMaintenanceMCP
        return WindowsMaintenanceMCP()
    else:
        from server import LinuxMaintenanceMCP
        return LinuxMaintenanceMCP()


# Exceptions unified
class MaintenanceError(Exception):
    """Base exception."""
    pass


class PrivilegeRequired(MaintenanceError):
    """Operação requer privilégios elevados (Admin/root)."""
    pass


class ToolMissing(MaintenanceError):
    """Ferramenta nativa não encontrada."""
    pass


class DistroUnsupported(MaintenanceError):
    """Distro/SO não suportado para operação."""
    pass


# Common datatypes
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class DiskInfo:
    device: str
    size: str
    fstype: str
    mountpoint: str
    model: str = ""
    serial: str = ""
    health: str = "Unknown"
    smart_available: bool = False
    media_type: str = "Unknown"  # Windows: HDD/SSD/SCM


@dataclass
class HealthReport:
    timestamp: str
    overall_status: str  # Healthy, Warning, Degraded
    checks: Dict[str, Any]
    recommendations: List[str]
    errors: List[str]


# Re-export key classes for convenience
try:
    from windows_maintenance import (
        WindowsMaintenance,
        DiskHealth,
        SystemIntegrity,
        EventLogManager,
        BootConfig,
        WindowsUpdateManager,
        ServiceManager,
        NetworkDiagnostics,
        DriverManager,
        AdminRequired as WindowsAdminRequired,
    )
except ImportError:
    WindowsMaintenance = None
    DiskHealth = None
    SystemIntegrity = None
    EventLogManager = None
    BootConfig = None
    WindowsUpdateManager = None
    ServiceManager = None
    NetworkDiagnostics = None
    DriverManager = None
    WindowsAdminRequired = None

try:
    from linux_maintenance import (
        LinuxMaintenance,
        DiskHealth as LinuxDiskHealth,
        SystemdManager,
        KernelBoot,
        PackageManager,
        LogManager,
        NetworkDiagnostics as LinuxNetworkDiagnostics,
        ProcessResources,
        HardwareSensors,
        SecurityHardening,
        RootRequired as LinuxRootRequired,
        ToolNotFound as LinuxToolNotFound,
        DistroNotSupported as LinuxDistroNotSupported,
    )
except ImportError:
    LinuxMaintenance = None
    LinuxDiskHealth = None
    SystemdManager = None
    KernelBoot = None
    PackageManager = None
    LogManager = None
    LinuxNetworkDiagnostics = None
    ProcessResources = None
    HardwareSensors = None
    SecurityHardening = None
    LinuxRootRequired = None
    LinuxToolNotFound = None
    LinuxDistroNotSupported = None


__all__ = [
    # Unified interface
    "get_maintenance",
    "get_mcp_server",
    "MaintenanceError",
    "PrivilegeRequired",
    "ToolMissing",
    "DistroUnsupported",
    "DiskInfo",
    "HealthReport",

    # Windows (if available)
    "WindowsMaintenance",
    "DiskHealth",
    "SystemIntegrity",
    "EventLogManager",
    "BootConfig",
    "WindowsUpdateManager",
    "ServiceManager",
    "NetworkDiagnostics",
    "DriverManager",
    "WindowsAdminRequired",

    # Linux (if available)
    "LinuxMaintenance",
    "LinuxDiskHealth",
    "SystemdManager",
    "KernelBoot",
    "PackageManager",
    "LogManager",
    "LinuxNetworkDiagnostics",
    "ProcessResources",
    "HardwareSensors",
    "SecurityHardening",
    "LinuxRootRequired",
    "LinuxToolNotFound",
    "LinuxDistroNotSupported",
]

__version__ = "1.0.0"
__author__ = "EcoSystemUmGrau"

# OS detection
CURRENT_OS = "Windows" if sys.platform.startswith("win32") else "Linux"