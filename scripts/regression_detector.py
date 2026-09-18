#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""regression_detector.py — Detecção de Regressão.

Comparação de performance ao longo do tempo, detecção de degradação de qualidade,
alertas de regressão funcional e baseline automático de performance.

Uso:
  python scripts/regression_detector.py measure <componente>  # Mede performance
  python scripts/regression_detector.py compare              # Compara com baseline
  python scripts/regression_detector.py detect               # Detecta regressão
  python scripts/regression_detector.py update-baseline      # Atualiza baseline

Saída JSON: {performance, baseline, comparison, regressao, timestamp}
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

# Estado persistente do regression detector
STATE_FILE = RUNTIME / "regression_detector_state.json"
BASELINE_FILE = RUNTIME / "regression_baseline.json"

# Componentes a monitorar
COMPONENTS = {
    "jarvis_bridge": {"type": "response_time", "threshold": 2.0},
    "memory_engine": {"type": "response_time", "threshold": 1.0},
    "response_normalizer": {"type": "response_time", "threshold": 0.5},
    "tts_service": {"type": "response_time", "threshold": 5.0},
}


class RegressionDetector:
    """Detector de regressão de performance."""
    
    def __init__(self):
        self.state = self._load_state()
        self._baseline = self._load_baseline()
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do regression detector."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "measurements": [],
            "regressions_detected": [],
            "last_check": None
        }
    
    def _load_baseline(self) -> dict:
        """Carrega baseline de performance."""
        if BASELINE_FILE.exists():
            try:
                with open(BASELINE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_state(self):
        """Salva estado persistente do regression detector."""
        self.state["last_check"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def _save_baseline(self):
        """Salva baseline de performance."""
        try:
            with open(BASELINE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._baseline, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar baseline: {e}")
    
    def measure_performance(self, component: str) -> Dict:
        """Mede performance de um componente específico."""
        if component not in COMPONENTS:
            return {
                "error": f"Componente {component} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        component_config = COMPONENTS[component]
        measurement_type = component_config["type"]
        
        if measurement_type == "response_time":
            # Simulação de medição de tempo de resposta
            # Em produção, isso mediria tempo real de execução
            start_time = time.time()
            
            # Simular execução do componente
            time.sleep(0.1)  # Placeholder
            
            response_time = time.time() - start_time
            
            measurement = {
                "component": component,
                "type": measurement_type,
                "value": response_time,
                "threshold": component_config["threshold"],
                "timestamp": datetime.now().isoformat(),
                "status": "ok" if response_time < component_config["threshold"] else "degraded"
            }
        else:
            measurement = {
                "component": component,
                "type": measurement_type,
                "value": 0,
                "timestamp": datetime.now().isoformat(),
                "status": "unknown"
            }
        
        # Registrar medição
        self.state["measurements"].append(measurement)
        self._save_state()
        
        return measurement
    
    def compare_with_baseline(self, current: Dict, baseline: Dict) -> Dict:
        """Compara medição atual com baseline."""
        component = current.get("component", "")
        current_value = current.get("value", 0)
        
        if component not in baseline:
            return {
                "component": component,
                "comparison": "no_baseline",
                "status": "unknown",
                "message": "Nenhum baseline disponível para comparação"
            }
        
        baseline_value = baseline[component].get("value", 0)
        threshold = baseline[component].get("threshold", 0)
        
        # Calcular diferença percentual
        if baseline_value > 0:
            diff_percent = ((current_value - baseline_value) / baseline_value) * 100
        else:
            diff_percent = 0
        
        # Determinar status
        if current_value > threshold:
            status = "degraded"
        elif diff_percent > 20:  # > 20% pior que baseline
            status = "regression"
        elif diff_percent < -20:  # > 20% melhor que baseline
            status = "improved"
        else:
            status = "stable"
        
        return {
            "component": component,
            "current_value": current_value,
            "baseline_value": baseline_value,
            "diff_percent": diff_percent,
            "threshold": threshold,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_regression(self) -> List[Dict]:
        """Detecta regressão em todos os componentes."""
        regressions = []
        
        for component in COMPONENTS.keys():
            # Medir performance atual
            current = self.measure_performance(component)
            
            # Comparar com baseline
            if component in self._baseline:
                comparison = self.compare_with_baseline(current, self._baseline[component])
                
                if comparison["status"] in ["regression", "degraded"]:
                    regressions.append({
                        "component": component,
                        "current": current,
                        "comparison": comparison,
                        "severity": "high" if comparison["status"] == "degraded" else "medium",
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Registrar regressões detectadas
        if regressions:
            self.state["regressions_detected"].extend(regressions)
            self._save_state()
        
        return regressions
    
    def update_baseline(self) -> bool:
        """Atualiza baseline de performance."""
        new_baseline = {}
        
        for component in COMPONENTS.keys():
            # Medir performance atual
            measurement = self.measure_performance(component)
            
            new_baseline[component] = {
                "value": measurement.get("value", 0),
                "threshold": measurement.get("threshold", 0),
                "timestamp": measurement.get("timestamp"),
                "status": measurement.get("status")
            }
        
        self._baseline = new_baseline
        self._save_baseline()
        
        print(f"Baseline atualizado com {len(new_baseline)} componentes")
        return True
    
    def get_trend(self, component: str, window: int = 10) -> Dict:
        """Calcula tendência de performance de um componente."""
        measurements = [
            m for m in self.state["measurements"]
            if m.get("component") == component
        ]
        
        if len(measurements) < 2:
            return {
                "component": component,
                "trend": "insufficient_data",
                "message": "Dados insuficientes para calcular tendência"
            }
        
        # Pegar últimas N medições
        recent_measurements = measurements[-window:]
        values = [m.get("value", 0) for m in recent_measurements]
        
        # Calcular média móvel
        avg_first_half = sum(values[:len(values)//2]) / (len(values)//2)
        avg_second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        # Determinar tendência
        if avg_second_half > avg_first_half * 1.1:
            trend = "degrading"
        elif avg_second_half < avg_first_half * 0.9:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "component": component,
            "trend": trend,
            "current_avg": avg_second_half,
            "previous_avg": avg_first_half,
            "change_percent": ((avg_second_half - avg_first_half) / avg_first_half) * 100 if avg_first_half > 0 else 0,
            "sample_size": len(recent_measurements),
            "timestamp": datetime.now().isoformat()
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python regression_detector.py measure|compare|detect|update-baseline|trend")
        sys.exit(1)
    
    command = sys.argv[1]
    detector = RegressionDetector()
    
    if command == "measure":
        if len(sys.argv) < 3:
            print("Uso: python regression_detector.py measure <componente>")
            sys.exit(1)
        component = sys.argv[2]
        result = detector.measure_performance(component)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "compare":
        # Medir todos e comparar com baseline
        comparisons = []
        for component in COMPONENTS.keys():
            current = detector.measure_performance(component)
            if component in detector._baseline:
                comparison = detector.compare_with_baseline(current, detector._baseline[component])
                comparisons.append(comparison)
        print(json.dumps(comparisons, indent=2, ensure_ascii=False))
    
    elif command == "detect":
        regressions = detector.detect_regression()
        print(json.dumps(regressions, indent=2, ensure_ascii=False))
    
    elif command == "update-baseline":
        success = detector.update_baseline()
        sys.exit(0 if success else 1)
    
    elif command == "trend":
        if len(sys.argv) < 3:
            print("Uso: python regression_detector.py trend <componente>")
            sys.exit(1)
        component = sys.argv[2]
        trend = detector.get_trend(component)
        print(json.dumps(trend, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()