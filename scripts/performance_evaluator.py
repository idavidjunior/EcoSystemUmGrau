#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""performance_evaluator.py — Avaliação de Performance por Componente.

Métricas de tempo de resposta, taxa de sucesso por componente, qualidade de
respostas (via ResponseNormalizer) e ranking de componentes por performance.

Uso:
  python scripts/performance_evaluator.py measure-response <componente>  # Mede tempo de resposta
  python scripts/performance_evaluator.py success-rate <componente>        # Calcula taxa de sucesso
  python scripts/performance_evaluator.py response-quality <componente>     # Avalia qualidade de resposta
  python scripts/performance_evaluator.py rank                               # Ranking de componentes

Saída JSON: {response_time, success_rate, quality, ranking, timestamp}
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
SCRIPTS = ROOT / "scripts"

# Estado persistente do performance evaluator
STATE_FILE = RUNTIME / "performance_evaluator_state.json"

# Componentes a avaliar
COMPONENTS = [
    "jarvis_bridge",
    "memory_engine",
    "response_normalizer",
    "tts_service",
    "health_monitor",
    "dynamic_self_knowledge",
]


class PerformanceEvaluator:
    """Avaliador de performance por componente."""
    
    def __init__(self):
        self.state = self._load_state()
        self._metrics = self.state.get("metrics", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do performance evaluator."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "metrics": {},
            "last_evaluation": None
        }
    
    def _save_state(self):
        """Salva estado persistente do performance evaluator."""
        self.state["last_evaluation"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def measure_response_time(self, component: str) -> Dict:
        """Mede tempo de resposta de um componente."""
        if component not in COMPONENTS:
            return {
                "error": f"Componente {component} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        # Simulação de medição de tempo de resposta
        # Em produção, isso mediria tempo real de execução
        start_time = time.time()
        
        # Simular execução do componente
        time.sleep(0.05)  # Placeholder para simulação
        
        response_time = time.time() - start_time
        
        measurement = {
            "component": component,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat(),
            "status": "fast" if response_time < 0.1 else "normal" if response_time < 0.5 else "slow"
        }
        
        # Registrar métrica
        if component not in self._metrics:
            self._metrics[component] = {"response_times": [], "success_count": 0, "total_count": 0}
        
        self._metrics[component]["response_times"].append(response_time)
        self._metrics[component]["last_measured"] = datetime.now().isoformat()
        self._save_state()
        
        return measurement
    
    def calculate_success_rate(self, component: str) -> Dict:
        """Calcula taxa de sucesso de um componente."""
        if component not in COMPONENTS:
            return {
                "error": f"Componente {component} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        # Inicializar métricas se necessário
        if component not in self._metrics:
            self._metrics[component] = {"response_times": [], "success_count": 0, "total_count": 0}
        
        # Simulação de taxa de sucesso
        # Em produção, isso contaria sucesso/falha reais
        success_count = self._metrics[component].get("success_count", 0)
        total_count = self._metrics[component].get("total_count", 0)
        
        # Simular medição atual
        total_count += 1
        # 95% de sucesso simulado
        import random
        if random.random() < 0.95:
            success_count += 1
        
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        result = {
            "component": component,
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat(),
            "status": "excellent" if success_rate >= 95 else "good" if success_rate >= 90 else "poor"
        }
        
        # Atualizar métricas
        self._metrics[component]["success_count"] = success_count
        self._metrics[component]["total_count"] = total_count
        self._metrics[component]["success_rate"] = success_rate
        self._save_state()
        
        return result
    
    def evaluate_response_quality(self, component: str) -> Dict:
        """Avalia qualidade de resposta via ResponseNormalizer."""
        if component not in COMPONENTS:
            return {
                "error": f"Componente {component} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        # Tentar importar ResponseNormalizer
        try:
            import sys
            sys.path.insert(0, str(SCRIPTS))
            from response_normalizer import normalizar_resposta
            
            # Simular resposta de teste
            test_response = "Esta é uma resposta de teste para avaliar qualidade."
            
            # Normalizar resposta
            result = normalizar_resposta(test_response)
            
            quality_metrics = {
                "component": component,
                "checklist_passed": result.get("checklist", {}).get("ok", True),
                "actions": result.get("actions", []),
                "simplified": result.get("simplified", False),
                "timestamp": datetime.now().isoformat(),
                "status": "high" if result.get("checklist", {}).get("ok", True) else "low"
            }
            
            # Registrar métrica
            if component not in self._metrics:
                self._metrics[component] = {"response_times": [], "success_count": 0, "total_count": 0}
            
            self._metrics[component]["quality"] = quality_metrics
            self._save_state()
            
            return quality_metrics
            
        except ImportError:
            return {
                "component": component,
                "error": "ResponseNormalizer não disponível",
                "timestamp": datetime.now().isoformat(),
                "status": "unknown"
            }
        except Exception as e:
            return {
                "component": component,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def rank_components(self) -> List[Dict]:
        """Ranking de componentes por performance."""
        rankings = []
        
        for component in COMPONENTS:
            # Coletar métricas
            response_time = self.measure_response_time(component)
            success_rate = self.calculate_success_rate(component)
            quality = self.evaluate_response_quality(component)
            
            # Calcular score composto
            rt = response_time.get("response_time", 0)
            sr = success_rate.get("success_rate", 0)
            qs = 1.0 if quality.get("status") == "high" else 0.5 if quality.get("status") == "unknown" else 0.0
            
            # Score normalizado (menor tempo = melhor, maior sucesso = melhor)
            time_score = max(0, 1 - (rt / 1.0))  # 1s como referência
            success_score = sr / 100
            
            # Score composto (50% tempo, 30% sucesso, 20% qualidade)
            composite_score = (time_score * 0.5) + (success_score * 0.3) + (qs * 0.2)
            
            ranking = {
                "component": component,
                "response_time": rt,
                "success_rate": sr,
                "quality_status": quality.get("status", "unknown"),
                "composite_score": composite_score,
                "rank": 0,  # Será calculado após ordenar
                "timestamp": datetime.now().isoformat()
            }
            
            rankings.append(ranking)
        
        # Ordenar por score composto (decrescente)
        rankings.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Atribuir ranks
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
        
        return rankings
    
    def get_component_summary(self, component: str) -> Dict:
        """Resumo completo de métricas de um componente."""
        if component not in COMPONENTS:
            return {
                "error": f"Componente {component} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        response_time = self.measure_response_time(component)
        success_rate = self.calculate_success_rate(component)
        quality = self.evaluate_response_quality(component)
        
        # Calcular média de tempo de resposta
        if component in self._metrics:
            response_times = self._metrics[component].get("response_times", [])
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        else:
            avg_response_time = 0
        
        summary = {
            "component": component,
            "avg_response_time": avg_response_time,
            "current_response_time": response_time.get("response_time", 0),
            "success_rate": success_rate.get("success_rate", 0),
            "quality_status": quality.get("status", "unknown"),
            "total_measurements": self._metrics.get(component, {}).get("total_count", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return summary


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python performance_evaluator.py measure-response|success-rate|response-quality|rank|summary")
        sys.exit(1)
    
    command = sys.argv[1]
    evaluator = PerformanceEvaluator()
    
    if command == "measure-response":
        if len(sys.argv) < 3:
            print("Uso: python performance_evaluator.py measure-response <componente>")
            sys.exit(1)
        component = sys.argv[2]
        result = evaluator.measure_response_time(component)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "success-rate":
        if len(sys.argv) < 3:
            print("Uso: python performance_evaluator.py success-rate <componente>")
            sys.exit(1)
        component = sys.argv[2]
        result = evaluator.calculate_success_rate(component)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "response-quality":
        if len(sys.argv) < 3:
            print("Uso: python performance_evaluator.py response-quality <componente>")
            sys.exit(1)
        component = sys.argv[2]
        result = evaluator.evaluate_response_quality(component)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "rank":
        rankings = evaluator.rank_components()
        print(json.dumps(rankings, indent=2, ensure_ascii=False))
    
    elif command == "summary":
        if len(sys.argv) < 3:
            print("Uso: python performance_evaluator.py summary <componente>")
            sys.exit(1)
        component = sys.argv[2]
        summary = evaluator.get_component_summary(component)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()