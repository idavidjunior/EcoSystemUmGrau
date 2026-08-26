#!/usr/bin/env python3
"""
Windows Native Maintenance Toolkit
Domina todas as ferramentas nativas do Windows para diagnóstico, reparo e otimização.
Zero dependências externas — apenas Windows built-ins.
"""

import subprocess
import json
import sys
import os
import argparse
import time
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum


class AdminRequired(Exception):
    """Operação requer privilégios de administrador."""
    pass


class ToolNotFound(Exception):
    """Ferramenta nativa não encontrada."""
    pass


def run_cmd(cmd: List[str], capture: bool = True, timeout: int = 300, require_admin: bool = False) -> Tuple[int, str, str]:
    """Executa comando e retorna (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout após {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Comando não encontrado: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def is_admin() -> bool:
    """Verifica se está rodando como administrador."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def require_admin_check(op_name: str):
    """Levanta exceção se não for admin e operação requer."""
    if not is_admin():
        raise AdminRequired(f"Operação '{op_name}' requer execução como Administrador. Reinicie o terminal como Admin.")


@dataclass
class DiskInfo:
    drive_letter: str
    file_system: str
    size_gb: float
    free_gb: float
    health_status: str = "Unknown"
    operational_status: str = "Unknown"
    media_type: str = "Unknown"  # HDD, SSD, SCM, Unspecified


@dataclass
class HealthReport:
    timestamp: str
    overall_status: str
    checks: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DiskHealth:
    """Gerencia saúde de disco: chkdsk, defrag, Storage Health, SMART."""

    def __init__(self):
        self.ps_available = self._check_powershell_storage()

    def _check_powershell_storage(self) -> bool:
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", "Get-Command -Module Storage -Name Get-PhysicalDisk"])
        return code == 0

    def get_disks(self) -> List[DiskInfo]:
        """Obtém info de todos os discos via PowerShell Storage module."""
        if not self.ps_available:
            return self._get_disks_legacy()

        ps_script = """
        Get-PhysicalDisk | ForEach-Object {
            $disk = $_
            $partitions = Get-Partition -DiskNumber $disk.DeviceId -ErrorAction SilentlyContinue
            $volumes = $partitions | Get-Volume -ErrorAction SilentlyContinue
            $drive = if ($volumes) { $volumes[0].DriveLetter } else { "" }
            [pscustomobject]@{
                DeviceId = $disk.DeviceId
                DriveLetter = $drive
                FriendlyName = $disk.FriendlyName
                MediaType = $disk.MediaType
                HealthStatus = $disk.HealthStatus
                OperationalStatus = $disk.OperationalStatus
                Size = $disk.Size
            }
        } | ConvertTo-Json -Depth 3
        """
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script])
        if code != 0:
            return self._get_disks_legacy()

        try:
            data = json.loads(out)
            if not isinstance(data, list):
                data = [data]
            disks = []
            for d in data:
                size_gb = d.get("Size", 0) / (1024**3)
                disks.append(DiskInfo(
                    drive_letter=d.get("DriveLetter", "") or f"Disk{d.get('DeviceId', '?')}",
                    file_system="NTFS",  # default assumido
                    size_gb=round(size_gb, 2),
                    free_gb=0,  # preenchido abaixo
                    health_status=d.get("HealthStatus", "Unknown"),
                    operational_status=", ".join(d.get("OperationalStatus", ["Unknown"])) if isinstance(d.get("OperationalStatus"), list) else str(d.get("OperationalStatus", "Unknown")),
                    media_type=d.get("MediaType", "Unknown")
                ))
            # Preencher free space via Get-Volume
            self._enrich_free_space(disks)
            return disks
        except Exception:
            return self._get_disks_legacy()

    def _enrich_free_space(self, disks: List[DiskInfo]):
        ps_script = """
        Get-Partition | Where-Object { $_.DriveLetter } | ForEach-Object {
            $part = $_
            $vol = Get-Volume -Partition $part -ErrorAction SilentlyContinue
            if ($vol) {
                [pscustomobject]@{
                    DriveLetter = $part.DriveLetter
                    DiskNumber = $part.DiskNumber
                    SizeRemaining = $vol.SizeRemaining
                    FileSystem = $vol.FileSystem
                }
            }
        } | ConvertTo-Json
        """
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=120)
        if code == 0:
            try:
                vols = json.loads(out)
                if not isinstance(vols, list):
                    vols = [vols] if vols else []
                # Map by DiskNumber
                vol_map = {}
                for v in vols:
                    if v.get("DriveLetter"):
                        key = f"Disk{v.get('DiskNumber', '?')}"
                        vol_map[key] = v
                
                for d in disks:
                    # Try to match by drive letter first
                    matched = False
                    for v in vols:
                        if v.get("DriveLetter") and d.drive_letter.rstrip(':').upper() == v.get("DriveLetter").upper():
                            d.free_gb = round(v.get("SizeRemaining", 0) / (1024**3), 2)
                            d.file_system = v.get("FileSystem", "NTFS")
                            matched = True
                            break
                    
                    # If not matched by drive letter, try by disk number
                    if not matched and d.drive_letter.startswith("Disk"):
                        disk_num = d.drive_letter.replace("Disk", "")
                        key = f"Disk{disk_num}"
                        if key in vol_map:
                            v = vol_map[key]
                            d.free_gb = round(v.get("SizeRemaining", 0) / (1024**3), 2)
                            d.file_system = v.get("FileSystem", "NTFS")
            except Exception:
                pass

    def _get_disks_legacy(self) -> List[DiskInfo]:
        """Fallback usando wmic (deprecated mas funcional)."""
        code, out, err = run_cmd(["wmic", "logicaldisk", "get", "DeviceID,FileSystem,Size,FreeSpace,VolumeName", "/format:csv"])
        disks = []
        if code == 0:
            lines = out.strip().split('\n')
            if len(lines) > 1:
                headers = lines[0].split(',')
                for line in lines[1:]:
                    parts = line.split(',')
                    if len(parts) >= 5:
                        drive = parts[headers.index('DeviceID')] if 'DeviceID' in headers else parts[1]
                        fs = parts[headers.index('FileSystem')] if 'FileSystem' in headers else "NTFS"
                        size = int(parts[headers.index('Size')]) if 'Size' in headers and parts[headers.index('Size')] else 0
                        free = int(parts[headers.index('FreeSpace')]) if 'FreeSpace' in headers and parts[headers.index('FreeSpace')] else 0
                        disks.append(DiskInfo(
                            drive_letter=drive,
                            file_system=fs,
                            size_gb=round(size / (1024**3), 2),
                            free_gb=round(free / (1024**3), 2)
                        ))
        return disks

    def winfr_recover(self, source: str, dest: str, mode: str = "regular", filters: List[str] = None, file_types: List[str] = None) -> Dict[str, Any]:
        """Windows File Recovery (winfr). Requer Admin + winfr instalado via Microsoft Store."""
        require_admin_check("winfr_recover")
        
        # Verificar se winfr existe
        code, out, err = run_cmd(["where", "winfr"], timeout=10)
        if code != 0:
            return {
                "error": "winfr não encontrado. Instale via Microsoft Store: 'Microsoft.WindowsFileRecovery' ou 'winget install Microsoft.WindowsFileRecovery'",
                "exit_code": -1,
                "installed": False
            }

        source = source.rstrip(':\\')
        if not source.endswith(':'):
            source += ':'
        dest = dest.rstrip(':\\')
        if not dest.endswith(':'):
            dest += ':'

        valid_modes = ["regular", "extensive", "segment"]
        if mode not in valid_modes:
            mode = "regular"

        cmd = ["winfr", source, dest, f"/{mode}"]
        
        if filters:
            for f in filters:
                cmd.extend(["/n", f])
        
        if file_types:
            for ft in file_types:
                cmd.extend(["/y", ft])

        result = {
            "source": source,
            "dest": dest,
            "mode": mode,
            "filters": filters,
            "file_types": file_types,
            "timestamp": datetime.now().isoformat()
        }

        code, out, err = run_cmd(cmd, timeout=7200)  # 2h max
        result["exit_code"] = code
        result["output"] = out
        result["errors"] = err
        
        return result

    def winfr_check_installed(self) -> Dict[str, Any]:
        """Verifica se winfr está instalado."""
        code, out, err = run_cmd(["where", "winfr"], timeout=10)
        if code == 0:
            # Tentar obter versão
            code2, out2, err2 = run_cmd(["winfr", "/?"], timeout=10)
            return {"installed": True, "path": out.strip(), "version_info": out2}
        return {"installed": False, "error": "winfr não encontrado no PATH"}

    def analyze_volume(self, drive: str) -> Dict[str, Any]:
        """Analisa volume (chkdsk /scan para NTFS online)."""
        drive = drive.rstrip(':\\')
        if not drive.endswith(':'):
            drive += ':'

        result = {"drive": drive, "timestamp": datetime.now().isoformat()}

        # chkdsk /scan (online, read-only)
        code, out, err = run_cmd(["chkdsk", drive, "/scan"], timeout=600)
        result["chkdsk_scan"] = {"exit_code": code, "output": out, "errors": err}

        # PowerShell Repair-Volume (online repair simulation)
        if self.ps_available:
            ps_script = f"Repair-Volume -DriveLetter '{drive.rstrip(':')}' -ScanOnly | ConvertTo-Json"
            code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=600)
            result["repair_volume_scan"] = {"exit_code": code, "output": out, "errors": err}

        return result

    def repair_volume(self, drive: str, offline: bool = False) -> Dict[str, Any]:
        """Repara volume. Requer Admin."""
        require_admin_check("repair_volume")
        drive = drive.rstrip(':\\')
        if not drive.endswith(':'):
            drive += ':'

        result = {"drive": drive, "timestamp": datetime.now().isoformat(), "offline": offline}

        if offline:
            # chkdsk /f /r offline (requer reinicialização para C:)
            code, out, err = run_cmd(["chkdsk", drive, "/f", "/r"], timeout=3600)
            result["chkdsk_offline"] = {"exit_code": code, "output": out, "errors": err}
        else:
            # chkdsk /scan + /spotfix (online spot fix)
            code, out, err = run_cmd(["chkdsk", drive, "/scan", "/forceofflinefix"], timeout=600)
            result["chkdsk_online_spotfix"] = {"exit_code": code, "output": out, "errors": err}

            # PowerShell Repair-Volume
            if self.ps_available:
                ps_script = f"Repair-Volume -DriveLetter '{drive.rstrip(':')}' | ConvertTo-Json"
                code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=600)
                result["repair_volume"] = {"exit_code": code, "output": out, "errors": err}

        return result

    def optimize_volume(self, drive: str, operation: str = "Optimize") -> Dict[str, Any]:
        """
        Otimiza volume.
        Operações: Analyze, Defrag, Retrim, TierOptimize, BootOptimize, SlabConsolidate, FreespaceConsolidate, Optimize (auto)
        """
        drive = drive.rstrip(':\\')
        if not drive.endswith(':'):
            drive += ':'

        valid_ops = ["Analyze", "Defrag", "Retrim", "TierOptimize", "BootOptimize", "SlabConsolidate", "FreespaceConsolidate", "Optimize"]
        if operation not in valid_ops:
            operation = "Optimize"

        result = {"drive": drive, "operation": operation, "timestamp": datetime.now().isoformat()}

        # defrag CLI
        op_map = {
            "Analyze": "/A",
            "Defrag": "/D",
            "Retrim": "/L",
            "TierOptimize": "/G",
            "BootOptimize": "/B",
            "SlabConsolidate": "/K",
            "FreespaceConsolidate": "/X",
            "Optimize": "/O"
        }
        code, out, err = run_cmd(["defrag", drive, op_map[operation], "/U", "/V"], timeout=3600)
        result["defrag"] = {"exit_code": code, "output": out, "errors": err}

        # PowerShell Optimize-Volume (mais detalhado)
        if self.ps_available:
            ps_script = f"Optimize-Volume -DriveLetter '{drive.rstrip(':')}' -{operation} -Verbose | ConvertTo-Json"
            code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=3600)
            result["optimize_volume"] = {"exit_code": code, "output": out, "errors": err}

        return result

    def get_storage_health(self) -> Dict[str, Any]:
        """Relatório completo de saúde de armazenamento (SMART/NVMe)."""
        if not self.ps_available:
            return {"error": "PowerShell Storage module não disponível"}

        ps_script = """
        $health = Get-StorageHealthReport
        $disks = Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, HealthStatus, OperationalStatus, Size, SerialNumber
        $actions = Get-StorageHealthAction
        [pscustomobject]@{
            HealthReport = $health
            Disks = $disks
            Actions = $actions
        } | ConvertTo-Json -Depth 4
        """
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=120)
        if code == 0:
            try:
                return json.loads(out)
            except Exception:
                return {"error": "Falha ao parsear JSON", "raw": out}
        return {"error": err, "exit_code": code}


class SystemIntegrity:
    """sfc, DISM, component store."""

    def run_sfc(self, offline: bool = False, offline_windir: str = None, offline_bootdir: str = None) -> Dict[str, Any]:
        """Executa sfc /scannow. Requer Admin."""
        require_admin_check("sfc")

        cmd = ["sfc", "/scannow"]
        if offline:
            if not offline_windir or not offline_bootdir:
                raise ValueError("Offline requer offline_windir e offline_bootdir")
            cmd = ["sfc", f"/offlinewindir={offline_windir}", f"/offlinebootdir={offline_bootdir}", "/scannow"]

        code, out, err = run_cmd(cmd, timeout=3600)
        return {"exit_code": code, "output": out, "errors": err, "timestamp": datetime.now().isoformat()}

    def run_dism_restore_health(self) -> Dict[str, Any]:
        """DISM /Online /Cleanup-Image /RestoreHealth. Requer Admin."""
        require_admin_check("dism_restore")
        cmd = ["dism", "/Online", "/Cleanup-Image", "/RestoreHealth"]
        code, out, err = run_cmd(cmd, timeout=3600)
        return {"exit_code": code, "output": out, "errors": err, "timestamp": datetime.now().isoformat()}

    def run_dism_component_cleanup(self, start: bool = True, analyze: bool = False) -> Dict[str, Any]:
        """DISM component store cleanup. Requer Admin."""
        require_admin_check("dism_cleanup")
        if analyze:
            cmd = ["dism", "/Online", "/Cleanup-Image", "/AnalyzeComponentStore"]
        elif start:
            cmd = ["dism", "/Online", "/Cleanup-Image", "/StartComponentCleanup"]
        else:
            cmd = ["dism", "/Online", "/Cleanup-Image", "/StartComponentCleanup", "/ResetBase"]
        code, out, err = run_cmd(cmd, timeout=3600)
        return {"exit_code": code, "output": out, "errors": err, "timestamp": datetime.now().isoformat()}

    def run_dism_check_health(self) -> Dict[str, Any]:
        """DISM /Online /Cleanup-Image /CheckHealth. Requer Admin."""
        require_admin_check("dism_check")
        cmd = ["dism", "/Online", "/Cleanup-Image", "/CheckHealth"]
        code, out, err = run_cmd(cmd, timeout=300)
        return {"exit_code": code, "output": out, "errors": err, "timestamp": datetime.now().isoformat()}

    def run_dism_scan_health(self) -> Dict[str, Any]:
        """DISM /Online /Cleanup-Image /ScanHealth. Requer Admin."""
        require_admin_check("dism_scan")
        cmd = ["dism", "/Online", "/Cleanup-Image", "/ScanHealth"]
        code, out, err = run_cmd(cmd, timeout=600)
        return {"exit_code": code, "output": out, "errors": err, "timestamp": datetime.now().isoformat()}


class EventLogManager:
    """Gerencia logs de eventos via wevtutil e PowerShell."""

    def export_log(self, log_name: str, output_path: str, query: str = None, days: int = None) -> Dict[str, Any]:
        """Exporta log para .evtx."""
        cmd = ["wevtutil", "epl", log_name, output_path]
        if query:
            cmd = ["wevtutil", "qe", log_name, "/q:" + query, "/f:xml", "/e:root"]
            # wevtutil qe não exporta direto para arquivo, precisa redirecionar
        code, out, err = run_cmd(cmd, timeout=120)
        return {"exit_code": code, "output": out, "errors": err, "file": output_path}

    def export_errors(self, days: int = 7, output: str = None, logs: List[str] = None) -> Dict[str, Any]:
        """Exporta erros dos logs System/Application dos últimos N dias."""
        if logs is None:
            logs = ["System", "Application"]

        if output is None:
            output = f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.evtx"

        # Query XPath para eventos Error/Critical dos últimos N dias
        start_time = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
        query = f"*[System[(Level=1 or Level=2) and TimeCreated[@SystemTime >= '{start_time}']]]"

        results = {}
        for log in logs:
            out_file = output.replace(".evtx", f"_{log}.evtx")
            # Usar PowerShell para query mais robusta
            ps_script = f"""
            $events = Get-WinEvent -LogName '{log}' -FilterXPath '{query}' -ErrorAction SilentlyContinue
            if ($events) {{ $events | Export-Clixml -Path '{out_file}.xml' }}
            $events.Count
            """
            code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=120)
            results[log] = {"exit_code": code, "count": out.strip(), "file": f"{out_file}.xml", "errors": err}

        return {"logs": results, "query": query, "timestamp": datetime.now().isoformat()}

    def clear_log(self, log_name: str, backup_path: str = None) -> Dict[str, Any]:
        """Limpa log (opcionalmente faz backup antes). Requer Admin."""
        require_admin_check("clear_log")
        if backup_path:
            self.export_log(log_name, backup_path)
        code, out, err = run_cmd(["wevtutil", "cl", log_name], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def get_log_info(self, log_name: str) -> Dict[str, Any]:
        """Info do log (tamanho, retenção, etc)."""
        code, out, err = run_cmd(["wevtutil", "gli", log_name], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}


class BootConfig:
    """BCD e WinRE management."""

    def backup_bcd(self, output_path: str = None) -> Dict[str, Any]:
        """Backup do BCD. Requer Admin."""
        require_admin_check("backup_bcd")
        if output_path is None:
            output_path = f"BCD_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bcd"
        code, out, err = run_cmd(["bcdedit", "/export", output_path], timeout=30)
        return {"exit_code": code, "output": out, "errors": err, "file": output_path}

    def restore_bcd(self, backup_path: str) -> Dict[str, Any]:
        """Restore do BCD. Requer Admin."""
        require_admin_check("restore_bcd")
        code, out, err = run_cmd(["bcdedit", "/import", backup_path], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def enum_bcd(self, verbose: bool = False) -> Dict[str, Any]:
        """Lista entradas BCD."""
        cmd = ["bcdedit", "/enum"]
        if verbose:
            cmd.append("/v")
        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def reagentc_info(self) -> Dict[str, Any]:
        """Info do WinRE. Requer Admin para algumas operações."""
        code, out, err = run_cmd(["reagentc", "/info"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def reagentc_enable(self) -> Dict[str, Any]:
        """Habilita WinRE. Requer Admin."""
        require_admin_check("reagentc_enable")
        code, out, err = run_cmd(["reagentc", "/enable"], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def reagentc_disable(self) -> Dict[str, Any]:
        """Desabilita WinRE. Requer Admin."""
        require_admin_check("reagentc_disable")
        code, out, err = run_cmd(["reagentc", "/disable"], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}


class WindowsUpdateManager:
    """Windows Update status e logs."""

    def get_update_log(self, output_path: str = None) -> Dict[str, Any]:
        """Gera log legível do Windows Update."""
        if output_path is None:
            output_path = f"WindowsUpdate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", f"Get-WindowsUpdateLog -LogPath '{output_path}'"], timeout=120)
        return {"exit_code": code, "output": out, "errors": err, "file": output_path}

    def force_detection(self) -> Dict[str, Any]:
        """Força detecção de updates (legacy wuauclt)."""
        code, out, err = run_cmd(["wuauclt", "/detectnow"], timeout=60)
        code2, out2, err2 = run_cmd(["wuauclt", "/updatenow"], timeout=60)
        return {"detect": {"exit_code": code, "output": out, "errors": err}, "update": {"exit_code": code2, "output": out2, "errors": err2}}

    def uso_client_scan(self) -> Dict[str, Any]:
        """USOClient StartScan (moderno)."""
        code, out, err = run_cmd(["USOClient", "StartScan"], timeout=120)
        return {"exit_code": code, "output": out, "errors": err}

    def get_update_history(self) -> Dict[str, Any]:
        """Histórico de updates via PowerShell."""
        ps_script = """
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $history = $searcher.GetTotalHistoryCount()
        $updates = $searcher.QueryHistory(0, $history) | Select-Object Title, Date, ResultCode, Description | ConvertTo-Json -Depth 3
        $updates
        """
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=120)
        return {"exit_code": code, "output": out, "errors": err}


class ServiceManager:
    """Gerenciamento de serviços."""

    def list_services(self, name_filter: str = None, status: str = None) -> Dict[str, Any]:
        """Lista serviços."""
        ps_script = "Get-Service"
        if name_filter:
            ps_script += f" -Name '*{name_filter}*'"
        ps_script += " | Select-Object Name, DisplayName, Status, StartType, ServiceType | ConvertTo-Json"
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=60)
        if code == 0:
            try:
                svcs = json.loads(out)
                if not isinstance(svcs, list):
                    svcs = [svcs]
                if status:
                    svcs = [s for s in svcs if s.get("Status", "").lower() == status.lower()]
                return {"services": svcs, "count": len(svcs)}
            except Exception:
                pass
        return {"error": err, "exit_code": code, "raw": out}

    def restart_service(self, name: str) -> Dict[str, Any]:
        """Reinicia serviço. Requer Admin."""
        require_admin_check("restart_service")
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", f"Restart-Service -Name '{name}' -Force -Verbose"], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def set_startup(self, name: str, startup_type: str) -> Dict[str, Any]:
        """Define tipo de inicialização (Automatic, Manual, Disabled). Requer Admin."""
        require_admin_check("set_startup")
        valid = ["Automatic", "Manual", "Disabled", "AutomaticDelayedStart"]
        if startup_type not in valid:
            return {"error": f"Tipo inválido. Use: {', '.join(valid)}"}
        code, out, err = run_cmd(["sc", "config", name, f"start={startup_type}"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}


class NetworkDiagnostics:
    """Diagnóstico de rede nativo."""

    def test_connection(self, target: str, port: int = None) -> Dict[str, Any]:
        """Test-NetConnection (TCP/ICMP/DNS)."""
        ps_script = f"Test-NetConnection -ComputerName '{target}'"
        if port:
            ps_script += f" -Port {port}"
        ps_script += " | Select-Object ComputerName, RemoteAddress, RemotePort, TcpTestSucceeded, PingSucceeded, PingReplyDetails | ConvertTo-Json"
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def flush_dns(self) -> Dict[str, Any]:
        """ipconfig /flushdns."""
        code, out, err = run_cmd(["ipconfig", "/flushdns"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def reset_winsock(self) -> Dict[str, Any]:
        """netsh winsock reset. Requer Admin."""
        require_admin_check("reset_winsock")
        code, out, err = run_cmd(["netsh", "winsock", "reset"], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def reset_tcpip(self) -> Dict[str, Any]:
        """netsh int ip reset. Requer Admin."""
        require_admin_check("reset_tcpip")
        code, out, err = run_cmd(["netsh", "int", "ip", "reset"], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def show_interfaces(self) -> Dict[str, Any]:
        """netsh interface ipv4 show addresses."""
        code, out, err = run_cmd(["netsh", "interface", "ipv4", "show", "addresses"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}


class DriverManager:
    """Gerenciamento de drivers via pnputil."""

    def list_drivers(self, published_only: bool = True) -> Dict[str, Any]:
        """Lista drivers no driver store."""
        cmd = ["pnputil", "/enum-drivers"]
        if published_only:
            cmd.append("/published")
        code, out, err = run_cmd(cmd, timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def find_problem_drivers(self) -> Dict[str, Any]:
        """Busca dispositivos com problema via PowerShell."""
        ps_script = """
        Get-PnpDevice -Status Error, Unknown, Degraded | Select-Object InstanceId, Status, Class, FriendlyName, Problem | ConvertTo-Json -Depth 3
        """
        code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=60)
        if code == 0:
            try:
                devs = json.loads(out)
                if not isinstance(devs, list):
                    devs = [devs] if devs else []
                return {"devices": devs, "count": len(devs)}
            except Exception:
                pass
        return {"error": err, "exit_code": code, "raw": out}


class WindowsMaintenance:
    """Orquestrador principal."""

    def __init__(self):
        self.disk = DiskHealth()
        self.system = SystemIntegrity()
        self.logs = EventLogManager()
        self.boot = BootConfig()
        self.update = WindowsUpdateManager()
        self.services = ServiceManager()
        self.network = NetworkDiagnostics()
        self.drivers = DriverManager()
        self.winfr = self.disk  # winfr methods are in DiskHealth

    def full_health_check(self) -> HealthReport:
        """Health check completo não-invasivo (sem Admin)."""
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            overall_status="Checking..."
        )

        # Discos
        try:
            disks = self.disk.get_disks()
            report.checks["disks"] = [asdict(d) for d in disks]
            # Verificar saúde
            unhealthy = [d for d in disks if d.health_status not in ["Healthy", "Unknown"]]
            if unhealthy:
                report.recommendations.append(f"Discos com saúde degradada: {[d.drive_letter for d in unhealthy]}")
        except Exception as e:
            report.errors.append(f"Disk check: {e}")

        # Storage Health (PowerShell)
        if self.disk.ps_available:
            try:
                health = self.disk.get_storage_health()
                report.checks["storage_health"] = health
            except Exception as e:
                report.errors.append(f"Storage health: {e}")

        # Serviços críticos
        try:
            critical_services = ["wuauserv", "bits", "TrustedInstaller", "WinDefend", "Schedule"]
            svc_result = self.services.list_services()
            if "services" in svc_result:
                critical_status = {s["Name"]: s["Status"] for s in svc_result["services"] if s["Name"] in critical_services}
                report.checks["critical_services"] = critical_status
                stopped = [k for k, v in critical_status.items() if v != "Running"]
                if stopped:
                    report.recommendations.append(f"Serviços críticos parados: {stopped}")
        except Exception as e:
            report.errors.append(f"Services check: {e}")

        # Drivers com problema
        try:
            drv = self.drivers.find_problem_drivers()
            if drv.get("count", 0) > 0:
                report.checks["problem_drivers"] = drv
                report.recommendations.append(f"{drv['count']} dispositivo(s) com problema detectado(s)")
        except Exception as e:
            report.errors.append(f"Drivers check: {e}")

        # BCD
        try:
            bcd = self.boot.enum_bcd()
            report.checks["bcd"] = "OK" if bcd["exit_code"] == 0 else "Error"
        except Exception as e:
            report.errors.append(f"BCD check: {e}")

        # Determinar status geral
        if report.errors:
            report.overall_status = "Degraded"
        elif report.recommendations:
            report.overall_status = "Warning"
        else:
            report.overall_status = "Healthy"

        return report

    def generate_report(self, json_output: bool = False, output_file: str = None) -> Dict[str, Any]:
        """Gera relatório completo."""
        report = self.full_health_check()
        data = asdict(report)

        # Adicionar info do sistema
        data["system_info"] = {
            "os": platform.platform(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "is_admin": is_admin(),
            "powershell_storage": self.disk.ps_available
        }

        if json_output:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            if output_file:
                Path(output_file).write_text(json_str, encoding="utf-8")
                print(f"Relatório salvo em: {output_file}")
            else:
                print(json_str)

        return data


def main():
    parser = argparse.ArgumentParser(
        description="Windows Native Maintenance Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python windows_maintenance.py health
  python windows_maintenance.py disk --analyze C: --repair
  python windows_maintenance.py system --sfc --dism
  python windows_maintenance.py optimize C: --operation Retrim
  python windows_maintenance.py logs --errors --days 7
  python windows_maintenance.py boot --backup-bcd
  python windows_maintenance.py update --log
  python windows_maintenance.py drivers --problems
  python windows_maintenance.py report --json --output report.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando principal")

    # health
    subparsers.add_parser("health", help="Health check completo (não invasivo)")

    # disk
    disk_parser = subparsers.add_parser("disk", help="Operações de disco")
    disk_parser.add_argument("drive", nargs="?", default="C:", help="Drive letter (ex: C:)")
    disk_parser.add_argument("--analyze", action="store_true", help="Analisar volume (chkdsk /scan)")
    disk_parser.add_argument("--repair", action="store_true", help="Reparar volume (requer Admin)")
    disk_parser.add_argument("--offline", action="store_true", help="Reparo offline (chkdsk /f /r)")
    disk_parser.add_argument("--optimize", action="store_true", help="Otimizar volume")
    disk_parser.add_argument("--operation", choices=["Analyze", "Defrag", "Retrim", "TierOptimize", "BootOptimize", "SlabConsolidate", "FreespaceConsolidate", "Optimize"], default="Optimize", help="Tipo de otimização")
    disk_parser.add_argument("--health", action="store_true", help="Relatório Storage Health (SMART)")

    # system
    sys_parser = subparsers.add_parser("system", help="Integridade do sistema")
    sys_parser.add_argument("--sfc", action="store_true", help="Executar sfc /scannow")
    sys_parser.add_argument("--dism", action="store_true", help="Executar DISM RestoreHealth")
    sys_parser.add_argument("--dism-scan", action="store_true", help="DISM ScanHealth")
    sys_parser.add_argument("--dism-check", action="store_true", help="DISM CheckHealth")
    sys_parser.add_argument("--dism-cleanup", action="store_true", help="DISM StartComponentCleanup")

    # optimize
    opt_parser = subparsers.add_parser("optimize", help="Otimização de volume")
    opt_parser.add_argument("drive", nargs="?", default="C:", help="Drive letter")
    opt_parser.add_argument("--operation", choices=["Analyze", "Defrag", "Retrim", "TierOptimize", "BootOptimize", "SlabConsolidate", "FreespaceConsolidate", "Optimize"], default="Optimize")
    opt_parser.add_argument("--all", action="store_true", help="Executar todas otimizações apropriadas")

    # logs
    log_parser = subparsers.add_parser("logs", help="Logs de eventos")
    log_parser.add_argument("--errors", action="store_true", help="Exportar erros recentes")
    log_parser.add_argument("--days", type=int, default=7, help="Dias para buscar erros")
    log_parser.add_argument("--output", help="Arquivo de saída")
    log_parser.add_argument("--logs", nargs="+", default=["System", "Application"], help="Logs a exportar")
    log_parser.add_argument("--clear", help="Limpar log específico (requer Admin + backup)")

    # boot
    boot_parser = subparsers.add_parser("boot", help="Configuração de boot")
    boot_parser.add_argument("--backup-bcd", action="store_true", help="Backup BCD")
    boot_parser.add_argument("--restore-bcd", help="Restore BCD de arquivo")
    boot_parser.add_argument("--enum", action="store_true", help="Listar entradas BCD")
    boot_parser.add_argument("--verbose", action="store_true", help="BCD verbose")
    boot_parser.add_argument("--reagentc-info", action="store_true", help="Info WinRE")
    boot_parser.add_argument("--reagentc-enable", action="store_true", help="Habilitar WinRE")
    boot_parser.add_argument("--reagentc-disable", action="store_true", help="Desabilitar WinRE")

    # winfr
    winfr_parser = subparsers.add_parser("winfr", help="Windows File Recovery (requer Admin + winfr instalado)")
    winfr_parser.add_argument("--source", help="Drive origem (ex: C:) - obrigatório exceto com --check")
    winfr_parser.add_argument("--dest", help="Drive destino (ex: D:) - obrigatório exceto com --check")
    winfr_parser.add_argument("--mode", choices=["regular", "extensive", "segment"], default="regular", help="Modo de recuperação")
    winfr_parser.add_argument("--filter", nargs="+", help="Filtros de arquivo (ex: *.docx *.pdf)")
    winfr_parser.add_argument("--type", nargs="+", dest="file_types", help="Tipos de arquivo: doc, pic, vid, aud, zip, etc.")
    winfr_parser.add_argument("--check", action="store_true", help="Apenas verifica se winfr está instalado")

    # update
    upd_parser = subparsers.add_parser("update", help="Windows Update")
    upd_parser.add_argument("--log", action="store_true", help="Gerar log Windows Update")
    upd_parser.add_argument("--detect", action="store_true", help="Forçar detecção (legacy)")
    upd_parser.add_argument("--scan", action="store_true", help="USOClient StartScan")
    upd_parser.add_argument("--history", action="store_true", help="Histórico de updates")

    # drivers
    drv_parser = subparsers.add_parser("drivers", help="Drivers e dispositivos")
    drv_parser.add_argument("--list", action="store_true", help="Listar drivers no store")
    drv_parser.add_argument("--problems", action="store_true", help="Dispositivos com problema")

    # services
    svc_parser = subparsers.add_parser("services", help="Serviços")
    svc_parser.add_argument("--list", action="store_true", help="Listar serviços")
    svc_parser.add_argument("--filter", help="Filtrar por nome")
    svc_parser.add_argument("--status", help="Filtrar por status (Running/Stopped)")
    svc_parser.add_argument("--restart", help="Reiniciar serviço (requer Admin)")
    svc_parser.add_argument("--startup", nargs=2, metavar=("NAME", "TYPE"), help="Definir startup type")

    # network
    net_parser = subparsers.add_parser("network", help="Diagnóstico de rede")
    net_parser.add_argument("--test", help="Testar conexão (host:port ou host)")
    net_parser.add_argument("--flush-dns", action="store_true", help="Flush DNS cache")
    net_parser.add_argument("--reset-winsock", action="store_true", help="Reset Winsock (Admin)")
    net_parser.add_argument("--reset-tcpip", action="store_true", help="Reset TCP/IP (Admin)")
    net_parser.add_argument("--interfaces", action="store_true", help="Mostrar interfaces")

    # report
    rpt_parser = subparsers.add_parser("report", help="Relatório completo JSON")
    rpt_parser.add_argument("--json", action="store_true", help="Saída JSON")
    rpt_parser.add_argument("--output", help="Arquivo de saída")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    wm = WindowsMaintenance()

    try:
        if args.command == "health":
            report = wm.full_health_check()
            print(f"\n=== HEALTH CHECK ===")
            print(f"Status: {report.overall_status}")
            print(f"Timestamp: {report.timestamp}")
            if report.recommendations:
                print("\nRecomendações:")
                for r in report.recommendations:
                    print(f"  - {r}")
            if report.errors:
                print("\nErros:")
                for e in report.errors:
                    print(f"  - {e}")

        elif args.command == "disk":
            if args.health:
                health = wm.disk.get_storage_health()
                print(json.dumps(health, indent=2, ensure_ascii=False))
            elif args.analyze:
                result = wm.disk.analyze_volume(args.drive)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.repair:
                result = wm.disk.repair_volume(args.drive, offline=args.offline)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.optimize:
                result = wm.disk.optimize_volume(args.drive, args.operation)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                disks = wm.disk.get_disks()
                for d in disks:
                    print(f"{d.drive_letter} | {d.file_system} | {d.size_gb}GB | Free: {d.free_gb}GB | Health: {d.health_status} | Media: {d.media_type}")

        elif args.command == "system":
            results = {}
            if args.sfc:
                results["sfc"] = wm.system.run_sfc()
            if args.dism:
                results["dism_restore"] = wm.system.run_dism_restore_health()
            if args.dism_scan:
                results["dism_scan"] = wm.system.run_dism_scan_health()
            if args.dism_check:
                results["dism_check"] = wm.system.run_dism_check_health()
            if args.dism_cleanup:
                results["dism_cleanup"] = wm.system.run_dism_component_cleanup()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "optimize":
            if args.all:
                # Auto-detect media type
                disks = wm.disk.get_disks()
                target = next((d for d in disks if d.drive_letter.upper() == args.drive.upper()), None)
                if target and target.media_type == "SSD":
                    ops = ["Retrim", "TierOptimize"]
                else:
                    ops = ["Defrag", "FreespaceConsolidate", "TierOptimize"]
                results = {}
                for op in ops:
                    results[op] = wm.disk.optimize_volume(args.drive, op)
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                result = wm.disk.optimize_volume(args.drive, args.operation)
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "logs":
            if args.errors:
                result = wm.logs.export_errors(days=args.days, output=args.output, logs=args.logs)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.clear:
                result = wm.logs.clear_log(args.clear, backup_path=args.output)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                for log in args.logs:
                    info = wm.logs.get_log_info(log)
                    print(f"\n--- {log} ---")
                    print(info["output"])

        elif args.command == "boot":
            if args.backup_bcd:
                result = wm.boot.backup_bcd()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.restore_bcd:
                result = wm.boot.restore_bcd(args.restore_bcd)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.enum:
                result = wm.boot.enum_bcd(verbose=args.verbose)
                print(result["output"])
            elif args.reagentc_info:
                result = wm.boot.reagentc_info()
                print(result["output"])
            elif args.reagentc_enable:
                result = wm.boot.reagentc_enable()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.reagentc_disable:
                result = wm.boot.reagentc_disable()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("Use --backup-bcd, --restore-bcd, --enum, --reagentc-info, etc.")

        elif args.command == "update":
            results = {}
            if args.log:
                results["log"] = wm.update.get_update_log()
            if args.detect:
                results["detect"] = wm.update.force_detection()
            if args.scan:
                results["scan"] = wm.update.uso_client_scan()
            if args.history:
                results["history"] = wm.update.get_update_history()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "winfr":
            if args.check:
                result = wm.disk.winfr_check_installed()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                if not args.source or not args.dest:
                    print("Erro: --source e --dest são obrigatórios (use --check para apenas verificar instalação)")
                    return 1
                result = wm.disk.winfr_recover(
                    source=args.source,
                    dest=args.dest,
                    mode=args.mode,
                    filters=args.filter,
                    file_types=args.file_types
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "drivers":
            if args.list:
                result = wm.drivers.list_drivers()
                print(result["output"])
            elif args.problems:
                result = wm.drivers.find_problem_drivers()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("Use --list ou --problems")

        elif args.command == "services":
            if args.list:
                result = wm.services.list_services(name_filter=args.filter, status=args.status)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.restart:
                result = wm.services.restart_service(args.restart)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.startup:
                result = wm.services.set_startup(args.startup[0], args.startup[1])
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("Use --list, --restart, ou --startup")

        elif args.command == "network":
            results = {}
            if args.test:
                parts = args.test.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else None
                results["test"] = wm.network.test_connection(host, port)
            if args.flush_dns:
                results["flush_dns"] = wm.network.flush_dns()
            if args.reset_winsock:
                results["reset_winsock"] = wm.network.reset_winsock()
            if args.reset_tcpip:
                results["reset_tcpip"] = wm.network.reset_tcpip()
            if args.interfaces:
                results["interfaces"] = wm.network.show_interfaces()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "report":
            wm.generate_report(json_output=args.json, output_file=args.output)

    except AdminRequired as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERRO INESPERADO: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())