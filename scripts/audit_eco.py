"""audit_eco.py — Escaneamento automático do Ecossistema UmGrau.

Executa verificações de saúde, completude e integração de todos os
componentes. Gera relatório com findings分类ados como OK, WARN, ERROR
e sugestões de melhoria.

Uso:
  python scripts/audit_eco.py              # relatório completo
  python scripts/audit_eco.py --json       # saída JSON
  python scripts/audit_eco.py --quick      # apenas erros e warnings
"""
import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
RUNTIME = BASE / "runtime"
DOCS = BASE / "docs"
KNOWLEDGE = BASE / "conhecimento"


class Severity(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    INFO = "info"


@dataclass
class Finding:
    category: str
    check: str
    severity: Severity
    message: str
    fix: Optional[str] = None
    file: Optional[str] = None


@dataclass
class AuditReport:
    timestamp: str = ""
    findings: list = field(default_factory=list)
    score: int = 0  # 0-100

    def add(self, category: str, check: str, severity: Severity, message: str,
            fix: str = None, file: str = None):
        self.findings.append(Finding(category, check, severity, message, fix, file))

    def calculate_score(self):
        if not self.findings:
            self.score = 100
            return
        total = len(self.findings)
        errors = sum(1 for f in self.findings if f.severity == Severity.ERROR)
        warns = sum(1 for f in self.findings if f.severity == Severity.WARN)
        oks = sum(1 for f in self.findings if f.severity in (Severity.OK, Severity.INFO))
        self.score = max(0, min(100, int((oks * 100 + warns * 60 + errors * 0) / max(1, total))))


def _process_running(script_name: str) -> bool:
    """Verifica se um script Python está rodando."""
    try:
        r = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'",
             "get", "CommandLine", "/format:list"],
            capture_output=True, text=True, timeout=5
        )
        return script_name.lower() in r.stdout.lower()
    except Exception:
        return False


def _port_listening(port: int) -> bool:
    """Verifica se uma porta está escutando."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def _file_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _read_json(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _ast_ok(path: Path) -> bool:
    """Verifica se um arquivo Python compila sem erros de sintaxe."""
    try:
        import ast
        ast.parse(path.read_text(encoding="utf-8"))
        return True
    except SyntaxError:
        return False


# ============================================================
# CHECKS POR CATEGORIA
# ============================================================

def check_services(report: AuditReport):
    """Verifica se todos os serviços essenciais estão rodando."""
    services = {
        "jarvis_bridge.py": "Bridge WebSocket (porta 8765)",
        "tts_service.py": "TTS Service (SpeechPipeline)",
        "widget_edge.py": "Widget Edge (narrador integrado)",
        "widget_grafo.py": "Cerebro Vivo (grafo)",
        "system_guardian.py": "System Guardian (watchdog)",
    }
    for script, desc in services.items():
        running = _process_running(script)
        if running:
            report.add("Serviços", desc, Severity.OK, f"{script} rodando")
        else:
            report.add("Serviços", desc, Severity.ERROR,
                        f"{script} NÃO está rodando",
                        fix=f"Execute: pythonw scripts/{script}")

    # Portas
    ports = {8765: "Bridge WebSocket", 8767: "OpenCode Serve"}
    for port, desc in ports.items():
        up = _port_listening(port)
        if up:
            report.add("Portas", f"Porta {port} ({desc})", Severity.OK, "Escutando")
        else:
            report.add("Portas", f"Porta {port} ({desc})", Severity.WARN,
                        f"Porta {port} não está escutando")

    # OpenCode Resilience
    resilience_script = SCRIPTS / "opencode_resilience.py"
    if _file_exists(resilience_script):
        try:
            r = subprocess.run(
                [sys.executable, str(resilience_script), "--check"],
                capture_output=True, text=True, timeout=30, cwd=str(BASE)
            )
            if "[CLEAN]" in r.stdout or "limpeza recomendada" in r.stdout:
                report.add("OpenCode", "Cache Resilience", Severity.WARN,
                           "Cache com erros, limpeza recomendada",
                           fix="Execute: python scripts/opencode_resilience.py --clean")
            else:
                report.add("OpenCode", "Cache Resilience", Severity.OK,
                           "Cache saudável")
        except Exception as e:
            report.add("OpenCode", "Cache Resilience", Severity.WARN,
                       f"Não foi possível verificar: {e}")

    # Solution Index (problema→solução)
    solution_script = SCRIPTS / "solution_index.py"
    if _file_exists(solution_script):
        try:
            r = subprocess.run(
                [sys.executable, str(solution_script), "--json"],
                capture_output=True, text=True, timeout=30, cwd=str(BASE)
            )
            if r.returncode == 0:
                data = json.loads(r.stdout)
                stats = data.get("stats", {})
                resolvidos = stats.get("resolvidos", 0)
                total = stats.get("total_erros", 0)
                taxa = stats.get("taxa_resolucao", "0%")
                if total > 0 and resolvidos == 0:
                    report.add("Conhecimento", "Índice Problema→Solução", Severity.WARN,
                               f"Nenhuma solução vinculada a {total} erros",
                               fix="Execute: python scripts/migrate_solutions.py")
                else:
                    report.add("Conhecimento", "Índice Problema→Solução", Severity.OK,
                               f"{resolvidos}/{total} erros resolvidos ({taxa})")
            else:
                report.add("Conhecimento", "Índice Problema→Solução", Severity.WARN,
                           "Não foi possível gerar índice")
        except Exception as e:
            report.add("Conhecimento", "Índice Problema→Solução", Severity.WARN,
                       f"Não foi possível verificar: {e}")


def check_widget_features(report: AuditReport):
    """Verifica se as 8 features do widget estão implementadas."""
    widget_file = SCRIPTS / "widget_edge.py"
    if not _file_exists(widget_file):
        report.add("Widget", "Arquivo principal", Severity.ERROR,
                    "widget_edge.py não encontrado")
        return

    content = widget_file.read_text(encoding="utf-8")

    features = {
        "conn": ("Indicadores de conexão", "conn.*narrador.*tts.*bridge"),
        "volume": ("Slider de volume", "volSlider|vol_slider|volume"),
        "sleep": ("Sleep timer", "sleepSelect|sleep_timer|sleep"),
        "tasks": ("Painel de tarefas", "tasksList|tasks_pendentes"),
        "model": ("Model chip", "modelChip|model_stats"),
        "errors": ("Toast de erros", "errorToast|error.*toast"),
        "pulse": ("Animação pulse", "pulse|mic.*active"),
        "theme": ("Toggle de tema", "themeDark|theme.*toggle|applyTheme"),
        "notif": ("Log de notificações", "notifLog|notificacoes"),
        "throttle": ("Throttle de narração", "NARRACAO_MIN_GAP|_falar_direto_throttle"),
        "position_reset": ("Reset de posição no startup", "_resetar_posicao_narrador"),
    }

    import re
    for key, (desc, pattern) in features.items():
        if re.search(pattern, content):
            report.add("Widget Features", desc, Severity.OK, "Implementado")
        else:
            report.add("Widget Features", desc, Severity.WARN,
                        f"{desc} não encontrado no widget",
                        fix=f"Implementar {desc} em widget_edge.py")


def check_widget_error_filter(report: AuditReport):
    """Valida se o filtro de erros do widget casa com os formatos reais dos logs.

    Motivo: o widget mostrava erros antigos porque os padrões [error]/[warning]
    não casavam com ERROR:vox:/WARNING:vox: dos logs reais. Esta check captura
    esse tipo de mismatch ANTES de chegar no usuário.
    """
    import re as _re
    from datetime import datetime as _dt

    widget_file = SCRIPTS / "widget_edge.py"
    if not _file_exists(widget_file):
        report.add("Widget Error Filter", "Widget existe", Severity.ERROR,
                    "widget_edge.py não encontrado")
        return

    content = widget_file.read_text(encoding="utf-8")

    # 1) Verifica se o regex de timestamp aceita formato com vírgula
    ts_pattern = r'[\[(\s]*(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})'
    test_cases = [
        ("2026-08-20 08:33:44,436 ERROR:vox:HTTP 500", True, "formato com vírgula"),
        ("[2026-08-20 10:19:53] FALHA ao restaurar", True, "formato com colchetes"),
        ("2026-08-20T08:33:44 WARNING:test", True, "formato ISO com T"),
        ("sem timestamp aqui", False, "sem timestamp"),
    ]
    ts_ok = 0
    for sample, should_match, desc in test_cases:
        matched = bool(_re.match(ts_pattern, sample))
        if matched == should_match:
            ts_ok += 1
        else:
            report.add("Widget Error Filter", f"Timestamp {desc}", Severity.ERROR,
                        f"Regex timestamp não casa com '{sample[:40]}' (esperado: {should_match})",
                        fix="Atualizar regex _ler_recent_errors() em widget_edge.py")

    if ts_ok == len(test_cases):
        report.add("Widget Error Filter", "Regex timestamp", Severity.OK,
                    f"Aceita todos os formatos de log ({ts_ok}/{len(test_cases)})")

    # 2) Verifica se padrões de erro casam com formatos reais dos logs
    log_patterns_to_check = [
        ("ERROR:vox:", "error:", "bridge ERROR padrão"),
        ("[ERROR]", "[error]", "colchete ERROR"),
        ("WARNING:vox:WATCHDOM: erro", "[warning]", "bridge WARNING com erro"),
        ("traceback", "traceback", "Python traceback"),
        ("exception:", "exception:", "Python exception"),
    ]

    # Lê linhas reais dos logs mais recentes (aplicando mesmos filtros do widget)
    log_files = sorted(SCRIPTS.glob("*log*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)[:3]
    real_error_lines = []
    for lf in log_files:
        try:
            lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-300:]:
                ll = line.lower()
                # Mesmos filtros do widget _ler_recent_errors()
                if "falando (" in ll:
                    continue  # narração, não erro
                if "warm-up" in ll:
                    continue  # warm-up do bridge
                if any(pat in ll for pat in ["error", "erro", "warning", "falhou",
                                              "traceback", "exception", "falha"]):
                    real_error_lines.append(line)
                    if len(real_error_lines) >= 20:
                        break
        except Exception:
            pass
        if len(real_error_lines) >= 20:
            break

    # Extrai padrões de erro do widget (verificação estática)
    widget_patterns = []
    pat_match = _re.search(r'is_real_error\s*=\s*\((.*?)\)', content, _re.DOTALL)
    if pat_match:
        block = pat_match.group(1)
        for m in _re.finditer(r'"([^"]+)"', block):
            widget_patterns.append(m.group(1).lower())

    if not widget_patterns:
        report.add("Widget Error Filter", "Padrões detectados", Severity.WARN,
                    "Não foi possível extrair padrões de erro do widget",
                    fix="Verificar formato de is_real_error em widget_edge.py")
        return

    # Testa cada linha real contra os padrões do widget
    matched_count = 0
    unmatched_lines = []
    for line in real_error_lines[:10]:
        ll = line.lower()
        # Aplica a mesma lógica do widget (espelho de _ler_recent_errors)
        is_error = (
            "[error]" in ll or
            "error:" in ll or
            "[erro]" in ll or
            ("[warning]" in ll and "falhou" in ll) or
            ("warning:" in ll and ("erro" in ll or "falhou" in ll)) or
            "traceback" in ll or
            "exception:" in ll or
            "falha de voz" in ll or
            "speechpipeline falhou" in ll or
            (ll.startswith("[") and "erro" in ll and "falando" not in ll)
        )
        if is_error:
            matched_count += 1
        else:
            unmatched_lines.append(line[:80])

    if unmatched_lines:
        report.add("Widget Error Filter", "MISMATCH padrões vs logs", Severity.WARN,
                    f"{len(unmatched_lines)} linhas de erro real não casam com padrões do widget",
                    fix="Adicionar padrões ausentes em _ler_recent_errors()")
        for ul in unmatched_lines[:3]:
            report.add("Widget Error Filter", "Exemplo mismatch", Severity.WARN, ul)
    elif real_error_lines:
        report.add("Widget Error Filter", "Padrões vs logs", Severity.OK,
                    f"Todos os erros reais casam com padrões do widget ({matched_count}/{len(real_error_lines[:10])})")
    else:
        report.add("Widget Error Filter", "Logs verificados", Severity.INFO,
                    "Nenhuma linha de erro encontrada nos logs recentes")


def check_tts_integration(report: AuditReport):
    """Verifica integração TTS (volume, SpeechPipeline)."""
    tts_file = SCRIPTS / "tts_service.py"
    if _file_exists(tts_file):
        content = tts_file.read_text(encoding="utf-8")
        if "widget_state" in content or "_ler_volume" in content:
            report.add("TTS", "Volume integrado", Severity.OK, "tts_service lê volume do widget")
        else:
            report.add("TTS", "Volume integrado", Severity.WARN,
                        "tts_service não lê volume de widget_state.json",
                        fix="Adicionar leitura de volume em tts_service.py")

    pipeline_file = BASE / "tts" / "speech_pipeline.py"
    if _file_exists(pipeline_file):
        content = pipeline_file.read_text(encoding="utf-8")
        if "volume" in content:
            report.add("TTS", "SpeechPipeline volume", Severity.OK, "Parâmetro volume no speak()")
        else:
            report.add("TTS", "SpeechPipeline volume", Severity.WARN,
                        "SpeechPipeline.speak() não tem parâmetro volume")


def check_bridge_integration(report: AuditReport):
    """Verifica integração do bridge (volume, model monitor)."""
    bridge_file = SCRIPTS / "jarvis_bridge.py"
    if not _file_exists(bridge_file):
        report.add("Bridge", "Arquivo principal", Severity.ERROR, "jarvis_bridge.py não encontrado")
        return

    content = bridge_file.read_text(encoding="utf-8")

    if "_ler_volume_widget" in content or "widget_state" in content:
        report.add("Bridge", "Volume no WebSocket", Severity.OK, "Bridge envia volume via WS")
    else:
        report.add("Bridge", "Volume no WebSocket", Severity.WARN,
                    "Bridge não envia volume para clientes",
                    fix="Adicionar _ler_volume_widget() e enviar volume nas mensagens WS")

    if "_fb_registrar" in content or "llm_feedback" in content:
        report.add("Bridge", "Model monitor", Severity.OK, "Bridge registra latência/taxa")
    else:
        report.add("Bridge", "Model monitor", Severity.WARN,
                    "Bridge não registra dados de modelo")


def check_model_monitor(report: AuditReport):
    """Verifica se model monitor tem dados reais."""
    feedback_file = DOCS / "llm_feedback.json"
    if _file_exists(feedback_file):
        data = _read_json(feedback_file)
        total_models = len(data)
        total_requests = sum(
            v.get("sucessos", 0) + v.get("falhas", 0)
            for v in data.values()
        )
        if total_requests > 0:
            report.add("Model Monitor", "Dados reais", Severity.OK,
                        f"{total_models} modelos, {total_requests} requests registrados")
        else:
            report.add("Model Monitor", "Dados reais", Severity.WARN,
                        "llm_feedback.json existe mas sem requests registrados")
    else:
        report.add("Model Monitor", "Arquivo", Severity.WARN,
                    "llm_feedback.json não existe ainda")


def check_narrator_health(report: AuditReport):
    """Verifica saúde do narrador (posição, backlog)."""
    pos_file = RUNTIME / "narrador_posicao.json"
    if _file_exists(pos_file):
        pos = _read_json(pos_file)
        ts = pos.get("ultimo_ts", 0)
        if ts > 0:
            age_hours = (time.time() * 1000 - ts) / (1000 * 3600)
            if age_hours < 24:
                report.add("Narrador", "Posição", Severity.OK,
                            f"Posição atualizada há {age_hours:.1f}h")
            else:
                report.add("Narrador", "Posição", Severity.WARN,
                            f"Posição desatualizada ({age_hours:.0f}h atrás)",
                            fix="Verificar se narrador está lendo SQLite corretamente")
        else:
            report.add("Narrador", "Posição", Severity.WARN, "Posição zero (início limpo)")
    else:
        report.add("Narrador", "Posição", Severity.INFO, "Arquivo de posição não existe")

    # Verifica se narrator relê posição do disco (no widget_edge, lar do narrador)
    narrator_file = SCRIPTS / "widget_edge.py"
    if _file_exists(narrator_file):
        content = narrator_file.read_text(encoding="utf-8")
        if "ler_posicao" in content and "ultimo_ts" in content:
            # Verifica se relê no loop (não só no startup)
            if content.count("ler_posicao") >= 2:
                report.add("Narrador", "Re-leitura de posição", Severity.OK,
                            "Narrador relê posição no loop (anti-backlog)")
            else:
                report.add("Narrador", "Re-leitura de posição", Severity.WARN,
                            "Narrador pode não reler posição no loop",
                            fix="Adicionar re-leitura de narrador_posicao.json no loop principal")

        # Filtro de idioma — narrador só fala português
        if "validar_idioma" in content and "BLOQUEADO (idioma=" in content:
            report.add("Narrador", "Filtro idioma", Severity.OK,
                        "Narrador bloqueia texto em inglês")
        elif "validar_idioma" in content:
            report.add("Narrador", "Filtro idioma", Severity.WARN,
                        "Narrador importa validar_idioma mas não bloqueia",
                        fix="Adicionar check de idioma no _flush()")
        else:
            report.add("Narrador", "Filtro idioma", Severity.ERROR,
                        "Narrador NÃO valida idioma — pode falar inglês",
                        fix="Adicionar filtro de idioma em widget_edge.py")

        # Mecanismo de stop — narrador respeita parar_fala.flag
        if "parar_fala" in content and "STOP_FLAG.exists()" in content:
            report.add("Narrador", "Mecanismo stop", Severity.OK,
                        "Narrador checa parar_fala.flag durante fala")
        else:
            report.add("Narrador", "Mecanismo stop", Severity.WARN,
                        "Narrador pode não respeitar parar_fala.flag",
                        fix="Adicionar check de STOP_FLAG.exists() no _flush()")


def check_guardian_coverage(report: AuditReport):
    """Verifica se guardian monitora todos os serviços."""
    guardian_file = SCRIPTS / "system_guardian.py"
    if not _file_exists(guardian_file):
        report.add("Guardian", "Arquivo", Severity.ERROR, "system_guardian.py não encontrado")
        return

    content = guardian_file.read_text(encoding="utf-8")

    monitored = {
        "is_narrador_up": "Narrador (via narracao_estado.json)",
        "tts_service": "TTS Service",
        "jarvis_bridge": "Bridge",
        "widget_edge": "Widget",
        "widget_grafo": "Cerebro Vivo",
    }
    for script, desc in monitored.items():
        if script in content:
            report.add("Guardian", f"Cobertura: {desc}", Severity.OK,
                        f"Guardian monitora {desc}")
        else:
            report.add("Guardian", f"Cobertura: {desc}", Severity.WARN,
                        f"Guardian NÃO monitora {desc}",
                        fix=f"Adicionar monitoramento de {script} no guardian")


def check_guardian_desktop_protection(report: AuditReport):
    """Verifica cláusula pétrea: guardian NUNCA mata o desktop OpenCode.

    Causa raiz do travamento recorrente do OpenCode: system_guardian.py
    matava opencode.exe por RAM crítica (o lower() fazia OpenCode.exe virar
    opencode.exe), corrompia o snapshot e obrigava a deletar a pasta.
    """
    guardian_file = SCRIPTS / "system_guardian.py"
    if not _file_exists(guardian_file):
        report.add("Guardian", "Proteção desktop", Severity.ERROR,
                   "system_guardian.py não encontrado")
        return

    content = guardian_file.read_text(encoding="utf-8")

    has_func = "def is_desktop_opencode" in content
    has_call = "is_desktop_opencode(pid)" in content
    has_path = "@opencode-aidesktop" in content
    has_cpu_guard = "CPU runaway no desktop OpenCode" in content

    if has_func and has_call and has_path and has_cpu_guard:
        report.add("Guardian", "Proteção desktop", Severity.OK,
                   "Desktop OpenCode intocável (kill candidates + CPU runaway)")
    else:
        missing = []
        if not has_func:
            missing.append("is_desktop_opencode() ausente")
        if not has_call:
            missing.append("checagem em get_kill_candidates() ausente")
        if not has_path:
            missing.append("caminho @opencode-aidesktop não verificado")
        if not has_cpu_guard:
            missing.append("proteção no CPU runaway ausente")
        report.add("Guardian", "Proteção desktop", Severity.ERROR,
                   "Cláusula pétrea pode ser violada: " + "; ".join(missing),
                   fix="Garantir que system_guardian.py nunca mate OpenCode.exe do @opencode-aidesktop")


def check_theme_sync(report: AuditReport):
    """Verifica sincronização de tema entre Jarvis e Cerebro Vivo."""
    widget_file = SCRIPTS / "widget_edge.py"
    grafo_file = SCRIPTS / "widget_grafo.py"
    extra_js = DOCS / "widget-extra.js"

    if _file_exists(widget_file):
        content = widget_file.read_text(encoding="utf-8")
        if "theme" in content and "widget_state" in content:
            report.add("Tema Sync", "Jarvis escreve tema", Severity.OK,
                        "Jarvis salva tema em widget_state.json")
        else:
            report.add("Tema Sync", "Jarvis escreve tema", Severity.WARN,
                        "Jarvis pode não salvar tema em widget_state.json")

    if _file_exists(grafo_file):
        content = grafo_file.read_text(encoding="utf-8")
        if "ler_tema_sincronizado" in content:
            report.add("Tema Sync", "Cerebro lê tema", Severity.OK,
                        "Cerebro Vivo lê tema de widget_state.json")
        else:
            report.add("Tema Sync", "Cerebro lê tema", Severity.WARN,
                        "Cerebro Vivo não lê tema do Jarvis",
                        fix="Adicionar ler_tema_sincronizado() ao Bridge do grafo")

    if _file_exists(extra_js):
        content = extra_js.read_text(encoding="utf-8")
        if "syncThemeFromJarvis" in content or "ler_tema_sincronizado" in content:
            report.add("Tema Sync", "Cerebro JS poll", Severity.OK,
                        "Cerebro JS faz polling de tema do Jarvis")
        else:
            report.add("Tema Sync", "Cerebro JS poll", Severity.WARN,
                        "Cerebro JS não faz polling de tema")


def check_config_consistency(report: AuditReport):
    """Verifica consistência de configs."""
    files_to_check = [
        (SCRIPTS / "pronuncias.json", "Pronúncias"),
        (SCRIPTS / "frases_manager.py", "Frases Manager"),
        (RUNTIME / "narracao_estado.json", "Estado Narração"),
        (RUNTIME / "widget_state.json", "Widget State"),
    ]

    for path, desc in files_to_check:
        if _file_exists(path):
            if path.suffix == ".json":
                data = _read_json(path)
                if data:
                    report.add("Config", desc, Severity.OK, f"{desc} existe e tem dados")
                else:
                    report.add("Config", desc, Severity.WARN, f"{desc} existe mas vazio")
            else:
                report.add("Config", desc, Severity.OK, f"{desc} existe")
        else:
            report.add("Config", desc, Severity.INFO, f"{desc} não existe (pode ser normal)")


def check_skills(report: AuditReport):
    """Verifica integridade do núcleo de habilidades MCP."""
    mcp_dir = BASE / "mcp"
    if not mcp_dir.exists():
        report.add("Habilidades", "Diretório mcp/", Severity.ERROR,
                    "mcp/ não existe", fix="Criar diretório mcp/")
        return

    # Conta skills por domínio
    domains = {}
    total_skills = 0
    total_with_code = 0
    empty_skills = []
    small_skills = []

    for skill_md in list(mcp_dir.rglob("skill.md")) + list(mcp_dir.rglob("SKILL.md")):
        # mcp/domínio/habilidades/nome-skill/skill.md → domínio = 3 levels up
        parts = skill_md.parts
        try:
            idx = parts.index("habilidades")
            domain = parts[idx - 1] if idx > 0 else "unknown"
        except ValueError:
            domain = "other"
        skill_name = skill_md.parent.name
        total_skills += 1
        domains[domain] = domains.get(domain, 0) + 1

        # Verifica se tem implementação Python
        py_files = list(skill_md.parent.glob("*.py"))
        if py_files:
            total_with_code += 1

        # Verifica tamanho mínimo
        size = skill_md.stat().st_size
        if size == 0:
            empty_skills.append(skill_name)
        elif size < 50:
            small_skills.append(skill_name)

    report.add("Habilidades", "Total", Severity.OK,
                f"{total_skills} skills em {len(domains)} domínios")

    # Skills com código
    pct_with_code = (total_with_code / max(1, total_skills)) * 100
    if pct_with_code > 20:
        report.add("Habilidades", "Com implementação", Severity.OK,
                    f"{total_with_code}/{total_skills} ({pct_with_code:.0f}%) têm código Python")
    else:
        report.add("Habilidades", "Com implementação", Severity.INFO,
                    f"{total_with_code}/{total_skills} ({pct_with_code:.0f}%) têm código Python")

    # Skills vazias
    if empty_skills:
        report.add("Habilidades", "Skills vazias", Severity.WARN,
                    f"{len(empty_skills)} skills vazias: {', '.join(empty_skills[:5])}",
                    fix="Preencher ou remover skills vazias")
    else:
        report.add("Habilidades", "Skills vazias", Severity.OK, "Nenhuma skill vazia")

    # Skills muito pequenas
    if small_skills:
        report.add("Habilidades", "Skills incompletas", Severity.INFO,
                    f"{len(small_skills)} skills < 50 bytes: {', '.join(small_skills[:5])}")
    else:
        report.add("Habilidades", "Skills completas", Severity.OK,
                    f"Todas as skills têm conteúdo substancial")


def check_python_syntax(report: AuditReport):
    """Verifica sintaxe de todos os scripts Python principais."""
    critical_scripts = [
        "widget_edge.py", "widget_grafo.py", "jarvis_bridge.py",
        "tts_service.py", "system_guardian.py", "frases_manager.py",
        "llm_feedback.py", "model_monitor.py",
    ]
    for script in critical_scripts:
        path = SCRIPTS / script
        if _file_exists(path):
            if _ast_ok(path):
                report.add("Sintaxe", script, Severity.OK, "Sintaxe OK")
            else:
                report.add("Sintaxe", script, Severity.ERROR,
                            f"Erro de sintaxe em {script}",
                            fix=f"Corrigir erro de sintaxe em scripts/{script}")


def check_knowledge_base(report: AuditReport):
    """Verifica base de conhecimento."""
    aprendizados = list((KNOWLEDGE / "aprendizados").glob("*.md")) if (KNOWLEDGE / "aprendizados").exists() else []
    if len(aprendizados) > 0:
        recent = sorted(aprendizados, key=lambda f: f.stat().st_mtime, reverse=True)[:3]
        report.add("Conhecimento", "Aprendizados", Severity.OK,
                    f"{len(aprendizados)} aprendizados registrados")
        # Verifica últimas atualizações
        if recent:
            age_days = (time.time() - recent[0].stat().st_mtime) / 86400
            if age_days < 7:
                report.add("Conhecimento", "Aprendizados recentes", Severity.OK,
                            f"Último aprendizado há {age_days:.1f} dias")
            else:
                report.add("Conhecimento", "Aprendizados recentes", Severity.WARN,
                            f"Último aprendizado há {age_days:.0f} dias — ecossistema pode não estar aprendendo",
                            fix="Rodar tarefas e registrar aprendizados regularmente")
    else:
        report.add("Conhecimento", "Aprendizados", Severity.WARN,
                    "Nenhum aprendizado registrado")


# ============================================================
# INTEGRAÇÃO — verifica se componentes se comunicam corretamente
# ============================================================

def check_integration_volume(report: AuditReport):
    """Verifica se o volume flui do widget → tts_service → speechPipeline → bridge."""
    # Widget escreve volume?
    widget_state = _read_json(RUNTIME / "widget_state.json")
    vol = widget_state.get("volume")
    if vol is not None:
        report.add("Integração Volume", "Widget → widget_state.json", Severity.OK,
                    f"Widget escreveu volume={vol}")
    elif widget_state:
        report.add("Integração Volume", "Widget → widget_state.json", Severity.INFO,
                    "Widget_state existe mas sem volume ainda (normal se slider não usado)")
    else:
        report.add("Integração Volume", "Widget → widget_state.json", Severity.WARN,
                    "widget_state.json não existe ou vazio",
                    fix="Widget deve criar widget_state.json no startup")

    # tts_service lê?
    tts_file = SCRIPTS / "tts_service.py"
    if _file_exists(tts_file):
        content = tts_file.read_text(encoding="utf-8")
        if "widget_state" in content:
            report.add("Integração Volume", "tts_service ← widget_state", Severity.OK,
                        "tts_service lê volume do widget")
        else:
            report.add("Integração Volume", "tts_service ← widget_state", Severity.ERROR,
                        "tts_service NÃO lê volume — widget não afeta áudio",
                        fix="Adicionar _ler_volume() em tts_service.py")

    # Bridge envia volume?
    bridge_file = SCRIPTS / "jarvis_bridge.py"
    if _file_exists(bridge_file):
        content = bridge_file.read_text(encoding="utf-8")
        if '"volume"' in content and "_ler_volume_widget" in content:
            report.add("Integração Volume", "Bridge → clientes WS", Severity.OK,
                        "Bridge envia volume via WebSocket")
        else:
            report.add("Integração Volume", "Bridge → clientes WS", Severity.ERROR,
                        "Bridge NÃO envia volume — mobile não respeita volume",
                        fix="Adicionar _ler_volume_widget() e enviar volume nas mensagens WS")


def check_integration_theme(report: AuditReport):
    """Verifica se tema flui Jarvis → widget_state → Cerebro Vivo."""
    # Jarvis escreve tema?
    widget_file = SCRIPTS / "widget_edge.py"
    if _file_exists(widget_file):
        content = widget_file.read_text(encoding="utf-8")
        if "_ler_tema" in content and "theme" in content:
            report.add("Integração Tema", "Jarvis → widget_state.json", Severity.OK,
                        "Jarvis salva tema")
        else:
            report.add("Integração Tema", "Jarvis → widget_state.json", Severity.WARN,
                        "Jarvis pode não salvar tema")

    # Cerebro lê?
    grafo_file = SCRIPTS / "widget_grafo.py"
    if _file_exists(grafo_file):
        content = grafo_file.read_text(encoding="utf-8")
        if "ler_tema_sincronizado" in content:
            report.add("Integração Tema", "Cerebro ← widget_state.json", Severity.OK,
                        "Cerebro Vivo lê tema do Jarvis")
        else:
            report.add("Integração Tema", "Cerebro ← widget_state.json", Severity.WARN,
                        "Cerebro Vivo não lê tema — sincronização de tema delegada (escopo aberto)",
                        fix="Cerebro Vivo pode não espelhar tema do Jarvis; aplicar ler_tema_sincronizado() no grafo")

    # JS poll?
    extra_js = DOCS / "widget-extra.js"
    if _file_exists(extra_js):
        content = extra_js.read_text(encoding="utf-8")
        if "syncThemeFromJarvis" in content or "ler_tema_sincronizado" in content:
            report.add("Integração Tema", "Cerebro JS polling", Severity.OK,
                        "JS faz polling de tema")
        else:
            report.add("Integração Tema", "Cerebro JS polling", Severity.WARN,
                        "JS não faz polling — tema não atualiza em tempo real")


def check_integration_narrator(report: AuditReport):
    """Verifica integração narrator ↔ SQLite ↔ widget."""
    # narrator_posicao.json existe e é válido?
    pos_file = RUNTIME / "narrador_posicao.json"
    if _file_exists(pos_file):
        pos = _read_json(pos_file)
        ts = pos.get("ultimo_ts", 0)
        if ts > 0:
            # Verifica se o narrador relê posição no loop (lar do narrador = widget_edge)
            narrator_file = SCRIPTS / "widget_edge.py"
            if _file_exists(narrator_file):
                content = narrator_file.read_text(encoding="utf-8")
                count_ler = content.count("ler_posicao")
                if count_ler >= 2:
                    report.add("Integração Narrador", "Anti-backlog", Severity.OK,
                                "Narrador relê posição no loop (previne backlog)")
                else:
                    report.add("Integração Narrador", "Anti-backlog", Severity.WARN,
                                "Narrador pode não reler posição — risco de backlog",
                                fix="Adicionar re-leitura de narrador_posicao.json no loop")
        else:
            report.add("Integração Narrador", "Posição", Severity.INFO,
                        "Posição zero (início limpo)")
    else:
        report.add("Integração Narrador", "Posição", Severity.WARN,
                    "narrador_posicao.json não existe",
                    fix="Widget deve criar ao iniciar")

    # Widget reset.position no startup?
    widget_file = SCRIPTS / "widget_edge.py"
    if _file_exists(widget_file):
        content = widget_file.read_text(encoding="utf-8")
        if "_resetar_posicao_narrador" in content and "def main" in content:
            # Verifica se chama no main
            main_section = content[content.find("def main"):]
            if "_resetar_posicao_narrador" in main_section:
                report.add("Integração Narrador", "Reset no startup", Severity.OK,
                            "Widget reseta posição ao iniciar")
            else:
                report.add("Integração Narrador", "Reset no startup", Severity.WARN,
                            "Widget não reseta posição no startup — pode narrar backlog",
                            fix="Chamar _resetar_posicao_narrador() no main()")


def check_integration_model_monitor(report: AuditReport):
    """Verifica se model monitor recebe dados do bridge."""
    feedback_file = DOCS / "llm_feedback.json"
    if _file_exists(feedback_file):
        data = _read_json(feedback_file)
        total_requests = sum(v.get("sucessos", 0) + v.get("falhas", 0) for v in data.values())
        total_models = len(data)
        if total_requests > 0:
            # Calcula latência média geral
            total_lat = sum(v.get("latencia_ms_total", 0) for v in data.values())
            total_ok = sum(v.get("sucessos", 0) for v in data.values())
            avg_lat = total_lat // max(1, total_ok)
            report.add("Integração Model", "Dados reais", Severity.OK,
                        f"{total_models} modelos, {total_requests} requests, latência média {avg_lat}ms")

            # Verifica se widget lê llm_feedback
            widget_file = SCRIPTS / "widget_edge.py"
            if _file_exists(widget_file):
                content = widget_file.read_text(encoding="utf-8")
                if "llm_feedback" in content:
                    report.add("Integração Model", "Widget lê dados", Severity.OK,
                                "Widget lê de llm_feedback.json (dados reais)")
                else:
                    report.add("Integração Model", "Widget lê dados", Severity.WARN,
                                "Widget pode não estar lendo llm_feedback.json",
                                fix="Atualizar _ler_model_stats() para ler llm_feedback.json")
        else:
            report.add("Integração Model", "Dados reais", Severity.WARN,
                        "llm_feedback.json sem requests — bridge não está registrando",
                        fix="Verificar se _fb_registrar() está sendo chamado no bridge")
    else:
        report.add("Integração Model", "Arquivo", Severity.WARN,
                    "llm_feedback.json não existe")


# ============================================================
# ARQUITETURA — verifica estrutura e convenções
# ============================================================

def check_architecture(report: AuditReport):
    """Verifica estrutura do ecossistema."""
    # Diretórios essenciais
    dirs = {
        SCRIPTS: "scripts/",
        RUNTIME: "runtime/",
        DOCS: "docs/",
        KNOWLEDGE: "conhecimento/",
        KNOWLEDGE / "aprendizados": "conhecimento/aprendizados/",
    }
    for d, name in dirs.items():
        if d.exists():
            report.add("Arquitetura", f"Diretório {name}", Severity.OK, "Existe")
        else:
            report.add("Arquitetura", f"Diretório {name}", Severity.ERROR,
                        f"{name} não existe",
                        fix=f"Criar diretório {name}")

    # Arquivos essenciais
    essential_files = {
        SCRIPTS / "widget_edge.py": "Widget principal (Narrador Edge)",
        SCRIPTS / "jarvis_bridge.py": "Bridge WebSocket",
        SCRIPTS / "widget_grafo.py": "Cerebro Vivo",
        SCRIPTS / "tts_service.py": "TTS Service",
        SCRIPTS / "system_guardian.py": "System Guardian",
        SCRIPTS / "frases_manager.py": "Frases Manager",
        SCRIPTS / "pronuncias.json": "Pronúncias",
        SCRIPTS / "llm_feedback.py": "LLM Feedback",
        SCRIPTS / "audit_eco.py": "Audit Script",
        BASE / "tts" / "speech_pipeline.py": "SpeechPipeline",
    }
    for f, desc in essential_files.items():
        if _file_exists(f):
            report.add("Arquitetura", f"Arquivo: {desc}", Severity.OK, f"{desc} existe")
        else:
            report.add("Arquitetura", f"Arquivo: {desc}", Severity.ERROR,
                        f"{desc} ({f.name}) não existe",
                        fix=f"Criar {f.name}")

    # Verifica duplicações
    widget_files = list(SCRIPTS.glob("widget*.py"))
    if len(widget_files) > 2:
        names = [f.name for f in widget_files]
        report.add("Arquitetura", "Duplicação de widgets", Severity.WARN,
                    f"Múltiplos arquivos de widget: {', '.join(names)}",
                    fix="Consolidar widgets em widget_edge.py")
    else:
        report.add("Arquitetura", "Duplicação de widgets", Severity.OK,
                    "Sem duplicação de widgets")

    # Verifica se runtime files estão no lugar certo
    runtime_files = list(RUNTIME.glob("*.json"))
    orphaned = [f for f in runtime_files if f.name not in (
        "narrador_posicao.json", "narracao_estado.json", "widget_state.json",
        "widget_controle_geometria.json", "bridge_estado.json",
        "model_monitor.json", "parar_fala.flag", "tts_cmd.json",
        "mic_estado.json", "mic_pid.txt", "controle.json",
    )]
    if orphaned:
        names = [f.name for f in orphaned[:5]]
        report.add("Arquitetura", "Arquivos órfãos em runtime/", Severity.INFO,
                    f"Arquivos não mapeados: {', '.join(names)}")
    else:
        report.add("Arquitetura", "Arquivos em runtime/", Severity.OK,
                    "Todos os arquivos runtime são conhecidos")


def check_architecture_processes(report: AuditReport):
    """Verifica processos órfãos e conflitos."""
    try:
        r = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'",
             "get", "ProcessId,CommandLine", "/format:list"],
            capture_output=True, text=True, timeout=5
        )
        lines = r.stdout.strip().split("\n")
        processes = []
        current = {}
        for line in lines:
            line = line.strip()
            if line.startswith("ProcessId="):
                current["pid"] = line.split("=", 1)[1]
            elif line.startswith("CommandLine="):
                current["cmd"] = line.split("=", 1)[1]
                if current.get("pid") and current.get("cmd"):
                    processes.append(current)
                current = {}

        # Conta processos por script
        script_counts = {}
        for p in processes:
            cmd = p.get("cmd", "").lower()
            for script in ["jarvis_bridge", "tts_service",
                           "widget_edge", "widget_grafo", "system_guardian"]:
                if script in cmd:
                    script_counts[script] = script_counts.get(script, 0) + 1

        # Duplicidade: narrador_desktop.py não deve rodar (narrador vive no widget_edge)
        for p in processes:
            cmd = p.get("cmd", "").lower()
            if "narrador_desktop" in cmd:
                report.add("Arquitetura", "Duplicidade: narrador_desktop", Severity.WARN,
                            "narrador_desktop.py rodando — narrador oficial vive no widget_edge.py",
                            fix="Encerrar narrador_desktop.py (duplicidade)")

        for script, count in script_counts.items():
            if count > 1:
                report.add("Arquitetura", f"Processos duplicados: {script}", Severity.WARN,
                            f"{count} instâncias de {script} rodando",
                            fix=f"Matar instâncias extras de {script}")
            else:
                report.add("Arquitetura", f"Processo: {script}", Severity.OK,
                            f"{script} com 1 instância")

    except Exception as e:
        report.add("Arquitetura", "Verificação de processos", Severity.INFO,
                    f"Não foi possível verificar processos: {e}")


# ============================================================
# EVOLUÇÃO — o que o ecossistema precisa aprender
# ============================================================

def check_evolution(report: AuditReport):
    """Verifica saúde da base de aprendizados e sugere evolução."""
    aprendizados_dir = KNOWLEDGE / "aprendizados"
    if not aprendizados_dir.exists():
        report.add("Evolução", "Base de aprendizados", Severity.WARN,
                    "Diretório knowledge/aprendizados/ não existe",
                    fix="Criar diretório e começar a registrar aprendizados")
        return

    aprendizados = list(aprendizados_dir.glob("*.md"))
    report.add("Evolução", "Total de aprendizados", Severity.OK,
                f"{len(aprendizados)} aprendizados registrados")

    if len(aprendizados) == 0:
        return

    # Último aprendizado
    recent = sorted(aprendizados, key=lambda f: f.stat().st_mtime, reverse=True)
    last_age_days = (time.time() - recent[0].stat().st_mtime) / 86400
    if last_age_days < 1:
        report.add("Evolução", "Aprendizado diário", Severity.OK,
                    "Aprendizado registrado hoje")
    elif last_age_days < 7:
        report.add("Evolução", "Aprendizado semanal", Severity.OK,
                    f"Último aprendizado há {last_age_days:.0f} dias")
    else:
        report.add("Evolução", "Aprendizado semanal", Severity.WARN,
                    f"Último aprendizado há {last_age_days:.0f} dias — ecossistema parou de aprender",
                    fix="Rodar tarefas e registrar aprendizados regularmente")

    # Verifica categorias de aprendizado
    categories = {}
    for a in recent:
        try:
            content = a.read_text(encoding="utf-8")
            if "tipo:" in content:
                tipo = content.split("tipo:")[1].split("\n")[0].strip()
                categories[tipo] = categories.get(tipo, 0) + 1
        except Exception:
            pass

    if categories:
        cat_str = ", ".join(f"{k}:{v}" for k, v in categories.items())
        report.add("Evolução", "Categorias de aprendizado", Severity.OK,
                    f"Distribuição: {cat_str}")

    # Verifica memória
    memory_file = BASE / "conhecimento" / "memoria" / "memories.json"
    if not _file_exists(memory_file):
        memory_file = BASE / "conhecimento" / "memories.json"
    if _file_exists(memory_file):
        memories = _read_json(memory_file)
        if isinstance(memories, list):
            report.add("Evolução", "Memória episódica", Severity.OK,
                        f"{len(memories)} memórias episódicas")
        elif isinstance(memories, dict):
            total = sum(len(v) if isinstance(v, list) else 1 for v in memories.values())
            report.add("Evolução", "Memória episódica", Severity.OK,
                        f"{total} memórias episódicas")
    else:
        report.add("Evolução", "Memória episódica", Severity.WARN,
                    "memories.json não encontrado",
                    fix="Executar memory_engine.py para criar base de memória")

    # Verifica se há gaps conhecidos (arquivos de known issues)
    known_issues = list((KNOWLEDGE / "aprendizados").glob("*erro*")) + \
                   list((KNOWLEDGE / "aprendizados").glob("*bug*")) + \
                   list((KNOWLEDGE / "aprendizados").glob("*fix*"))
    if known_issues:
        report.add("Evolução", "Issues conhecidos", Severity.INFO,
                    f"{len(known_issues)} issues registrados na base")
    else:
        report.add("Evolução", "Issues conhecidos", Severity.OK,
                    "Nenhum issue pendente na base")


# ============================================================
# MAIN
# ============================================================

def run_audit(quick: bool = False) -> AuditReport:
    report = AuditReport(timestamp=datetime.now().isoformat(timespec="seconds"))

    check_services(report)
    check_widget_features(report)
    check_widget_error_filter(report)
    check_tts_integration(report)
    check_bridge_integration(report)
    check_model_monitor(report)
    check_narrator_health(report)
    check_guardian_coverage(report)
    check_guardian_desktop_protection(report)
    check_theme_sync(report)
    check_config_consistency(report)
    check_python_syntax(report)
    check_skills(report)
    check_knowledge_base(report)
    # Novas categorias
    check_integration_volume(report)
    check_integration_theme(report)
    check_integration_narrator(report)
    check_integration_model_monitor(report)
    check_architecture(report)
    check_architecture_processes(report)
    check_evolution(report)

    report.calculate_score()
    return report


def print_report(report: AuditReport, as_json: bool = False):
    if as_json:
        out = {
            "timestamp": report.timestamp,
            "score": report.score,
            "findings": [
                {
                    "category": f.category,
                    "check": f.check,
                    "severity": f.severity.value,
                    "message": f.message,
                    "fix": f.fix,
                    "file": f.file,
                }
                for f in report.findings
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    icons = {Severity.OK: "[OK]", Severity.WARN: "[!!]", Severity.ERROR: "[XX]", Severity.INFO: "[--]"}
    print(f"\n{'='*60}")
    print(f"  AUDITORIA DO ECOSSISTEMA — {report.timestamp}")
    print(f"  Score: {report.score}/100")
    print(f"{'='*60}\n")

    current_cat = None
    for f in report.findings:
        if f.category != current_cat:
            current_cat = f.category
            print(f"\n  {current_cat}:")
        print(f"    {icons[f.severity]} {f.check}: {f.message}")
        if f.fix:
            print(f"         -> {f.fix}")

    errors = sum(1 for f in report.findings if f.severity == Severity.ERROR)
    warns = sum(1 for f in report.findings if f.severity == Severity.WARN)
    oks = sum(1 for f in report.findings if f.severity == Severity.OK)
    print(f"\n{'='*60}")
    print(f"  Resumo: {oks} OK | {warns} WARN | {errors} ERROR")
    print(f"  Score: {report.score}/100")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Auditoria automática do ecossistema")
    ap.add_argument("--json", action="store_true", help="Saída em JSON")
    ap.add_argument("--quick", action="store_true", help="Apenas erros e warnings")
    args = ap.parse_args()

    report = run_audit(quick=args.quick)

    if args.quick:
        report.findings = [f for f in report.findings if f.severity in (Severity.ERROR, Severity.WARN)]

    print_report(report, as_json=args.json)

    sys.exit(1 if any(f.severity == Severity.ERROR for f in report.findings) else 0)
