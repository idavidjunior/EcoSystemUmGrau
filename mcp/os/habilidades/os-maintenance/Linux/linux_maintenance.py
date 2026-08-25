#!/usr/bin/env python3
"""
Linux Native Maintenance Toolkit
Domina todas as ferramentas nativas do Linux para diagnóstico, reparo e otimização.
Zero dependências externas — apenas Linux built-ins (coreutils, util-linux, systemd, etc.).
"""

import subprocess
import json
import sys
import os
import argparse
import time
import platform
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum


class RootRequired(Exception):
    """Operação requer privilégios de root."""
    pass


class ToolNotFound(Exception):
    """Ferramenta nativa não encontrada."""
    pass


class DistroNotSupported(Exception):
    """Distro não suportada para operação específica."""
    pass


def run_cmd(cmd: List[str], capture: bool = True, timeout: int = 300, require_root: bool = False) -> Tuple[int, str, str]:
    """Executa comando e retorna (exit_code, stdout, stderr)."""
    if require_root and os.geteuid() != 0:
        # Tentar com sudo se não for root
        if shutil.which("sudo"):
            cmd = ["sudo", "-n"] + cmd
        else:
            raise RootRequired(f"Operação requer root. Execute com sudo ou como root.")

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


def is_root() -> bool:
    """Verifica se está rodando como root."""
    return os.geteuid() == 0


def require_root_check(op_name: str):
    """Levanta exceção se não for root e operação requer."""
    if not is_root() and not shutil.which("sudo"):
        raise RootRequired(f"Operação '{op_name}' requer root/sudo.")


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


@dataclass
class HealthReport:
    timestamp: str
    overall_status: str
    checks: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DiskHealth:
    """Gerencia saúde de disco: fsck, smartctl, fstrim, lsblk, nvme."""

    def __init__(self):
        self.tools = {
            "lsblk": shutil.which("lsblk"),
            "blkid": shutil.which("blkid"),
            "smartctl": shutil.which("smartctl"),
            "fsck": shutil.which("fsck"),
            "fstrim": shutil.which("fstrim"),
            "nvme": shutil.which("nvme"),
            "hdparm": shutil.which("hdparm"),
            "df": shutil.which("df"),
            "ls": shutil.which("ls"),
        }
        self.distro_pkg = self._detect_package_manager()

    def _detect_package_manager(self) -> str:
        for pm in ["apt", "dnf", "yum", "pacman", "zypper", "apk"]:
            if shutil.which(pm):
                return pm
        return "unknown"

    def get_disks(self) -> List[DiskInfo]:
        """Obtém info de todos os discos via lsblk."""
        if not self.tools["lsblk"]:
            raise ToolNotFound("lsblk não encontrado")

        # lsblk JSON output
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,MODEL,SERIAL,TYPE,PKNAME"]
        code, out, err = run_cmd(cmd)
        if code != 0:
            raise ToolNotFound(f"lsblk falhou: {err}")

        try:
            data = json.loads(out)
            disks = []
            for dev in data.get("blockdevices", []):
                if dev.get("type") == "disk":
                    disks.append(DiskInfo(
                        device=f"/dev/{dev['name']}",
                        size=dev.get("size", ""),
                        fstype=dev.get("fstype", ""),
                        mountpoint=dev.get("mountpoint", ""),
                        model=dev.get("model", ""),
                        serial=dev.get("serial", ""),
                    ))
                    # Partitions
                    for part in dev.get("children", []):
                        disks.append(DiskInfo(
                            device=f"/dev/{part['name']}",
                            size=part.get("size", ""),
                            fstype=part.get("fstype", ""),
                            mountpoint=part.get("mountpoint", ""),
                            model=part.get("model", ""),
                            serial=part.get("serial", ""),
                        ))
            # Enriquecer com SMART
            self._enrich_smart(disks)
            return disks
        except Exception as e:
            raise ToolNotFound(f"Falha ao parsear lsblk: {e}")

    def _enrich_smart(self, disks: List[DiskInfo]):
        if not self.tools["smartctl"]:
            return
        for d in disks:
            if d.device.startswith("/dev/") and not any(p in d.device for p in ["loop", "ram", "zram"]):
                code, out, err = run_cmd(["smartctl", "-i", d.device], timeout=30)
                if code == 0 and "SMART support is: Available" in out:
                    d.smart_available = True
                    # Quick health check
                    code2, out2, err2 = run_cmd(["smartctl", "-H", d.device], timeout=30)
                    if code2 == 0:
                        if "PASSED" in out2:
                            d.health = "PASSED"
                        elif "FAILED" in out2:
                            d.health = "FAILED"
                        else:
                            d.health = "Unknown"

    def smart_health(self, device: str) -> Dict[str, Any]:
        """SMART health completo."""
        if not self.tools["smartctl"]:
            raise ToolNotFound("smartctl não encontrado (instale smartmontools)")

        result = {"device": device, "timestamp": datetime.now().isoformat()}

        # Info básico
        code, out, err = run_cmd(["smartctl", "-i", device], timeout=30)
        result["info"] = {"exit_code": code, "output": out, "errors": err}

        # Health
        code, out, err = run_cmd(["smartctl", "-H", device], timeout=30)
        result["health"] = {"exit_code": code, "output": out, "errors": err}

        # Atributos
        code, out, err = run_cmd(["smartctl", "-A", device], timeout=30)
        result["attributes"] = {"exit_code": code, "output": out, "errors": err}

        # Self-test log
        code, out, err = run_cmd(["smartctl", "-l", "selftest", device], timeout=30)
        result["selftest_log"] = {"exit_code": code, "output": out, "errors": err}

        return result

    def smart_test(self, device: str, test_type: str = "short") -> Dict[str, Any]:
        """Inicia teste SMART (short/long/conveyance). Requer root."""
        require_root_check("smart_test")
        if not self.tools["smartctl"]:
            raise ToolNotFound("smartctl não encontrado")

        valid_types = ["short", "long", "conveyance", "select", "afterselect", "vendor"]
        if test_type not in valid_types:
            test_type = "short"

        code, out, err = run_cmd(["smartctl", "-t", test_type, device], timeout=60, require_root=True)
        return {"exit_code": code, "output": out, "errors": err, "test_type": test_type}

    def fsck_check(self, device: str, dry_run: bool = True, fstype: str = None) -> Dict[str, Any]:
        """Verifica filesystem (fsck). Dry-run por padrão."""
        if not self.tools["fsck"]:
            raise ToolNotFound("fsck não encontrado")

        # Verificar se montado
        mount_check = run_cmd(["findmnt", "-n", "-o", "TARGET", device])
        if mount_check[0] == 0 and mount_check[1].strip():
            if not dry_run:
                raise RootRequired(f"Dispositivo {device} está montado em {mount_check[1].strip()}. Desmonte antes de reparar.")

        cmd = ["fsck"]
        if dry_run:
            cmd.append("-n")
        if fstype:
            cmd.extend(["-t", fstype])
        cmd.append(device)

        code, out, err = run_cmd(cmd, timeout=600, require_root=not dry_run)
        return {"exit_code": code, "output": out, "errors": err, "dry_run": dry_run, "device": device}

    def trim_filesystem(self, mountpoint: str = "/") -> Dict[str, Any]:
        """Executa fstrim no ponto de montagem. Requer root para trim real."""
        if not self.tools["fstrim"]:
            raise ToolNotFound("fstrim não encontrado (util-linux)")

        # Verificar se filesystem suporta discard
        code, out, err = run_cmd(["findmnt", "-n", "-o", "FSTYPE,OPTIONS", mountpoint])
        supports_discard = False
        if code == 0 and "discard" in out:
            supports_discard = True

        # fstrim -v para verbose
        code, out, err = run_cmd(["fstrim", "-v", mountpoint], timeout=300, require_root=True)
        return {
            "mountpoint": mountpoint,
            "exit_code": code,
            "output": out,
            "errors": err,
            "discard_mounted": supports_discard
        }

    def trim_all(self) -> Dict[str, Any]:
        """fstrim em todos os filesystems montados que suportam."""
        if not self.tools["fstrim"]:
            raise ToolNotFound("fstrim não encontrado")

        code, out, err = run_cmd(["fstrim", "-av"], timeout=600, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def nvme_health(self, device: str = None) -> Dict[str, Any]:
        """NVMe health via nvme-cli."""
        if not self.tools["nvme"]:
            raise ToolNotFound("nvme-cli não encontrado")

        result = {"timestamp": datetime.now().isoformat()}

        if device:
            # Single device
            code, out, err = run_cmd(["nvme", "smart-log", device], timeout=30)
            result[device] = {"exit_code": code, "output": out, "errors": err}
        else:
            # List all
            code, out, err = run_cmd(["nvme", "list", "-o", "json"], timeout=30)
            if code == 0:
                try:
                    data = json.loads(out)
                    devices = data.get("Devices", [])
                    for dev in devices:
                        dev_path = dev.get("DevicePath", "")
                        if dev_path:
                            code2, out2, err2 = run_cmd(["nvme", "smart-log", dev_path], timeout=30)
                            result[dev_path] = {"exit_code": code2, "output": out2, "errors": err2}
                except Exception:
                    result["list_error"] = "Falha ao parsear nvme list"
            else:
                result["list_error"] = err

        return result

    def disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Uso de disco (df)."""
        if not self.tools["df"]:
            raise ToolNotFound("df não encontrado")

        code, out, err = run_cmd(["df", "-h", path], timeout=30)
        return {"exit_code": code, "output": out, "errors": err, "path": path}


class SystemdManager:
    """systemctl, journalctl, systemd-analyze."""

    def __init__(self):
        self.tools = {
            "systemctl": shutil.which("systemctl"),
            "journalctl": shutil.which("journalctl"),
            "systemd-analyze": shutil.which("systemd-analyze"),
        }

    def service_status(self, name: str = None) -> Dict[str, Any]:
        """Status de serviço(s)."""
        if not self.tools["systemctl"]:
            raise ToolNotFound("systemctl não encontrado")

        cmd = ["systemctl", "list-units", "--type=service", "--no-pager", "--no-legend"]
        if name:
            cmd.extend(["--grep", name])

        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def failed_services(self) -> Dict[str, Any]:
        """Lista serviços falhados."""
        if not self.tools["systemctl"]:
            raise ToolNotFound("systemctl não encontrado")

        cmd = ["systemctl", "list-units", "--type=service", "--state=failed", "--no-pager", "--no-legend"]
        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def enable_service(self, name: str, now: bool = False) -> Dict[str, Any]:
        """Habilita serviço. Requer root."""
        require_root_check("enable_service")
        if not self.tools["systemctl"]:
            raise ToolNotFound("systemctl não encontrado")

        cmd = ["systemctl", "enable"]
        if now:
            cmd.append("--now")
        cmd.append(name)
        code, out, err = run_cmd(cmd, timeout=30, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def disable_service(self, name: str, now: bool = False) -> Dict[str, Any]:
        """Desabilita serviço. Requer root."""
        require_root_check("disable_service")
        if not self.tools["systemctl"]:
            raise ToolNotFound("systemctl não encontrado")

        cmd = ["systemctl", "disable"]
        if now:
            cmd.append("--now")
        cmd.append(name)
        code, out, err = run_cmd(cmd, timeout=30, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def restart_service(self, name: str) -> Dict[str, Any]:
        """Reinicia serviço. Requer root."""
        require_root_check("restart_service")
        if not self.tools["systemctl"]:
            raise ToolNotFound("systemctl não encontrado")

        code, out, err = run_cmd(["systemctl", "restart", name], timeout=60, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def journal_errors(self, since: str = "7 days ago", priority: int = 3, unit: str = None) -> Dict[str, Any]:
        """Logs de erro do journalctl (priority 0-3 = emerg/alert/crit/err)."""
        if not self.tools["journalctl"]:
            raise ToolNotFound("journalctl não encontrado")

        cmd = ["journalctl", "-p", str(priority), "--since", since, "--no-pager"]
        if unit:
            cmd.extend(["-u", unit])
        cmd.extend(["-o", "json"])

        code, out, err = run_cmd(cmd, timeout=60)
        entries = []
        if code == 0:
            for line in out.strip().split('\n'):
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
        return {"exit_code": code, "count": len(entries), "entries": entries, "errors": err}

    def boot_analysis(self) -> Dict[str, Any]:
        """Análise de boot (systemd-analyze)."""
        if not self.tools["systemd-analyze"]:
            raise ToolNotFound("systemd-analyze não encontrado")

        results = {}

        # Time
        code, out, err = run_cmd(["systemd-analyze", "time"], timeout=30)
        results["time"] = {"exit_code": code, "output": out, "errors": err}

        # Blame
        code, out, err = run_cmd(["systemd-analyze", "blame", "--no-pager"], timeout=30)
        results["blame"] = {"exit_code": code, "output": out, "errors": err}

        # Critical chain
        code, out, err = run_cmd(["systemd-analyze", "critical-chain", "--no-pager"], timeout=30)
        results["critical_chain"] = {"exit_code": code, "output": out, "errors": err}

        return results


class KernelBoot:
    """Kernel, bootloader, initramfs, sysctl."""

    def __init__(self):
        self.tools = {
            "dmesg": shutil.which("dmesg"),
            "grub2-mkconfig": shutil.which("grub2-mkconfig") or shutil.which("grub-mkconfig") or shutil.which("update-grub"),
            "efibootmgr": shutil.which("efibootmgr"),
            "mkinitcpio": shutil.which("mkinitcpio"),
            "dracut": shutil.which("dracut"),
            "update-initramfs": shutil.which("update-initramfs"),
            "sysctl": shutil.which("sysctl"),
            "kmod": shutil.which("kmod"),
            "lsmod": shutil.which("lsmod"),
        }

    def dmesg_errors(self, level: str = "err,crit,alert,emerg") -> Dict[str, Any]:
        """Erros do kernel (dmesg)."""
        if not self.tools["dmesg"]:
            raise ToolNotFound("dmesg não encontrado")

        cmd = ["dmesg", "-T", "-l", level]
        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def sysctl_show(self, pattern: str = None) -> Dict[str, Any]:
        """Mostra parâmetros kernel."""
        if not self.tools["sysctl"]:
            raise ToolNotFound("sysctl não encontrado")

        cmd = ["sysctl", "-a"]
        if pattern:
            cmd = ["sysctl", pattern]
        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def sysctl_set(self, param: str, value: str) -> Dict[str, Any]:
        """Define parâmetro kernel (runtime). Requer root."""
        require_root_check("sysctl_set")
        if not self.tools["sysctl"]:
            raise ToolNotFound("sysctl não encontrado")

        code, out, err = run_cmd(["sysctl", "-w", f"{param}={value}"], timeout=30, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def grub_config(self, output: str = "/boot/grub/grub.cfg") -> Dict[str, Any]:
        """Regenera config GRUB. Requer root."""
        require_root_check("grub_config")
        if not self.tools["grub2-mkconfig"]:
            raise ToolNotFound("grub-mkconfig/update-grub não encontrado")

        cmd = [self.tools["grub2-mkconfig"], "-o", output]
        code, out, err = run_cmd(cmd, timeout=60, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def efibootmgr_list(self) -> Dict[str, Any]:
        """Lista entradas EFI boot. Requer root."""
        require_root_check("efibootmgr")
        if not self.tools["efibootmgr"]:
            raise ToolNotFound("efibootmgr não encontrado")

        code, out, err = run_cmd(["efibootmgr", "-v"], timeout=30, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def initramfs_rebuild(self, kernel: str = "all") -> Dict[str, Any]:
        """Reconstrói initramfs. Requer root."""
        require_root_check("initramfs_rebuild")

        # Detectar ferramenta
        if self.tools["mkinitcpio"]:
            cmd = ["mkinitcpio", "-P"] if kernel == "all" else ["mkinitcpio", "-p", kernel]
        elif self.tools["dracut"]:
            cmd = ["dracut", "--force", "--regenerate-all"] if kernel == "all" else ["dracut", "--force", "-k", kernel]
        elif self.tools["update-initramfs"]:
            cmd = ["update-initramfs", "-u", "-k", "all"] if kernel == "all" else ["update-initramfs", "-u", "-k", kernel]
        else:
            raise ToolNotFound("Nenhuma ferramenta initramfs encontrada (mkinitcpio/dracut/update-initramfs)")

        code, out, err = run_cmd(cmd, timeout=300, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def loaded_modules(self) -> Dict[str, Any]:
        """Módulos carregados."""
        if not self.tools["lsmod"]:
            raise ToolNotFound("lsmod não encontrado")

        code, out, err = run_cmd(["lsmod"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}


class PackageManager:
    """Gerenciamento de pacotes multi-distro."""

    def __init__(self):
        self.pm = self._detect()
        self.tools = {pm: shutil.which(pm) for pm in ["apt", "apt-get", "dnf", "yum", "pacman", "zypper", "apk", "flatpak", "snap"]}

    def _detect(self) -> str:
        for pm in ["apt", "dnf", "yum", "pacman", "zypper", "apk"]:
            if shutil.which(pm):
                return pm
        return "unknown"

    def update_check(self) -> Dict[str, Any]:
        """Verifica atualizações disponíveis (dry-run)."""
        if self.pm == "unknown":
            raise DistroNotSupported("Package manager não detectado")

        cmds = {
            "apt": ["apt", "update"],
            "dnf": ["dnf", "check-update"],
            "yum": ["yum", "check-update"],
            "pacman": ["pacman", "-Qu"],
            "zypper": ["zypper", "list-updates"],
            "apk": ["apk", "version", "-l", "<"],
        }

        if self.pm not in cmds:
            raise DistroNotSupported(f"PM {self.pm} não suportado para check")

        code, out, err = run_cmd(cmds[self.pm], timeout=120)
        return {"pm": self.pm, "exit_code": code, "output": out, "errors": err, "updates_available": code == 0 and bool(out.strip())}

    def upgrade(self, dry_run: bool = True) -> Dict[str, Any]:
        """Atualiza sistema. Requer root para execução real."""
        if self.pm == "unknown":
            raise DistroNotSupported("Package manager não detectado")

        if dry_run:
            return self.update_check()

        require_root_check("upgrade")

        cmds = {
            "apt": ["apt", "full-upgrade", "-y"],
            "dnf": ["dnf", "upgrade", "-y"],
            "yum": ["yum", "update", "-y"],
            "pacman": ["pacman", "-Syu", "--noconfirm"],
            "zypper": ["zypper", "dup", "-y"],
            "apk": ["apk", "upgrade"],
        }

        if self.pm not in cmds:
            raise DistroNotSupported(f"PM {self.pm} não suportado para upgrade")

        code, out, err = run_cmd(cmds[self.pm], timeout=600, require_root=True)
        return {"pm": self.pm, "exit_code": code, "output": out, "errors": err}

    def clean_cache(self) -> Dict[str, Any]:
        """Limpa cache de pacotes. Requer root."""
        require_root_check("clean_cache")

        cmds = {
            "apt": ["apt", "clean"],
            "dnf": ["dnf", "clean", "all"],
            "yum": ["yum", "clean", "all"],
            "pacman": ["pacman", "-Sc", "--noconfirm"],
            "zypper": ["zypper", "clean", "-a"],
            "apk": ["apk", "cache", "clean"],
        }

        if self.pm not in cmds:
            raise DistroNotSupported(f"PM {self.pm} não suportado para clean")

        code, out, err = run_cmd(cmds[self.pm], timeout=120, require_root=True)
        return {"pm": self.pm, "exit_code": code, "output": out, "errors": err}

    def verify_packages(self) -> Dict[str, Any]:
        """Verifica integridade de pacotes instalados."""
        cmds = {
            "apt": ["debsums", "-s"],  # requer debsums instalado
            "dnf": ["rpm", "-Va"],
            "yum": ["rpm", "-Va"],
            "pacman": ["pacman", "-Qk"],
            "zypper": ["rpm", "-Va"],
            "apk": ["apk", "verify"],
        }

        if self.pm not in cmds:
            return {"error": f"Verificação não implementada para {self.pm}"}

        # Check if tool exists
        if self.pm in ["apt"] and not shutil.which("debsums"):
            return {"error": "debsums não instalado (apt install debsums)"}

        code, out, err = run_cmd(cmds[self.pm], timeout=300)
        return {"pm": self.pm, "exit_code": code, "output": out, "errors": err}


class LogManager:
    """journalctl, auditd, logrotate."""

    def __init__(self):
        self.tools = {
            "journalctl": shutil.which("journalctl"),
            "ausearch": shutil.which("ausearch"),
            "aureport": shutil.which("aureport"),
            "logrotate": shutil.which("logrotate"),
            "last": shutil.which("last"),
        }

    def export_errors(self, days: int = 7, priority: int = 3, output: str = None, unit: str = None) -> Dict[str, Any]:
        """Exporta erros do journalctl."""
        if not self.tools["journalctl"]:
            raise ToolNotFound("journalctl não encontrado")

        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cmd = ["journalctl", "-p", str(priority), "--since", since, "--no-pager"]
        if unit:
            cmd.extend(["-u", unit])
        if output:
            cmd.extend(["-o", "json"])

        code, out, err = run_cmd(cmd, timeout=60)

        if output and code == 0:
            Path(output).write_text(out, encoding="utf-8")

        return {"exit_code": code, "output": out if not output else f"Salvo em {output}", "errors": err}

    def audit_summary(self) -> Dict[str, Any]:
        """Resumo de auditoria (aureport). Requer root para logs completos."""
        if not self.tools["aureport"]:
            raise ToolNotFound("aureport não encontrado (auditd)")

        code, out, err = run_cmd(["aureport", "--summary"], timeout=60, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def login_history(self, failed_only: bool = False) -> Dict[str, Any]:
        """Histórico de login (last/lastb)."""
        cmd = ["lastb"] if failed_only else ["last"]
        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}


class NetworkDiagnostics:
    """ip, ss, nmcli, dig, curl."""

    def __init__(self):
        self.tools = {
            "ip": shutil.which("ip"),
            "ss": shutil.which("ss"),
            "nmcli": shutil.which("nmcli"),
            "dig": shutil.which("dig"),
            "curl": shutil.which("curl"),
            "ping": shutil.which("ping"),
            "traceroute": shutil.which("traceroute"),
            "mtr": shutil.which("mtr"),
            "resolvectl": shutil.which("resolvectl"),
        }

    def interfaces(self) -> Dict[str, Any]:
        """Interfaces de rede."""
        if not self.tools["ip"]:
            raise ToolNotFound("ip não encontrado (iproute2)")

        code, out, err = run_cmd(["ip", "-j", "address", "show"], timeout=30)
        if code == 0:
            try:
                return {"exit_code": code, "interfaces": json.loads(out), "errors": err}
            except Exception:
                pass
        return {"exit_code": code, "output": out, "errors": err}

    def sockets(self, listening: bool = True, tcp: bool = True, udp: bool = True) -> Dict[str, Any]:
        """Sockets (ss)."""
        if not self.tools["ss"]:
            raise ToolNotFound("ss não encontrado (iproute2)")

        cmd = ["ss", "-n"]
        if listening:
            cmd.append("-l")
        if tcp:
            cmd.append("-t")
        if udp:
            cmd.append("-u")
        cmd.extend(["-p", "-e"])  # process info, extended

        code, out, err = run_cmd(cmd, timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def dns_lookup(self, domain: str, record: str = "A") -> Dict[str, Any]:
        """DNS lookup (dig)."""
        if not self.tools["dig"]:
            raise ToolNotFound("dig não encontrado (bind-utils/dnsutils)")

        code, out, err = run_cmd(["dig", "+short", record, domain], timeout=30)
        return {"exit_code": code, "output": out.strip(), "errors": err, "domain": domain, "record": record}

    def http_check(self, url: str, timeout_sec: int = 10) -> Dict[str, Any]:
        """HTTP check (curl)."""
        if not self.tools["curl"]:
            raise ToolNotFound("curl não encontrado")

        code, out, err = run_cmd(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout_sec), url], timeout=timeout_sec + 5)
        return {"exit_code": code, "http_code": out.strip(), "errors": err, "url": url}

    def ping_test(self, target: str, count: int = 4) -> Dict[str, Any]:
        """Ping test."""
        if not self.tools["ping"]:
            raise ToolNotFound("ping não encontrado")

        code, out, err = run_cmd(["ping", "-c", str(count), target], timeout=30)
        return {"exit_code": code, "output": out, "errors": err, "target": target}

    def firewall_status(self) -> Dict[str, Any]:
        """Status firewall (nftables/iptables/ufw/firewalld)."""
        results = {}

        # nftables
        if shutil.which("nft"):
            code, out, err = run_cmd(["nft", "list", "ruleset"], timeout=30)
            results["nftables"] = {"exit_code": code, "output": out, "errors": err}

        # iptables
        if shutil.which("iptables"):
            code, out, err = run_cmd(["iptables", "-L", "-n", "-v"], timeout=30)
            results["iptables"] = {"exit_code": code, "output": out, "errors": err}

        # ufw
        if shutil.which("ufw"):
            code, out, err = run_cmd(["ufw", "status", "verbose"], timeout=30)
            results["ufw"] = {"exit_code": code, "output": out, "errors": err}

        # firewalld
        if shutil.which("firewall-cmd"):
            code, out, err = run_cmd(["firewall-cmd", "--list-all"], timeout=30)
            results["firewalld"] = {"exit_code": code, "output": out, "errors": err}

        return results


class ProcessResources:
    """ps, top, vmstat, free, cgroups."""

    def __init__(self):
        self.tools = {
            "ps": shutil.which("ps"),
            "top": shutil.which("top"),
            "vmstat": shutil.which("vmstat"),
            "iostat": shutil.which("iostat"),
            "mpstat": shutil.which("mpstat"),
            "free": shutil.which("free"),
            "lsof": shutil.which("lsof"),
        }

    def top_processes(self, count: int = 20, sort: str = "cpu") -> Dict[str, Any]:
        """Top processos (ps)."""
        if not self.tools["ps"]:
            raise ToolNotFound("ps não encontrado (procps)")

        sort_map = {"cpu": "-%cpu", "mem": "-%mem", "time": "-time", "pid": "pid"}
        sort_key = sort_map.get(sort, "-%cpu")

        cmd = ["ps", "aux", "--sort", sort_key]
        code, out, err = run_cmd(cmd, timeout=30)

        # Parse output
        processes = []
        if code == 0:
            lines = out.strip().split('\n')
            if len(lines) > 1:
                headers = lines[0].split()
                for line in lines[1:count+1]:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        proc = dict(zip(headers[:10], parts[:10]))
                        proc["command"] = parts[10] if len(parts) > 10 else ""
                        processes.append(proc)

        return {"exit_code": code, "processes": processes, "errors": err}

    def memory_info(self) -> Dict[str, Any]:
        """Info de memória (free + /proc/meminfo)."""
        results = {}

        if self.tools["free"]:
            code, out, err = run_cmd(["free", "-h"], timeout=10)
            results["free"] = {"exit_code": code, "output": out, "errors": err}

        # /proc/meminfo
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = {}
                for line in f:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meminfo[k.strip()] = v.strip()
            results["meminfo"] = meminfo
        except Exception as e:
            results["meminfo_error"] = str(e)

        return results

    def cpu_info(self) -> Dict[str, Any]:
        """Info CPU (/proc/cpuinfo + lscpu)."""
        results = {}

        if shutil.which("lscpu"):
            code, out, err = run_cmd(["lscpu", "-J"], timeout=10)
            if code == 0:
                try:
                    results["lscpu"] = json.loads(out)
                except Exception:
                    results["lscpu_raw"] = out

        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = {}
                current = {}
                for line in f:
                    if not line.strip():
                        if current:
                            cpuinfo[f"cpu{len(cpuinfo)}"] = current
                            current = {}
                        continue
                    if ":" in line:
                        k, v = line.split(":", 1)
                        current[k.strip()] = v.strip()
                if current:
                    cpuinfo[f"cpu{len(cpuinfo)}"] = current
            results["cpuinfo"] = cpuinfo
        except Exception as e:
            results["cpuinfo_error"] = str(e)

        return results

    def vmstat_stats(self, interval: int = 1, count: int = 5) -> Dict[str, Any]:
        """Estatísticas VM (vmstat)."""
        if not self.tools["vmstat"]:
            raise ToolNotFound("vmstat não encontrado (sysstat)")

        code, out, err = run_cmd(["vmstat", str(interval), str(count)], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}

    def disk_io_stats(self, interval: int = 1, count: int = 5) -> Dict[str, Any]:
        """Estatísticas I/O (iostat)."""
        if not self.tools["iostat"]:
            raise ToolNotFound("iostat não encontrado (sysstat)")

        code, out, err = run_cmd(["iostat", "-x", str(interval), str(count)], timeout=60)
        return {"exit_code": code, "output": out, "errors": err}


class HardwareSensors:
    """lscpu, lspci, lsusb, sensors, dmidecode."""

    def __init__(self):
        self.tools = {
            "lscpu": shutil.which("lscpu"),
            "lspci": shutil.which("lspci"),
            "lsusb": shutil.which("lsusb"),
            "sensors": shutil.which("sensors"),
            "dmidecode": shutil.which("dmidecode"),
            "lshw": shutil.which("lshw"),
        }

    def sensors_read(self) -> Dict[str, Any]:
        """Sensores (lm-sensors)."""
        if not self.tools["sensors"]:
            raise ToolNotFound("sensors não encontrado (lm-sensors)")

        code, out, err = run_cmd(["sensors", "-j"], timeout=30)
        if code == 0:
            try:
                return {"exit_code": code, "sensors": json.loads(out), "errors": err}
            except Exception:
                pass
        return {"exit_code": code, "output": out, "errors": err}

    def pci_devices(self) -> Dict[str, Any]:
        """Dispositivos PCI."""
        if not self.tools["lspci"]:
            raise ToolNotFound("lspci não encontrado (pciutils)")

        code, out, err = run_cmd(["lspci", "-v"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def usb_devices(self) -> Dict[str, Any]:
        """Dispositivos USB."""
        if not self.tools["lsusb"]:
            raise ToolNotFound("lsusb não encontrado (usbutils)")

        code, out, err = run_cmd(["lsusb", "-v"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def smbios_info(self) -> Dict[str, Any]:
        """SMBIOS/DMI (dmidecode). Requer root."""
        require_root_check("smbios_info")
        if not self.tools["dmidecode"]:
            raise ToolNotFound("dmidecode não encontrado")

        code, out, err = run_cmd(["dmidecode", "-t", "system,bios,baseboard,chassis,processor,memory"], timeout=60, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}


class SecurityHardening:
    """SSH, firewall, audit, apparmor/selinux."""

    def __init__(self):
        self.tools = {
            "sshd": shutil.which("sshd"),
            "ssh": shutil.which("ssh"),
            "ufw": shutil.which("ufw"),
            "firewall-cmd": shutil.which("firewall-cmd"),
            "nft": shutil.which("nft"),
            "iptables": shutil.which("iptables"),
            "aa-status": shutil.which("aa-status"),
            "sestatus": shutil.which("sestatus"),
            "lynis": shutil.which("lynis"),
            "rkhunter": shutil.which("rkhunter"),
        }

    def ssh_config_check(self) -> Dict[str, Any]:
        """Verifica config SSH (/etc/ssh/sshd_config)."""
        config_path = "/etc/ssh/sshd_config"
        if not Path(config_path).exists():
            return {"error": f"{config_path} não encontrado"}

        try:
            content = Path(config_path).read_text()
            # Verificações básicas de hardening
            checks = {
                "PermitRootLogin": "no" in content.lower() or "prohibit-password" in content.lower(),
                "PasswordAuthentication": "no" in content.lower(),
                "PubkeyAuthentication": "yes" in content.lower(),
                "Protocol": "2" in content,
                "MaxAuthTries": any("maxauthtries" in line.lower() and int(line.split()[-1]) <= 3 for line in content.split('\n') if "maxauthtries" in line.lower()),
                "AllowUsers": "allowusers" in content.lower(),
                "DenyUsers": "denyusers" in content.lower(),
                "X11Forwarding": "no" in content.lower(),
                "PermitEmptyPasswords": "no" in content.lower(),
            }
            return {"config_path": config_path, "checks": checks, "content": content}
        except Exception as e:
            return {"error": str(e)}

    def apparmor_status(self) -> Dict[str, Any]:
        """Status AppArmor."""
        if not self.tools["aa-status"]:
            raise ToolNotFound("aa-status não encontrado (apparmor)")

        code, out, err = run_cmd(["aa-status"], timeout=30, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}

    def selinux_status(self) -> Dict[str, Any]:
        """Status SELinux."""
        if not self.tools["sestatus"]:
            raise ToolNotFound("sestatus não encontrado (selinux)")

        code, out, err = run_cmd(["sestatus", "-v"], timeout=30)
        return {"exit_code": code, "output": out, "errors": err}

    def lynis_audit(self) -> Dict[str, Any]:
        """Lynis security audit. Requer root."""
        require_root_check("lynis_audit")
        if not self.tools["lynis"]:
            raise ToolNotFound("lynis não encontrado")

        code, out, err = run_cmd(["lynis", "audit", "system", "--quick"], timeout=300, require_root=True)
        return {"exit_code": code, "output": out, "errors": err}


class LinuxMaintenance:
    """Orquestrador principal."""

    def __init__(self):
        self.disk = DiskHealth()
        self.systemd = SystemdManager()
        self.kernel = KernelBoot()
        self.packages = PackageManager()
        self.logs = LogManager()
        self.network = NetworkDiagnostics()
        self.processes = ProcessResources()
        self.hardware = HardwareSensors()
        self.security = SecurityHardening()

    def full_health_check(self) -> HealthReport:
        """Health check completo não-invasivo (sem root)."""
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            overall_status="Checking..."
        )

        # Discos
        try:
            disks = self.disk.get_disks()
            report.checks["disks"] = [asdict(d) for d in disks]
            failed = [d for d in disks if d.health == "FAILED"]
            if failed:
                report.recommendations.append(f"Discos com SMART FAILED: {[d.device for d in failed]}")
            unknown = [d for d in disks if d.health == "Unknown" and d.smart_available]
            if unknown:
                report.recommendations.append(f"Discos com SMART disponível mas status desconhecido: {[d.device for d in unknown]}")
        except Exception as e:
            report.errors.append(f"Disk check: {e}")

        # Serviços falhados
        try:
            failed = self.systemd.failed_services()
            if failed["exit_code"] == 0 and failed["output"].strip():
                report.checks["failed_services"] = failed["output"]
                report.recommendations.append("Serviços systemd em estado failed detectados")
        except Exception as e:
            report.errors.append(f"Systemd check: {e}")

        # Erros kernel recentes
        try:
            kernel_errs = self.kernel.dmesg_errors()
            if kernel_errs["exit_code"] == 0 and kernel_errs["output"].strip():
                report.checks["kernel_errors"] = "Erros recentes no dmesg"
                report.recommendations.append("Verifique dmesg para erros de kernel recentes")
        except Exception as e:
            report.errors.append(f"Kernel check: {e}")

        # Updates disponíveis
        try:
            updates = self.packages.update_check()
            if updates.get("updates_available"):
                report.checks["package_updates"] = "Atualizações disponíveis"
                report.recommendations.append(f"Atualizações de pacotes disponíveis ({self.packages.pm})")
        except Exception as e:
            report.errors.append(f"Package check: {e}")

        # Memória
        try:
            mem = self.processes.memory_info()
            report.checks["memory"] = "OK"
        except Exception as e:
            report.errors.append(f"Memory check: {e}")

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

        # System info
        data["system_info"] = {
            "os": platform.platform(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "distro": self._get_distro_info(),
            "is_root": is_root(),
            "package_manager": self.packages.pm,
            "tools_available": {k: v is not None for k, v in self.disk.tools.items()}
        }

        if json_output:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            if output_file:
                Path(output_file).write_text(json_str, encoding="utf-8")
                print(f"Relatório salvo em: {output_file}")
            else:
                print(json_str)

        return data

    def _get_distro_info(self) -> Dict[str, str]:
        info = {}
        # /etc/os-release
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        info[k.lower()] = v.strip('"')
        except Exception:
            pass
        return info


def main():
    parser = argparse.ArgumentParser(
        description="Linux Native Maintenance Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python linux_maintenance.py health
  python linux_maintenance.py disk --device /dev/sda --smart
  python linux_maintenance.py disk --trim /
  python linux_maintenance.py system --services --kernel
  python linux_maintenance.py logs --errors --days 7
  python linux_maintenance.py boot --grub --initramfs
  python linux_maintenance.py network --interfaces --dns google.com
  python linux_maintenance.py hardware --sensors --pci
  python linux_maintenance.py security --ssh --apparmor
  python linux_maintenance.py report --json --output report.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando principal")

    # health
    subparsers.add_parser("health", help="Health check completo (não invasivo)")

    # disk
    disk_parser = subparsers.add_parser("disk", help="Operações de disco")
    disk_parser.add_argument("--device", help="Device (ex: /dev/sda)")
    disk_parser.add_argument("--smart", action="store_true", help="SMART health")
    disk_parser.add_argument("--smart-test", choices=["short", "long", "conveyance"], help="Iniciar teste SMART")
    disk_parser.add_argument("--fsck", action="store_true", help="Verificar filesystem (dry-run)")
    disk_parser.add_argument("--repair", action="store_true", help="Reparar filesystem (requer root + umount)")
    disk_parser.add_argument("--fstype", help "Tipo de filesystem (ext4, xfs, etc.)")
    disk_parser.add_argument("--trim", help="fstrim no mountpoint")
    disk_parser.add_argument("--trim-all", action="store_true", help="fstrim em todos")
    disk_parser.add_argument("--nvme", action="store_true", help="NVMe health")
    disk_parser.add_argument("--usage", help="df no path")

    # system
    sys_parser = subparsers.add_parser("system", help="Systemd, kernel, pacotes")
    sys_parser.add_argument("--services", action="store_true", help="Lista serviços")
    sys_parser.add_argument("--failed", action="store_true", help="Serviços falhados")
    sys_parser.add_argument("--kernel", action="store_true", help="Kernel (dmesg, sysctl)")
    sys_parser.add_argument("--packages", action="store_true", help="Verifica updates")
    sys_parser.add_argument("--upgrade", action="store_true", help="Upgrade (dry-run por padrão)")
    sys_parser.add_argument("--clean", action="store_true", help="Limpa cache pacotes")

    # logs
    log_parser = subparsers.add_parser("logs", help="Logs (journalctl, audit)")
    log_parser.add_argument("--errors", action="store_true", help="Erros recentes")
    log_parser.add_argument("--days", type=int, default=7, help="Dias")
    log_parser.add_argument("--priority", type=int, default=3, help="Priority (0-3)")
    log_parser.add_argument("--unit", help="Unit systemd")
    log_parser.add_argument("--output", help="Arquivo saída")
    log_parser.add_argument("--audit", action="store_true", help="Resumo auditd")
    log_parser.add_argument("--logins", action="store_true", help="Histórico login")

    # boot
    boot_parser = subparsers.add_parser("boot", help="Bootloader, initramfs")
    boot_parser.add_argument("--grub", action="store_true", help="Regenera GRUB")
    boot_parser.add_argument("--efi", action="store_true", help="Lista EFI boot entries")
    boot_parser.add_argument("--initramfs", action="store_true", help="Reconstrói initramfs")
    boot_parser.add_argument("--kernel", help="Kernel version para initramfs")
    boot_parser.add_argument("--dmesg", action="store_true", help="Erros dmesg")
    boot_parser.add_argument("--modules", action="store_true", help="Módulos carregados")

    # network
    net_parser = subparsers.add_parser("network", help="Rede")
    net_parser.add_argument("--interfaces", action="store_true", help="Interfaces")
    net_parser.add_argument("--sockets", action="store_true", help="Sockets listening")
    net_parser.add_argument("--dns", help "DNS lookup domain")
    net_parser.add_argument("--http", help "HTTP check URL")
    net_parser.add_argument("--ping", help "Ping target")
    net_parser.add_argument("--firewall", action="store_true", help="Status firewall")

    # hardware
    hw_parser = subparsers.add_parser("hardware", help="Hardware & sensores")
    hw_parser.add_argument("--sensors", action="store_true", help="lm-sensors")
    hw_parser.add_argument("--pci", action="store_true", help "PCI devices")
    hw_parser.add_argument("--usb", action="store_true", help "USB devices")
    hw_parser.add_argument("--smbios", action="store_true", help "SMBIOS (root)")
    hw_parser.add_argument("--cpu", action="store_true", help "CPU info")

    # security
    sec_parser = subparsers.add_parser("security", help="Segurança")
    sec_parser.add_argument("--ssh", action="store_true", help "SSH config check")
    sec_parser.add_argument("--apparmor", action="store_true", help "AppArmor status")
    sec_parser.add_argument("--selinux", action="store_true", help "SELinux status")
    sec_parser.add_argument("--lynis", action="store_true", help "Lynis audit (root)")

    # report
    rpt_parser = subparsers.add_parser("report", help="Relatório completo JSON")
    rpt_parser.add_argument("--json", action="store_true", help="Saída JSON")
    rpt_parser.add_argument("--output", help="Arquivo de saída")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    lm = LinuxMaintenance()

    try:
        if args.command == "health":
            report = lm.full_health_check()
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
            if args.smart and args.device:
                result = lm.disk.smart_health(args.device)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.smart_test and args.device:
                result = lm.disk.smart_test(args.device, args.smart_test)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.fsck and args.device:
                result = lm.disk.fsck_check(args.device, dry_run=not args.repair, fstype=args.fstype)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.trim:
                result = lm.disk.trim_filesystem(args.trim)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.trim_all:
                result = lm.disk.trim_all()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.nvme:
                result = lm.disk.nvme_health(args.device)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.usage:
                result = lm.disk.disk_usage(args.usage)
                print(result["output"])
            else:
                disks = lm.disk.get_disks()
                for d in disks:
                    smart = f" | SMART: {d.health}" if d.smart_available else ""
                    print(f"{d.device} | {d.size} | {d.fstype} | {d.mountpoint} | {d.model}{smart}")

        elif args.command == "system":
            results = {}
            if args.services:
                results["services"] = lm.systemd.service_status()
            if args.failed:
                results["failed"] = lm.systemd.failed_services()
            if args.kernel:
                results["dmesg_errors"] = lm.kernel.dmesg_errors()
                results["sysctl"] = lm.kernel.sysctl_show()
            if args.packages:
                results["updates"] = lm.packages.update_check()
            if args.upgrade:
                results["upgrade"] = lm.packages.upgrade(dry_run=True)
            if args.clean:
                results["clean"] = lm.packages.clean_cache()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "logs":
            if args.errors:
                result = lm.logs.export_errors(days=args.days, priority=args.priority, output=args.output, unit=args.unit)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.audit:
                result = lm.logs.audit_summary()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.logins:
                result = lm.logs.login_history(failed_only=False)
                print(result["output"])
            else:
                print("Use --errors, --audit, ou --logins")

        elif args.command == "boot":
            results = {}
            if args.grub:
                results["grub"] = lm.kernel.grub_config()
            if args.efi:
                results["efi"] = lm.kernel.efibootmgr_list()
            if args.initramfs:
                results["initramfs"] = lm.kernel.initramfs_rebuild(args.kernel or "all")
            if args.dmesg:
                results["dmesg"] = lm.kernel.dmesg_errors()
            if args.modules:
                results["modules"] = lm.kernel.loaded_modules()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "network":
            results = {}
            if args.interfaces:
                results["interfaces"] = lm.network.interfaces()
            if args.sockets:
                results["sockets"] = lm.network.sockets()
            if args.dns:
                results["dns"] = lm.network.dns_lookup(args.dns)
            if args.http:
                results["http"] = lm.network.http_check(args.http)
            if args.ping:
                results["ping"] = lm.network.ping_test(args.ping)
            if args.firewall:
                results["firewall"] = lm.network.firewall_status()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "hardware":
            results = {}
            if args.sensors:
                results["sensors"] = lm.hardware.sensors_read()
            if args.pci:
                results["pci"] = lm.hardware.pci_devices()
            if args.usb:
                results["usb"] = lm.hardware.usb_devices()
            if args.smbios:
                results["smbios"] = lm.hardware.smbios_info()
            if args.cpu:
                results["cpu"] = lm.processes.cpu_info()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "security":
            results = {}
            if args.ssh:
                results["ssh"] = lm.security.ssh_config_check()
            if args.apparmor:
                results["apparmor"] = lm.security.apparmor_status()
            if args.selinux:
                results["selinux"] = lm.security.selinux_status()
            if args.lynis:
                results["lynis"] = lm.security.lynis_audit()
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif args.command == "report":
            lm.generate_report(json_output=args.json, output_file=args.output)

    except RootRequired as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    except ToolNotFound as e:
        print(f"FERRAMENTA NÃO ENCONTRADA: {e}", file=sys.stderr)
        return 3
    except DistroNotSupported as e:
        print(f"DISTRO NÃO SUPORTADA: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"ERRO INESPERADO: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())