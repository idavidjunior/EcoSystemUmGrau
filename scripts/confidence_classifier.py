#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""confidence_classifier.py — Classificação de Confiança por Domínio.

Classificação de confiança por domínio de conhecimento, identificação de
domínios de alta/baixa confiança, recomendação de investimento em aprendizado
e visualização de mapa de confiança.

Uso:
  python scripts/confidence_classifier.py classify <dominio>  # Classifica confiança
  python scripts/confidence_classifier.py identify-low         # Identifica baixa confiança
  python scripts/confidence_classifier.py recommend-investment  # Recomenda investimento
  python scripts/confidence_classifier.py visualize            # Visualiza mapa de confiança

Saída JSON: {confianca, dominios, recomendacoes, mapa, timestamp}
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
LER_RUNTIME = ROOT / "ler-runtime"

# Estado persistente do confidence classifier
STATE_FILE = RUNTIME / "confidence_classifier_state.json"

# Domínios de conhecimento
DOMAINS = [
    "android",
    "ecossistema",
    "desenvolvimento",
    "internet",
    "memoria",
    "multimidia",
    "nucleo",
    "os",
    "financeiro",
    "devops",
]


class ConfidenceClassifier:
    """Classificador de confiança por domínio."""
    
    def __init__(self):
        self.state = self._load_state()
        self._confidence_db = self.state.get("confidence_db", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do confidence classifier."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "confidence_db": {},
            "last_classification": None
        }
    
    def _save_state(self):
        """Salva estado persistente do confidence classifier."""
        self.state["last_classification"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def classify_domain_confidence(self, domain: str) -> Dict:
        """Classifica confiança de um domínio específico."""
        if domain not in DOMAINS:
            return {
                "error": f"Domínio {domain} não configurado",
                "timestamp": datetime.now().isoformat()
            }
        
        # Carregar knowledge graph
        knowledge_file = LER_RUNTIME / "knowledge" / "knowledge_graph.json"
        
        if not knowledge_file.exists():
            return {
                "domain": domain,
                "confidence": "unknown",
                "score": 0,
                "message": "Knowledge graph não encontrado",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                knowledge_graph = json.load(f)
        except Exception:
            return {
                "domain": domain,
                "confidence": "unknown",
                "score": 0,
                "message": "Erro ao carregar knowledge graph",
                "timestamp": datetime.now().isoformat()
            }
        
        # Contar padrões relevantes ao domínio
        patterns = knowledge_graph.get("patterns", [])
        domain_patterns = []
        
        for pattern in patterns:
            source = pattern.get("source", "").lower()
            
            # Mapear source para domínio
            if domain == "android" and "android" in source:
                domain_patterns.append(pattern)
            elif domain == "ecossistema" and "opencode" in source:
                domain_patterns.append(pattern)
            elif domain == "desenvolvimento" and ("devops" in source or "node" in source):
                domain_patterns.append(pattern)
            elif domain == "multimidia" and "mp3player" in source:
                domain_patterns.append(pattern)
            elif domain == "ler" and "ler" in source:
                domain_patterns.append(pattern)
        
        # Calcular score de confiança
        pattern_count = len(domain_patterns)
        
        if pattern_count >= 50:
            confidence = "very_high"
            score = 100
        elif pattern_count >= 30:
            confidence = "high"
            score = 80
        elif pattern_count >= 20:
            confidence = "moderate"
            score = 60
        elif pattern_count >= 10:
            confidence = "low"
            score = 40
        elif pattern_count >= 5:
            confidence = "very_low"
            score = 20
        else:
            confidence = "minimal"
            score = 10
        
        classification = {
            "domain": domain,
            "confidence": confidence,
            "score": score,
            "pattern_count": pattern_count,
            "timestamp": datetime.now().isoformat()
        }
        
        # Atualizar banco de confiança
        self._confidence_db[domain] = classification
        self._save_state()
        
        return classification
    
    def identify_low_confidence_domains(self) -> List[Dict]:
        """Identifica domínios de baixa confiança."""
        low_confidence = []
        
        for domain in DOMAINS:
            classification = self.classify_domain_confidence(domain)
            
            if classification.get("confidence") in ["very_low", "minimal"]:
                low_confidence.append({
                    "domain": domain,
                    "confidence": classification.get("confidence"),
                    "score": classification.get("score"),
                    "pattern_count": classification.get("pattern_count"),
                    "priority": "critical"
                })
            elif classification.get("confidence") == "low":
                low_confidence.append({
                    "domain": domain,
                    "confidence": classification.get("confidence"),
                    "score": classification.get("score"),
                    "pattern_count": classification.get("pattern_count"),
                    "priority": "high"
                })
        
        # Ordenar por score (ascendente)
        low_confidence.sort(key=lambda x: x["score"])
        
        return low_confidence
    
    def recommend_learning_investment(self) -> List[Dict]:
        """Recomenda investimento em aprendizado."""
        low_confidence = self.identify_low_confidence_domains()
        
        recommendations = []
        
        for domain_info in low_confidence:
            domain = domain_info["domain"]
            priority = domain_info["priority"]
            score = domain_info["score"]
            
            # Calcular urgência baseada em score e prioridade
            if priority == "critical":
                urgency = "immediate"
            elif priority == "high":
                urgency = "soon"
            else:
                urgency = "eventual"
            
            recommendations.append({
                "domain": domain,
                "current_confidence": domain_info["confidence"],
                "current_score": score,
                "recommended_action": f"Expandir conhecimento em {domain}",
                "urgency": urgency,
                "investment_priority": priority
            })
        
        return recommendations
    
    def visualize_confidence_map(self) -> Dict:
        """Visualiza mapa de confiança."""
        confidence_map = {}
        
        for domain in DOMAINS:
            classification = self.classify_domain_confidence(domain)
            confidence_map[domain] = {
                "confidence": classification.get("confidence"),
                "score": classification.get("score"),
                "pattern_count": classification.get("pattern_count")
            }
        
        # Calcular estatísticas
        scores = [d["score"] for d in confidence_map.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        high_count = sum(1 for d in confidence_map.values() if d["confidence"] in ["very_high", "high"])
        low_count = sum(1 for d in confidence_map.values() if d["confidence"] in ["very_low", "minimal", "low"])
        
        visualization = {
            "confidence_map": confidence_map,
            "statistics": {
                "average_score": avg_score,
                "high_confidence_domains": high_count,
                "low_confidence_domains": low_count,
                "total_domains": len(confidence_map)
            },
            "overall_health": "good" if avg_score >= 60 else "moderate" if avg_score >= 40 else "poor",
            "timestamp": datetime.now().isoformat()
        }
        
        return visualization
    
    def get_domain_summary(self, domain: str) -> Dict:
        """Resumo completo de um domínio."""
        classification = self.classify_domain_confidence(domain)
        
        if "error" in classification:
            return classification
        
        # Carregar knowledge graph para detalhes adicionais
        knowledge_file = LER_RUNTIME / "knowledge" / "knowledge_graph.json"
        
        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    knowledge_graph = json.load(f)
                
                # Contar tipos de padrões no domínio
                patterns = knowledge_graph.get("patterns", [])
                domain_patterns = []
                
                for pattern in patterns:
                    source = pattern.get("source", "").lower()
                    
                    if domain == "android" and "android" in source:
                        domain_patterns.append(pattern)
                    elif domain == "ecossistema" and "opencode" in source:
                        domain_patterns.append(pattern)
                    elif domain == "desenvolvimento" and ("devops" in source or "node" in source):
                        domain_patterns.append(pattern)
                    elif domain == "multimidia" and "mp3player" in source:
                        domain_patterns.append(pattern)
                    elif domain == "ler" and "ler" in source:
                        domain_patterns.append(pattern)
                
                # Contar tipos de ações
                action_types = Counter()
                for pattern in domain_patterns:
                    action = pattern.get("action", "unknown")
                    action_types[action] += 1
                
                classification["action_types"] = dict(action_types)
                classification["total_patterns"] = len(domain_patterns)
                
            except Exception:
                pass
        
        return classification


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python confidence_classifier.py classify|identify-low|recommend-investment|visualize|summary")
        sys.exit(1)
    
    command = sys.argv[1]
    classifier = ConfidenceClassifier()
    
    if command == "classify":
        if len(sys.argv) < 3:
            print("Uso: python confidence_classifier.py classify <dominio>")
            sys.exit(1)
        domain = sys.argv[2]
        result = classifier.classify_domain_confidence(domain)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "identify-low":
        low = classifier.identify_low_confidence_domains()
        print(json.dumps(low, indent=2, ensure_ascii=False))
    
    elif command == "recommend-investment":
        recommendations = classifier.recommend_learning_investment()
        print(json.dumps(recommendations, indent=2, ensure_ascii=False))
    
    elif command == "visualize":
        viz = classifier.visualize_confidence_map()
        print(json.dumps(viz, indent=2, ensure_ascii=False))
    
    elif command == "summary":
        if len(sys.argv) < 3:
            print("Uso: python confidence_classifier.py summary <dominio>")
            sys.exit(1)
        domain = sys.argv[2]
        summary = classifier.get_domain_summary(domain)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()