#!/usr/bin/env python3
"""
EcoSystemUmGrau - Universal Bridge Core
Define ConnectionEndpoint e health check methods para todos protocolos
"""

import subprocess
import json
import socket
import urllib.request
import urllib.error
import ssl
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any


@dataclass
class ConnectionEndpoint:
    """Define um endpoint de conexão multi-protocolo"""
    id: str
    type: str  # adb_tcp, adb_usb, tailscale, ssh, http, serial, websocket, mqtt, dns, vpn
    name: str
    primary: bool
    config: Dict[str, Any]
    health_check_interval: int = 15
    timeout: int = 10
    max_retries: int = 3
    fallback_chain: List[str] = None  # IDs of fallback endpoints

    def __post_init__(self):
        if self.fallback_chain is None:
            self.fallback_chain = []


def check_adb_usb(adb_path: str, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión ADB USB"""
    try:
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True, text=True, timeout=timeout
        )
        devices = []
        for line in result.stdout.strip().split('\n')[1:]:
            if 'device' in line and not line.startswith('*'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
        return len(devices) > 0, {"devices": devices, "count": len(devices)}
    except Exception as e:
        return False, {"error": str(e)}


def check_adb_tcp(adb_path: str, device_ips: List[str], timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión ADB TCP/IP"""
    connected = []
    for ip_port in device_ips:
        try:
            result = subprocess.run(
                [adb_path, "connect", ip_port],
                capture_output=True, text=True, timeout=timeout
            )
            if "connected" in result.stdout.lower() or "already" in result.stdout.lower():
                connected.append(ip_port)
        except:
            continue
    return len(connected) > 0, {"connected": connected, "count": len(connected)}


def check_tailscale(timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión Tailscale"""
    try:
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True, text=True, timeout=timeout
        )
        active_nodes = []
        for line in result.stdout.strip().split('\n'):
            if 'active' in line:
                parts = line.split()
                if len(parts) >= 2:
                    active_nodes.append({"ip": parts[0], "name": parts[1]})
        return len(active_nodes) > 0, {"active_nodes": active_nodes, "count": len(active_nodes)}
    except Exception as e:
        return False, {"error": str(e)}


def check_ssh(host: str, port: int, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión SSH (port check)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return True, {"host": host, "port": port, "reachable": True}
        return False, {"host": host, "port": port, "reachable": False}
    except Exception as e:
        return False, {"host": host, "port": port, "error": str(e)}


def check_http(url: str, expected_status: int, timeout: int) -> Tuple[bool, Dict]:
    """Verifica endpoint HTTP"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            status = response.getcode()
            return status == expected_status, {"status": status, "expected": expected_status}
    except urllib.error.HTTPError as e:
        return False, {"status": e.code, "expected": expected_status, "error": str(e)}
    except Exception as e:
        return False, {"error": str(e), "url": url}


def check_dns(resolvers: List[str], test_domain: str) -> Tuple[bool, Dict]:
    """Verifica resolução DNS"""
    successes = []
    try:
        socket.getaddrinfo(test_domain, None)
        for resolver in resolvers:
            try:
                socket.setdefaulttimeout(3)
                # Simple reachability test
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.connect((resolver, 53))
                sock.close()
                successes.append(resolver)
            except:
                continue
        return len(successes) > 0, {"resolvers_working": successes, "total_resolvers": len(resolvers)}
    except Exception as e:
        return False, {"error": str(e)}


def check_mqtt(host: str, port: int, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión MQTT (port check)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return True, {"host": host, "port": port, "reachable": True}
        return False, {"host": host, "port": port, "reachable": False}
    except Exception as e:
        return False, {"host": host, "port": port, "error": str(e)}


def check_websocket(url: str, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión WebSocket (TCP check)"""
    match = re.match(r'wss?://([^:/]+)(?::(\d+))?', url)
    if match:
        host = match.group(1)
        port = int(match.group(2)) if match.group(2) else (443 if url.startswith("wss") else 80)
    else:
        return False, {"error": "Invalid URL format", "url": url}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return True, {"host": host, "port": port, "reachable": True}
        return False, {"host": host, "port": port, "reachable": False}
    except Exception as e:
        return False, {"error": str(e)}


def check_vpn(vpn_type: str, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión VPN"""
    try:
        result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=10)
        if vpn_type == "openvpn":
            if "TAP-Windows" in result.stdout or "tun0" in result.stdout.lower():
                return True, {"type": vpn_type, "detected": True}
        return False, {"type": vpn_type, "detected": False}
    except Exception as e:
        return False, {"error": str(e)}


def check_serial(ports: List[str], baudrate: int, timeout: int) -> Tuple[bool, Dict]:
    """Verifica conexión serial (port check via pyserial or Windows API)"""
    available_ports = []
    for port in ports:
        try:
            import serial
            with serial.Serial(port, baudrate, timeout=timeout) as ser:
                if ser.is_open:
                    available_ports.append(port)
        except ImportError:
            try:
                import ctypes
                handle = ctypes.windll.kernel32.CreateFileW(
                    f"\\\\.\\{port}", 0x80000000, 0, None, 0x3, 0, None
                )
                if handle != -1:
                    available_ports.append(port)
                    ctypes.windll.kernel32.CloseHandle(handle)
            except:
                continue
        except Exception:
            continue
    return len(available_ports) > 0, {"ports_available": available_ports}


# Health checkers registry
HEALTH_CHECKERS = {
    "adb_tcp": lambda ep: check_adb_tcp(ep.config["adb_path"], ep.config["device_ips"], ep.timeout),
    "adb_usb": lambda ep: check_adb_usb(ep.config["adb_path"], ep.timeout),
    "tailscale_exit": lambda ep: check_tailscale(ep.timeout),
    "tailscale_subnet": lambda ep: check_tailscale(ep.timeout),
    "ssh": lambda ep: check_ssh(ep.config["host"], ep.config.get("port", 22), ep.timeout),
    "http": lambda ep: check_http(ep.config["url"], ep.config.get("expected_status", 200), ep.timeout),
    "dns": lambda ep: check_dns(ep.config.get("resolvers", ["8.8.8.8"]), ep.config.get("test_domain", "google.com")),
    "mqtt": lambda ep: check_mqtt(ep.config.get("host", "localhost"), ep.config.get("port", 1883), ep.timeout),
    "websocket": lambda ep: check_websocket(ep.config["url"], ep.timeout),
    "vpn": lambda ep: check_vpn(ep.config.get("type", "openvpn"), ep.timeout),
    "serial": lambda ep: check_serial(ep.config.get("ports", []), ep.config.get("baudrate", 9600), ep.timeout),
    "http_polling": lambda ep: check_http(ep.config["url"], ep.config.get("expected_status", 200), ep.timeout),
}
