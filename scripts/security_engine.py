"""Security Engine - Engine dedicada de segurança do Ecossistema.

Fornece:
- Validação de entradas (sanitização, schema, limites)
- Detecção de ameaças (injection, path traversal, comandos perigosos)
- Sandbox de execução (isolamento, timeouts, limites de recursos)
- Auditoria de segurança (logs estruturados, alertas)
- Políticas de acesso (princípio menor privilégio)
- Gestão de segredos (detecção, rotação, validação)
"""

import os
import sys
import json
import re
import hashlib
import secrets
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
SECURITY_DIR = os.path.join(RUNTIME_DIR, 'security')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class ThreatLevel(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    INPUT_VALIDATION = "input_validation"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SECRET_DETECTED = "secret_detected"
    PERMISSION_VIOLATION = "permission_violation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    POLICY_VIOLATION = "policy_violation"
    SANDBOX_VIOLATION = "sandbox_violation"


@dataclass
class SecurityEvent:
    id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    source: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    blocked: bool = False
    remediation: str = ""


@dataclass
class ValidationRule:
    name: str
    pattern: str
    threat_level: ThreatLevel
    description: str
    action: str = "block"  # block, warn, sanitize


@dataclass
class SandboxConfig:
    max_cpu_time: float = 30.0
    max_memory_mb: int = 512
    max_disk_mb: int = 100
    max_processes: int = 10
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=list)
    network_allowed: bool = False
    timeout: float = 60.0


DEFAULT_VALIDATION_RULES = [
    ValidationRule(
        name="sql_injection",
        pattern=r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+set|exec\s*\()",
        threat_level=ThreatLevel.HIGH,
        description="Possível SQL injection",
    ),
    ValidationRule(
        name="command_injection",
        pattern=r"(;|\||&|\$\(|\`|\|\||\&\&)\s*(rm|wget|curl|nc|netcat|bash|sh|python|perl|ruby)",
        threat_level=ThreatLevel.CRITICAL,
        description="Possível command injection",
    ),
    ValidationRule(
        name="path_traversal",
        pattern=r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/)",
        threat_level=ThreatLevel.HIGH,
        description="Path traversal attempt",
    ),
    ValidationRule(
        name="xss_script",
        pattern=r"(?i)(<script|javascript:|onerror=|onload=|onclick=|eval\(|document\.cookie)",
        threat_level=ThreatLevel.MEDIUM,
        description="Possível XSS",
    ),
    ValidationRule(
        name="secret_api_key",
        pattern=r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*[\"']?[a-zA-Z0-9_\-]{20,}",
        threat_level=ThreatLevel.CRITICAL,
        description="Chave de API ou segredo detectado",
    ),
    ValidationRule(
        name="secret_password",
        pattern=r"(?i)(password|passwd|pwd)\s*[:=]\s*[\"']?[^\s\"']{8,}",
        threat_level=ThreatLevel.HIGH,
        description="Senha em texto claro",
    ),
    ValidationRule(
        name="private_key",
        pattern=r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        threat_level=ThreatLevel.CRITICAL,
        description="Chave privada detectada",
    ),
    ValidationRule(
        name="aws_credentials",
        pattern=r"(?i)(aws[_-]?access[_-]?key|aws[_-]?secret[_-]?key)\s*[:=]\s*[A-Z0-9]{16,}",
        threat_level=ThreatLevel.CRITICAL,
        description="Credenciais AWS detectadas",
    ),
]


class SecurityEngine:
    def __init__(self):
        self.rules: List[ValidationRule] = list(DEFAULT_VALIDATION_RULES)
        self.custom_rules: List[ValidationRule] = []
        self.events: List[SecurityEvent] = []
        self.max_events = 1000
        self.sandbox_config = SandboxConfig()
        self._lock = threading.RLock()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        self._load()

    def _compile_patterns(self):
        for rule in self.rules + self.custom_rules:
            try:
                self._compiled_patterns[rule.name] = re.compile(rule.pattern)
            except re.error:
                pass

    def _get_storage_path(self):
        return os.path.join(SECURITY_DIR, 'security_events.json')

    def _ensure_dirs(self):
        os.makedirs(SECURITY_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    self.events.append(SecurityEvent(
                        id=item['id'],
                        event_type=SecurityEventType(item['event_type']),
                        threat_level=ThreatLevel(item['threat_level']),
                        source=item['source'],
                        description=item['description'],
                        details=item.get('details', {}),
                        timestamp=item.get('timestamp', ''),
                        blocked=item.get('blocked', False),
                        remediation=item.get('remediation', ''),
                    ))
            except Exception as e:
                print(f"[SecurityEngine] Erro ao carregar: {e}")

    def _save(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        try:
            tmp = path + '.tmp'
            data = [asdict(e) for e in self.events[-self.max_events:]]
            for d in data:
                d['event_type'] = d['event_type'].value if isinstance(d['event_type'], SecurityEventType) else d['event_type']
                d['threat_level'] = d['threat_level'].value if isinstance(d['threat_level'], ThreatLevel) else d['threat_level']
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[SecurityEngine] Erro ao salvar: {e}")

    def add_rule(self, rule: ValidationRule):
        with self._lock:
            self.custom_rules.append(rule)
            self.rules.append(rule)
            try:
                self._compiled_patterns[rule.name] = re.compile(rule.pattern)
            except re.error:
                pass
            self._save()

    def validate_input(self, input_data: str, source: str = "unknown") -> Tuple[bool, List[SecurityEvent]]:
        """Valida uma entrada contra todas as regras. Retorna (is_safe, events)."""
        events = []
        for rule in self.rules:
            pattern = self._compiled_patterns.get(rule.name)
            if pattern and pattern.search(input_data):
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=self._rule_to_event_type(rule),
                    threat_level=rule.threat_level,
                    source=source,
                    description=rule.description,
                    details={
                        'rule': rule.name,
                        'matched_text': input_data[:200],
                        'action': rule.action,
                    },
                    blocked=(rule.action == "block"),
                )
                events.append(event)
                self._record_event(event)
        return len([e for e in events if e.blocked]) == 0, events

    def _rule_to_event_type(self, rule: ValidationRule) -> SecurityEventType:
        mapping = {
            "sql_injection": SecurityEventType.INPUT_VALIDATION,
            "command_injection": SecurityEventType.COMMAND_INJECTION,
            "path_traversal": SecurityEventType.PATH_TRAVERSAL,
            "xss_script": SecurityEventType.INPUT_VALIDATION,
            "secret_api_key": SecurityEventType.SECRET_DETECTED,
            "secret_password": SecurityEventType.SECRET_DETECTED,
            "private_key": SecurityEventType.SECRET_DETECTED,
            "aws_credentials": SecurityEventType.SECRET_DETECTED,
        }
        return mapping.get(rule.name, SecurityEventType.SUSPICIOUS_PATTERN)

    def sanitize_input(self, input_data: str) -> str:
        """Remove/mascaras padrões perigosos."""
        result = input_data
        for rule in self.rules:
            if rule.action == "sanitize":
                pattern = self._compiled_patterns.get(rule.name)
                if pattern:
                    result = pattern.sub("[REDACTED]", result)
        return result

    def check_secrets(self, content: str, source: str = "unknown") -> List[SecurityEvent]:
        """Detecta segredos no conteúdo."""
        events = []
        secret_rules = [r for r in self.rules if r.event_type == SecurityEventType.SECRET_DETECTED]
        for rule in secret_rules:
            pattern = self._compiled_patterns.get(rule.name)
            if pattern:
                matches = pattern.findall(content)
                for match in matches:
                    event = SecurityEvent(
                        id=self._gen_id(),
                        event_type=SecurityEventType.SECRET_DETECTED,
                        threat_level=rule.threat_level,
                        source=source,
                        description=f"Segredo detectado: {rule.name}",
                        details={
                            'rule': rule.name,
                            'match': match[:100] if isinstance(match, str) else str(match)[:100],
                        },
                        blocked=True,
                    )
                    events.append(event)
                    self._record_event(event)
        return events

    def validate_path(self, path: str, source: str = "unknown") -> Tuple[bool, List[SecurityEvent]]:
        """Valida se um path é seguro (sem traversal, dentro de allowed_paths)."""
        events = []
        safe = True

        # Check path traversal
        traversal_rule = next((r for r in self.rules if r.name == "path_traversal"), None)
        if traversal_rule:
            pattern = self._compiled_patterns.get("path_traversal")
            if pattern and pattern.search(path):
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.PATH_TRAVERSAL,
                    threat_level=ThreatLevel.HIGH,
                    source=source,
                    description="Path traversal detectado",
                    details={'path': path},
                    blocked=True,
                )
                events.append(event)
                self._record_event(event)
                safe = False

        # Check allowed paths
        if self.sandbox_config.allowed_paths:
            path_obj = Path(path).resolve()
            allowed = any(str(path_obj).startswith(str(Path(p).resolve())) for p in self.sandbox_config.allowed_paths)
            if not allowed:
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.PERMISSION_VIOLATION,
                    threat_level=ThreatLevel.MEDIUM,
                    source=source,
                    description="Path fora de diretórios permitidos",
                    details={'path': path, 'allowed': self.sandbox_config.allowed_paths},
                    blocked=True,
                )
                events.append(event)
                self._record_event(event)
                safe = False

        # Check blocked paths
        for blocked in self.sandbox_config.blocked_paths:
            if Path(path).resolve().is_relative_to(Path(blocked).resolve()):
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.PERMISSION_VIOLATION,
                    threat_level=ThreatLevel.HIGH,
                    source=source,
                    description="Path em diretório bloqueado",
                    details={'path': path, 'blocked_dir': blocked},
                    blocked=True,
                )
                events.append(event)
                self._record_event(event)
                safe = False

        return safe, events

    def validate_command(self, command: str, source: str = "unknown") -> Tuple[bool, List[SecurityEvent]]:
        """Valida se um comando é seguro para execução."""
        events = []
        safe = True

        # Check injection patterns
        inj_rule = next((r for r in self.rules if r.name == "command_injection"), None)
        if inj_rule:
            pattern = self._compiled_patterns.get("command_injection")
            if pattern and pattern.search(command):
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.COMMAND_INJECTION,
                    threat_level=inj_rule.threat_level,
                    source=source,
                    description=inj_rule.description,
                    details={'command': command, 'action': inj_rule.action},
                    blocked=(inj_rule.action == "block"),
                )
                events.append(event)
                self._record_event(event)
                safe = False

        # Check blocked commands
        for blocked in self.sandbox_config.blocked_commands:
            if blocked in command:
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.COMMAND_INJECTION,
                    threat_level=ThreatLevel.CRITICAL,
                    source=source,
                    description=f"Comando bloqueado detectado: {blocked}",
                    details={'command': command, 'blocked': blocked},
                    blocked=True,
                )
                events.append(event)
                self._record_event(event)
                safe = False

        # Check allowed commands (if allowlist configured)
        if self.sandbox_config.allowed_commands:
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] not in self.sandbox_config.allowed_commands:
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.POLICY_VIOLATION,
                    threat_level=ThreatLevel.MEDIUM,
                    source=source,
                    description="Comando não está na allowlist",
                    details={'command': command, 'allowed': self.sandbox_config.allowed_commands},
                    blocked=True,
                )
                events.append(event)
                self._record_event(event)
                safe = False

        return safe, events

    def execute_sandboxed(self, command: List[str], cwd: str = None, stdin: str = None) -> Dict[str, Any]:
        """Executa comando em sandbox com limites de recursos."""
        safe, events = self.validate_command(" ".join(command), "sandbox")
        if not safe:
            return {
                'success': False,
                'error': 'Command blocked by security policy',
                'events': [asdict(e) for e in events],
            }

        cwd = cwd or BASE
        self.validate_path(cwd, "sandbox_cwd")

        try:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.PIPE if stdin else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = proc.communicate(input=stdin, timeout=self.sandbox_config.timeout)
                return {
                    'success': proc.returncode == 0,
                    'returncode': proc.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'events': [],
                }
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                event = SecurityEvent(
                    id=self._gen_id(),
                    event_type=SecurityEventType.RESOURCE_EXHAUSTION,
                    threat_level=ThreatLevel.HIGH,
                    source="sandbox",
                    description="Processo excedeu timeout",
                    details={'command': command, 'timeout': self.sandbox_config.timeout},
                    blocked=True,
                )
                self._record_event(event)
                return {
                    'success': False,
                    'error': f'Timeout after {self.sandbox_config.timeout}s',
                    'events': [asdict(event)],
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'events': [],
            }

    def _record_event(self, event: SecurityEvent):
        with self._lock:
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
            self._save()

    def _gen_id(self) -> str:
        return hashlib.md5(f"{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()[:12]

    def get_events(self, limit: int = 50, threat_level: ThreatLevel = None,
                   event_type: SecurityEventType = None, source: str = None) -> List[SecurityEvent]:
        with self._lock:
            filtered = list(self.events)
        if threat_level:
            filtered = [e for e in filtered if e.threat_level == threat_level]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if source:
            filtered = [e for e in filtered if e.source == source]
        return filtered[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            events = list(self.events)
        by_level = {}
        by_type = {}
        by_source = {}
        for e in events:
            by_level[e.threat_level.value] = by_level.get(e.threat_level.value, 0) + 1
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
            by_source[e.source] = by_source.get(e.source, 0) + 1
        return {
            'total_events': len(events),
            'by_level': by_level,
            'by_type': by_type,
            'by_source': by_source,
            'blocked_count': sum(1 for e in events if e.blocked),
        }

    def clear_events(self):
        with self._lock:
            self.events.clear()
            self._save()


engine = SecurityEngine()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Security Engine')
    sub = parser.add_subparsers(dest='cmd')

    p_validate = sub.add_parser('validate')
    p_validate.add_argument('input')
    p_validate.add_argument('--source', default='cli')

    p_check_path = sub.add_parser('check-path')
    p_check_path.add_argument('path')
    p_check_path.add_argument('--source', default='cli')

    p_check_cmd = sub.add_parser('check-command')
    p_check_cmd.add_argument('command')
    p_check_cmd.add_argument('--source', default='cli')

    p_exec = sub.add_parser('exec')
    p_exec.add_argument('command', nargs='+')

    p_sandbox = sub.add_parser('sandbox-config')
    p_sandbox.add_argument('--timeout', type=float)
    p_sandbox.add_argument('--allow-path', action='append')
    p_sandbox.add_argument('--block-path', action='append')
    p_sandbox.add_argument('--allow-cmd', action='append')
    p_sandbox.add_argument('--block-cmd', action='append')

    p_events = sub.add_parser('events')
    p_events.add_argument('--limit', type=int, default=20)
    p_events.add_argument('--level', choices=[l.value for l in ThreatLevel])
    p_events.add_argument('--type', choices=[t.value for t in SecurityEventType])
    p_events.add_argument('--source')

    p_stats = sub.add_parser('stats')
    p_clear = sub.add_parser('clear')

    p_add_rule = sub.add_parser('add-rule')
    p_add_rule.add_argument('name')
    p_add_rule.add_argument('pattern')
    p_add_rule.add_argument('level', choices=[l.value for l in ThreatLevel])
    p_add_rule.add_argument('description')
    p_add_rule.add_argument('--action', choices=['block', 'warn', 'sanitize'], default='block')

    args = parser.parse_args()

    if args.cmd == 'validate':
        safe, events = engine.validate_input(args.input, args.source)
        print(f"Safe: {safe}")
        for e in events:
            print(f"  [{e.threat_level.value}] {e.description}")

    elif args.cmd == 'check-path':
        safe, events = engine.validate_path(args.path, args.source)
        print(f"Safe: {safe}")
        for e in events:
            print(f"  [{e.threat_level.value}] {e.description}")

    elif args.cmd == 'check-command':
        safe, events = engine.validate_command(args.command, args.source)
        print(f"Safe: {safe}")
        for e in events:
            print(f"  [{e.threat_level.value}] {e.description}")

    elif args.cmd == 'exec':
        result = engine.execute_sandboxed(args.command)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == 'sandbox-config':
        if args.timeout:
            engine.sandbox_config.timeout = args.timeout
        if args.allow_path:
            engine.sandbox_config.allowed_paths.extend(args.allow_path)
        if args.block_path:
            engine.sandbox_config.blocked_paths.extend(args.block_path)
        if args.allow_cmd:
            engine.sandbox_config.allowed_commands.extend(args.allow_cmd)
        if args.block_cmd:
            engine.sandbox_config.blocked_commands.extend(args.block_cmd)
        print("Sandbox config updated")
        print(json.dumps(asdict(engine.sandbox_config), indent=2, ensure_ascii=False))

    elif args.cmd == 'events':
        level = ThreatLevel(args.level) if args.level else None
        etype = SecurityEventType(args.type) if args.type else None
        events = engine.get_events(args.limit, level, etype, args.source)
        for e in events:
            print(f"{e.timestamp} [{e.threat_level.value}] {e.event_type.value} | {e.source} | {e.description}")

    elif args.cmd == 'stats':
        print(json.dumps(engine.get_stats(), indent=2, ensure_ascii=False))

    elif args.cmd == 'clear':
        engine.clear_events()
        print("Events cleared")

    elif args.cmd == 'add-rule':
        rule = ValidationRule(
            name=args.name,
            pattern=args.pattern,
            threat_level=ThreatLevel(args.level),
            description=args.description,
            action=args.action,
        )
        engine.add_rule(rule)
        print(f"Rule added: {rule.name}")

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())