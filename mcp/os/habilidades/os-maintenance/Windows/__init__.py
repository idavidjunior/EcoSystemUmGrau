"""
Windows Native Maintenance - EcoSystemUmGrau
Ferramentas nativas do Windows para diagnóstico, reparo e otimização.
"""

from .windows_maintenance import (
    WindowsMaintenance,
    DiskHealth,
    SystemIntegrity,
    EventLogManager,
    BootConfig,
    WindowsUpdateManager,
    ServiceManager,
    NetworkDiagnostics,
    DriverManager,
    DiskInfo,
    HealthReport,
    AdminRequired,
    ToolNotFound,
)

__all__ = [
    "WindowsMaintenance",
    "DiskHealth",
    "SystemIntegrity",
    "EventLogManager",
    "BootConfig",
    "WindowsUpdateManager",
    "ServiceManager",
    "NetworkDiagnostics",
    "DriverManager",
    "DiskInfo",
    "HealthReport",
    "AdminRequired",
    "ToolNotFound",
]

__version__ = "1.0.0"
__author__ = "EcoSystemUmGrau"