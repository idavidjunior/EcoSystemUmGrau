#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""error_analyzer.py — Análise Automática de Erros.

Coleta automática de logs de erro, classificação por tipo e severidade,
análise de padrões de falha e geração de relatórios de autocrítica.

Uso:
  python scripts/error_analyzer.py collect          # Coleta erros
  python scripts/error_analyzer.py analyze          # Analisa padrões
  python scripts/error_analyzer.py self-critique    # Gera autocrítica
  python scripts/error_analyzer.py status           # Status de erros

Saída JSON: {erros, classificacao, padroes, autocrítica, timestamp}
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
CONHECIMENTO = ROOT / "conhecimento"
APRENDIZADOS = CONHECIMENTO / "aprendizados"

# Estado persistente do error analyzer
STATE_FILE = RUNTIME / "error_analyzer_state.json"

# Logs a monitorar
LOG_FILES = [
    RUNTIME / "tts_service.log",
    RUNTIME / "supervisao.log",
    RUNTIME / "maestro.log",
    RUNTIME / "widget_edge.log",
]

# Padrões de erro comuns
ERROR_PATTERNS = {
    "permission_denied": r"(Permission denied|Access denied|PermissionError)",
    "connection_failed": r"(Connection failed|ConnectionError|Network error)",
    "timeout": r"(Timeout|timed out|timeout)",
    "not_found": r"(Not found|FileNotFoundError|404)",
    "import_error": r"(ImportError|ModuleNotFoundError)",
    "syntax_error": r"(SyntaxError|IndentationError)",
    "runtime_error": r"(RuntimeError|ValueError|TypeError)",
    "memory_error": r"(MemoryError|OutOfMemory)",
    "api_error": r"(API error|APIError|HTTP error)",
    "validation_error": r"(ValidationError|Validation failed)",
}


class ErrorAnalyzer:
    """Analisador automático de erros do ecossistema."""
    
    def __init__(self):
        self.state = self._load_state()
        self._errors_db = self.state.get("errors_db", [])
        self._patterns_db = self.state.get("patterns_db", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do error analyzer."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "errors_db": [],
            "patterns_db": {},
            "last_analysis": None,
            "total_errors_analyzed": 0
        }
    
    def _save_state(self):
        """Salva estado persistente do error analyzer."""
        self.state["last_analysis"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def collect_errors(self, timeframe: str = "24h") -> List[Dict]:
        """Coleta erros dos logs no timeframe especificado."""
        errors = []
        
        # Parse timeframe
        hours = 24
        if timeframe.endswith("h"):
            hours = int(timeframe[:-1])
        elif timeframe.endswith("d"):
            hours = int(timeframe[:-1]) * 24
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for log_file in LOG_FILES:
            if not log_file.exists():
                continue
            
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Extrair timestamp se disponível
                        timestamp = self._extract_timestamp(line)
                        if timestamp and timestamp < cutoff_time:
                            continue
                        
                        # Detectar se é erro
                        if self._is_error_line(line):
                            error_entry = {
                                "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                "source": log_file.name,
                                "message": line,
                                "severity": self._classify_severity(line),
                                "type": self._classify_error_type(line)
                            }
                            errors.append(error_entry)
                            
            except Exception as e:
                print(f"Erro ao ler {log_file}: {e}")
        
        # Atualizar banco de erros
        self._errors_db.extend(errors)
        self.state["total_errors_analyzed"] = len(self._errors_db)
        self._save_state()
        
        return errors
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extrai timestamp de uma linha de log."""
        # Padrões comuns de timestamp
        patterns = [
            r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]",
            r"\[(\d{2}:\d{2}:\d{2})\]",
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                ts_str = match.group(1)
                try:
                    if "T" in ts_str:
                        return datetime.fromisoformat(ts_str)
                    elif "-" in ts_str:
                        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        # Apenas hora, usar data atual
                        today = datetime.now().date()
                        time_part = datetime.strptime(ts_str, "%H:%M:%S").time()
                        return datetime.combine(today, time_part)
                except Exception:
                    continue
        
        return None
    
    def _is_error_line(self, line: str) -> bool:
        """Verifica se a linha é um erro."""
        error_indicators = [
            "error", "Error", "ERROR",
            "exception", "Exception", "EXCEPTION",
            "failed", "Failed", "FAILED",
            "crash", "Crash", "CRASH",
            "traceback", "Traceback", "TRACEBACK",
            "permission denied", "Permission denied",
            "not found", "Not found",
        ]
        
        return any(indicator in line.lower() for indicator in error_indicators)
    
    def _classify_severity(self, line: str) -> str:
        """Classifica severidade do erro."""
        line_lower = line.lower()
        
        if any(critical in line_lower for critical in ["critical", "fatal", "crash", "exception"]):
            return "critical"
        elif any(high in line_lower for high in ["error", "failed", "timeout"]):
            return "high"
        elif any(medium in line_lower for medium in ["warning", "warn", "deprecated"]):
            return "medium"
        else:
            return "low"
    
    def _classify_error_type(self, line: str) -> str:
        """Classifica tipo do erro baseado em padrões."""
        for error_type, pattern in ERROR_PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                return error_type
        
        return "unknown"
    
    def classify_error(self, error: Dict) -> Dict:
        """Classifica um erro específico."""
        result = {
            "original": error,
            "severity": error.get("severity", "unknown"),
            "type": error.get("type", "unknown"),
            "category": self._categorize_error(error),
            "action_required": self._determine_action(error)
        }
        return result
    
    def _categorize_error(self, error: Dict) -> str:
        """Categoriza erro em grupos funcionais."""
        error_type = error.get("type", "")
        source = error.get("source", "")
        
        if "permission" in error_type:
            return "access_control"
        elif "connection" in error_type or "network" in error_type:
            return "network"
        elif "memory" in error_type:
            return "resource"
        elif "api" in error_type:
            return "external_service"
        elif "validation" in error_type:
            return "data_quality"
        elif "import" in error_type:
            return "dependency"
        elif "tts" in source.lower():
            return "tts_service"
        elif "widget" in source.lower():
            return "ui_component"
        else:
            return "general"
    
    def _determine_action(self, error: Dict) -> str:
        """Determina ação necessária para o erro."""
        severity = error.get("severity", "")
        error_type = error.get("type", "")
        
        if severity == "critical":
            return "immediate_investigation"
        elif error_type == "permission_denied":
            return "permission_fix"
        elif error_type == "connection_failed":
            return "network_check"
        elif error_type == "timeout":
            return "timeout_adjustment"
        elif error_type == "not_found":
            return "file_check"
        elif error_type == "import_error":
            return "dependency_check"
        else:
            return "monitor"
    
    def detect_patterns(self, errors: List[Dict]) -> List[Dict]:
        """Detecta padrões de falha nos erros."""
        patterns = []
        
        if not errors:
            return patterns
        
        # Contar erros por tipo
        type_counts = {}
        for error in errors:
            error_type = error.get("type", "unknown")
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        # Identificar padrões frequentes
        for error_type, count in type_counts.items():
            if count >= 3:  # Padrão se ocorrer 3+ vezes
                patterns.append({
                    "type": error_type,
                    "frequency": count,
                    "severity": self._get_pattern_severity(error_type, errors),
                    "trend": self._calculate_trend(error_type, errors)
                })
        
        # Atualizar banco de padrões
        for pattern in patterns:
            pattern_key = pattern["type"]
            if pattern_key not in self._patterns_db:
                self._patterns_db[pattern_key] = {
                    "first_seen": datetime.now().isoformat(),
                    "occurrences": 0,
                    "trend": []
                }
            self._patterns_db[pattern_key]["occurrences"] += pattern["frequency"]
            self._patterns_db[pattern_key]["last_seen"] = datetime.now().isoformat()
            self._patterns_db[pattern_key]["trend"].append({
                "timestamp": datetime.now().isoformat(),
                "count": pattern["frequency"]
            })
        
        self._save_state()
        return patterns
    
    def _get_pattern_severity(self, error_type: str, errors: List[Dict]) -> str:
        """Determina severidade do padrão."""
        errors_of_type = [e for e in errors if e.get("type") == error_type]
        severities = [e.get("severity", "low") for e in errors_of_type]
        
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"
    
    def _calculate_trend(self, error_type: str, errors: List[Dict]) -> str:
        """Calcula tendência do padrão."""
        errors_of_type = [e for e in errors if e.get("type") == error_type]
        
        if len(errors_of_type) < 2:
            return "stable"
        
        # Simples: comparar primeira metade com segunda metade
        mid = len(errors_of_type) // 2
        first_half = errors_of_type[:mid]
        second_half = errors_of_type[mid:]
        
        if len(second_half) > len(first_half):
            return "increasing"
        elif len(second_half) < len(first_half):
            return "decreasing"
        else:
            return "stable"
    
    def generate_self_critique(self) -> Dict:
        """Gera relatório de autocrítica."""
        # Coletar erros recentes
        recent_errors = self.collect_errors("24h")
        
        # Classificar erros
        classified_errors = [self.classify_error(e) for e in recent_errors]
        
        # Detectar padrões
        patterns = self.detect_patterns(recent_errors)
        
        # Gerar autocrítica
        critique = {
            "timestamp": datetime.now().isoformat(),
            "errors_analyzed": len(recent_errors),
            "severity_distribution": self._calculate_severity_distribution(classified_errors),
            "top_error_types": self._get_top_error_types(classified_errors),
            "patterns_detected": patterns,
            "recommendations": self._generate_recommendations(classified_errors, patterns),
            "overall_health": self._calculate_overall_health(classified_errors, patterns)
        }
        
        return critique
    
    def _calculate_severity_distribution(self, errors: List[Dict]) -> Dict:
        """Calcula distribuição de severidade."""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for error in errors:
            severity = error.get("severity", "low")
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _get_top_error_types(self, errors: List[Dict]) -> List[Dict]:
        """Identifica tipos de erro mais frequentes."""
        type_counts = {}
        for error in errors:
            error_type = error.get("type", "unknown")
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        # Ordenar por frequência
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{"type": t, "count": c} for t, c in sorted_types[:5]]
    
    def _generate_recommendations(self, errors: List[Dict], patterns: List[Dict]) -> List[str]:
        """Gera recomendações baseadas em erros e padrões."""
        recommendations = []
        
        # Recomendações baseadas em severidade
        severity_dist = self._calculate_severity_distribution(errors)
        if severity_dist["critical"] > 0:
            recommendations.append("Investigar erros críticos imediatamente - prioridade máxima")
        if severity_dist["high"] > 5:
            recommendations.append("Alta incidência de erros de alta severidade - revisar código afetado")
        
        # Recomendações baseadas em padrões
        for pattern in patterns:
            if pattern["trend"] == "increasing":
                recommendations.append(f"Padrão {pattern['type']} está crescendo - investigar causa raiz")
            if pattern["severity"] == "critical":
                recommendations.append(f"Padrão crítico {pattern['type']} requer correção urgente")
        
        # Recomendações genéricas
        if len(errors) > 20:
            recommendations.append("Volume alto de erros - considerar aumento de logging e monitoramento")
        
        if not recommendations:
            recommendations.append("Nenhuma recomendação específica - sistema estável")
        
        return recommendations
    
    def _calculate_overall_health(self, errors: List[Dict], patterns: List[Dict]) -> str:
        """Calcula saúde geral do sistema."""
        severity_dist = self._calculate_severity_distribution(errors)
        
        if severity_dist["critical"] > 0:
            return "critical"
        elif severity_dist["high"] > 5 or any(p["severity"] == "critical" for p in patterns):
            return "degraded"
        elif severity_dist["high"] > 0 or any(p["trend"] == "increasing" for p in patterns):
            return "warning"
        else:
            return "healthy"


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python error_analyzer.py collect|analyze|self-critique|status")
        sys.exit(1)
    
    command = sys.argv[1]
    analyzer = ErrorAnalyzer()
    
    if command == "collect":
        timeframe = sys.argv[2] if len(sys.argv) > 2 else "24h"
        errors = analyzer.collect_errors(timeframe)
        print(json.dumps(errors, indent=2, ensure_ascii=False))
    
    elif command == "analyze":
        errors = analyzer.collect_errors("24h")
        patterns = analyzer.detect_patterns(errors)
        print(json.dumps(patterns, indent=2, ensure_ascii=False))
    
    elif command == "self-critique":
        critique = analyzer.generate_self_critique()
        print(json.dumps(critique, indent=2, ensure_ascii=False))
    
    elif command == "status":
        print(json.dumps({
            "total_errors_analyzed": analyzer.state.get("total_errors_analyzed", 0),
            "patterns_tracked": len(analyzer.state.get("patterns_db", {})),
            "last_analysis": analyzer.state.get("last_analysis")
        }, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()