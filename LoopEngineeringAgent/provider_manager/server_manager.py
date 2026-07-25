"""
ServerManager — Gerencia multiplas instancias do servidor OpenCode com failover.

Cada instancia e um processo `opencode serve` em uma porta unica.
O ServerManager monitora saude via TCP, faz failover automatico
quando o primario cai, e auto-return quando o primario recupera.

Arquitetura:
    primary:   127.0.0.1:50136  (instancia principal)
    secondary: 127.0.0.1:50137  (instancia reserva)
    status:    active | standby | down
"""

import os
import sys
import time
import socket
import subprocess
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("ServerManager")

# How often to check server health (seconds)
HEALTH_CHECK_INTERVAL = 30
# How often to test if primary has recovered (seconds)
AUTO_RETURN_INTERVAL = 120
# How long to wait for a server to start (seconds)
SERVER_START_TIMEOUT = 30


@dataclass
class ServerInstance:
    """Represents a single OpenCode server instance."""
    name: str
    host: str
    port: int
    pid: Optional[int] = None
    process: Optional[subprocess.Popen] = None
    status: str = "down"  # active | standby | down | starting
    last_online: Optional[float] = None
    error: Optional[str] = None


class ServerManager:
    """Manages OpenCode server instances with automatic failover.

    Usage:
        sm = ServerManager()
        sm.add_server("primary", "127.0.0.1", 50136)
        sm.add_server("secondary", "127.0.0.1", 50137)
        sm.initialize()
        sm.start_all()
    """

    def __init__(self, opencode_bin: Optional[str] = None):
        self._servers: Dict[str, ServerInstance] = {}
        self._active_server: Optional[str] = None
        self._primary_name: str = "primary"
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._auto_return_thread: Optional[threading.Thread] = None

        # Find opencode binary
        self._opencode_bin = opencode_bin or self._find_opencode()

    def _find_opencode(self) -> str:
        """Locate the opencode executable."""
        candidates = [
            os.path.join(os.environ.get("APPDATA", ""),
                         "npm", "node_modules", "opencode-ai", "bin", "opencode.exe"),
            os.path.join(os.path.dirname(sys.executable), "opencode.exe"),
            "opencode.exe",
            "opencode",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate
            # Try with which/where
            try:
                result = subprocess.run(
                    ["where", "opencode"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split("\n")[0]
            except Exception:
                pass
        return "opencode.exe"  # fallback — assume on PATH

    def add_server(self, name: str, host: str, port: int,
                   auto_start: bool = False) -> ServerInstance:
        """Register a server instance.

        Args:
            name: Unique identifier (e.g., 'primary', 'secondary')
            host: Hostname or IP
            port: TCP port
            auto_start: If True, start this server on initialize()
        """
        server = ServerInstance(name=name, host=host, port=port)
        self._servers[name] = server
        if not self._active_server:
            self._active_server = name
            self._primary_name = name
        return server

    def initialize(self):
        """Initialize: register default servers and find opencode binary."""
        if not self._servers:
            # Register default servers
            self.add_server("primary", "127.0.0.1", 50136)
            self.add_server("secondary", "127.0.0.1", 50137)

        # Check which servers are already running
        for name, server in self._servers.items():
            if self._check_port(server.host, server.port):
                server.status = "active" if name == self._active_server else "standby"
                server.last_online = time.time()
                logger.info(f"Server {name} already running on {server.host}:{server.port}")
            else:
                server.status = "down"

        # Update active server based on real state
        self._update_active_server()

        # Start background monitoring
        self._running = True
        self._start_monitor()
        self._start_auto_return()

        return self.summary()

    def start_server(self, name: str) -> bool:
        """Start a specific server instance via `opencode serve`."""
        server = self._servers.get(name)
        if not server:
            logger.error(f"Unknown server: {name}")
            return False

        if server.status not in ("down", "standby"):
            logger.info(f"Server {name} already {server.status}")
            return True

        if not os.path.isfile(self._opencode_bin):
            # Try to find it again
            self._opencode_bin = self._find_opencode()
            if not os.path.isfile(self._opencode_bin) and "opencode" not in self._opencode_bin:
                logger.error(f"opencode binary not found: {self._opencode_bin}")
                server.error = "opencode binary not found"
                return False

        try:
            server.status = "starting"
            logger.info(f"Starting server {name} on {server.host}:{server.port}...")

            # Build command: opencode serve --port PORT --hostname HOST
            cmd = [
                self._opencode_bin,
                "serve",
                "--port", str(server.port),
                "--hostname", server.host,
                "--print-logs",
            ]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            server.process = proc
            server.pid = proc.pid

            # Wait for server to start (poll port)
            for _ in range(SERVER_START_TIMEOUT):
                time.sleep(1)
                if self._check_port(server.host, server.port):
                    server.status = "active" if name == self._active_server else "standby"
                    server.last_online = time.time()
                    server.error = None
                    logger.info(f"Server {name} started on {server.host}:{server.port} (PID {proc.pid})")
                    if self._active_server == name:
                        self._update_active_server()
                    return True

            # Timeout
            server.status = "down"
            server.error = "Timeout starting server"
            logger.error(f"Server {name} failed to start within {SERVER_START_TIMEOUT}s")
            return False

        except Exception as e:
            server.status = "down"
            server.error = str(e)
            logger.error(f"Failed to start server {name}: {e}")
            return False

    def stop_server(self, name: str) -> bool:
        """Stop a specific server instance."""
        server = self._servers.get(name)
        if not server:
            return False

        if server.process and server.process.poll() is None:
            server.process.terminate()
            try:
                server.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.process.kill()
        elif server.pid:
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(server.pid)],
                               capture_output=True, timeout=5)
            except Exception:
                pass

        server.status = "down"
        server.process = None
        server.pid = None
        server.error = "Stopped"
        return True

    def stop_all(self):
        """Stop all server instances."""
        for name in list(self._servers.keys()):
            self.stop_server(name)
        self._running = False

    def check_health(self, name: str) -> dict:
        """Check if a specific server is alive."""
        server = self._servers.get(name)
        if not server:
            return {"name": name, "online": False, "error": "Unknown server"}

        start = time.time()
        online = self._check_port(server.host, server.port)
        elapsed = (time.time() - start) * 1000

        return {
            "name": name,
            "online": online,
            "latency_ms": round(elapsed, 1),
            "port": server.port,
            "status": server.status,
            "pid": server.pid,
        }

    def check_all_health(self) -> Dict[str, dict]:
        """Check health of all servers."""
        return {
            name: self.check_health(name)
            for name in self._servers
        }

    def get_active_server(self) -> Optional[str]:
        """Return the name of the currently active server."""
        return self._active_server

    def get_server(self, name: str) -> Optional[ServerInstance]:
        return self._servers.get(name)

    def summary(self) -> dict:
        """Return a summary of all servers."""
        result = {
            "active_server": self._active_server,
            "primary": self._primary_name,
            "servers": [],
        }
        for name, server in self._servers.items():
            result["servers"].append({
                "name": name,
                "host": server.host,
                "port": server.port,
                "status": server.status,
                "pid": server.pid,
                "error": server.error,
            })
        return result

    def summary_text(self) -> str:
        """Return a human-readable summary."""
        lines = []
        lines.append("=" * 50)
        lines.append(f"  SERVIDORES OPENCODE")
        lines.append(f"  Ativo: {self._active_server or 'NENHUM'}")
        lines.append(f"  Primario: {self._primary_name}")
        lines.append("=" * 50)

        for name, server in self._servers.items():
            indicator = "►" if name == self._active_server else " "
            status_icon = {
                "active": "ONLINE",
                "standby": "STANDBY",
                "down": "DOWN",
                "starting": "INICIANDO",
            }.get(server.status, server.status)
            lines.append(
                f"  {indicator} {name:12s} {server.host}:{server.port:<6d} "
                f"{status_icon:>8s}"
                f"{'  PID: ' + str(server.pid) if server.pid else ''}"
                f"{'  ERRO: ' + server.error if server.error else ''}"
            )
        lines.append("=" * 50)
        return "\n".join(lines)

    # ─── Internal ───────────────────────────────────────────────────

    def _check_port(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """Check if a TCP port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _update_active_server(self):
        """Ensure the active server is actually online."""
        with self._lock:
            # Check if current active is still alive
            active = self._servers.get(self._active_server) if self._active_server else None
            if active and active.status != "down":
                if self._check_port(active.host, active.port):
                    active.status = "active"
                    active.last_online = time.time()
                    return

            # Active is down — find next available
            for name, server in self._servers.items():
                if self._check_port(server.host, server.port):
                    old = self._active_server
                    self._active_server = name
                    server.status = "active"
                    server.last_online = time.time()
                    if old and old != name:
                        logger.info(f"SERVER FAILOVER: {old} -> {name}")
                        # Also update old server status
                        old_srv = self._servers.get(old)
                        if old_srv:
                            old_srv.status = "down"
                    return

            # No servers online at all
            self._active_server = None

    def _start_monitor(self):
        """Start background health monitor."""
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self):
        """Background: check all servers every N seconds, trigger failover if needed."""
        while self._running:
            time.sleep(HEALTH_CHECK_INTERVAL)
            try:
                self._update_active_server()
            except Exception:
                pass

    def _start_auto_return(self):
        """Start background auto-return thread."""
        self._auto_return_thread = threading.Thread(
            target=self._auto_return_loop, daemon=True
        )
        self._auto_return_thread.start()

    def _auto_return_loop(self):
        """Background: every N seconds, test if primary server is back."""
        while self._running:
            time.sleep(AUTO_RETURN_INTERVAL)
            try:
                with self._lock:
                    if self._active_server == self._primary_name:
                        continue  # Already on primary

                    primary = self._servers.get(self._primary_name)
                    if not primary:
                        continue

                    if self._check_port(primary.host, primary.port):
                        # Primary is back!
                        old = self._active_server
                        self._active_server = self._primary_name
                        primary.status = "active"
                        primary.last_online = time.time()
                        primary.error = None
                        if old:
                            old_srv = self._servers.get(old)
                            if old_srv:
                                old_srv.status = "standby"
                        logger.info(f"SERVER AUTO-RETURN: {old} -> {self._primary_name}")
            except Exception:
                pass
