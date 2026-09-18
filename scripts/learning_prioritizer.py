#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""learning_prioritizer.py — Priorização de Aprendizado.

Priorização de aprendizado baseada em lacunas e confiança, geração de roadmap
de aprendizado, sugestão de skills a desenvolver e integração com agente
10-Aprendizado.

Uso:
  python scripts/learning_prioritizer.py prioritize       # Prioriza aprendizado
  python scripts/learning_prioritizer.py generate-roadmap  # Gera roadmap
  python scripts/learning_prioritizer.py suggest-skills   # Sugere skills
  python scripts/learning_prioritizer.py integrate-agent10 # Integra com agente 10

Saída JSON: {prioridades, roadmap, skills, integracao, timestamp}
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
SCRIPTS = ROOT / "scripts"

# Estado persistente do learning prioritizer
STATE_FILE = RUNTIME / "learning_prioritizer_state.json"

# Importar detectores de metacognição
import sys
sys.path.insert(0, str(SCRIPTS))
from knowledge_gap_detector import KnowledgeGapDetector
from confidence_classifier import ConfidenceClassifier


class LearningPrioritizer:
    """Priorizador de aprendizado baseado em metacognição."""
    
    def __init__(self):
        self.state = self._load_state()
        self.gap_detector = KnowledgeGapDetector()
        self.confidence_classifier = ConfidenceClassifier()
        self._priorities_db = self.state.get("priorities_db", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do learning prioritizer."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "priorities_db": {},
            "last_prioritization": None
        }
    
    def _save_state(self):
        """Salva estado persistente do learning prioritizer."""
        self.state["last_prioritization"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def prioritize_learning(self, gaps: List[Dict], confidence: Dict) -> List[Dict]:
        """Prioriza aprendizado baseado em lacunas e confiança."""
        priorities = []
        
        # Priorizar domínios com baixa confiança
        try:
            low_confidence = self.confidence_classifier.identify_low_confidence_domains()
        except Exception as e:
            print(f"Erro ao identificar baixa confiança: {e}")
            low_confidence = []
        
        for domain_info in low_confidence:
            domain = domain_info["domain"]
            priority_score = 100 - domain_info["score"]  # Inverter score
            
            priorities.append({
                "type": "domain_expansion",
                "target": domain,
                "current_confidence": domain_info["confidence"],
                "priority_score": priority_score,
                "urgency": domain_info["priority"],
                "reason": f"Domínio {domain} tem confiança {domain_info['confidence']}"
            })
        
        # Priorizar lacunas de conhecimento
        try:
            underexplored = self.gap_detector.detect_underexplored_domains()
        except Exception as e:
            print(f"Erro ao detectar domínios pouco explorados: {e}")
            underexplored = []
        
        for domain_info in underexplored:
            domain = domain_info["dominio"]
            if domain_info["status"] == "underexplored":
                priority_score = 80
                
                # Verificar se já está na lista
                if not any(p["target"] == domain for p in priorities):
                    priorities.append({
                        "type": "domain_expansion",
                        "target": domain,
                        "current_confidence": "unknown",
                        "priority_score": priority_score,
                        "urgency": domain_info["priority"],
                        "reason": f"Domínio {domain} é pouco explorado ({domain_info['count']} padrões)"
                    })
        
        # Priorizar termos não explicados
        try:
            unexplained = self.gap_detector.find_unexplained_terms()
        except Exception as e:
            print(f"Erro ao encontrar termos não explicados: {e}")
            unexplained = []
        
        if len(unexplained) > 10:
            priorities.append({
                "type": "term_documentation",
                "target": "technical_terms",
                "current_confidence": "unknown",
                "priority_score": 60,
                "urgency": "medium",
                "reason": f"{len(unexplained)} termos técnicos não explicados"
            })
        
        # Ordenar por prioridade (score decrescente)
        priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Atualizar banco de prioridades
        self._priorities_db["current"] = priorities
        self._save_state()
        
        return priorities
    
    def generate_roadmap(self) -> Dict:
        """Gera roadmap de aprendizado."""
        # Coletar dados de metacognição
        gaps = self.gap_detector.analyze_unanswered_questions()
        underexplored = self.gap_detector.detect_underexplored_domains()
        low_confidence = self.confidence_classifier.identify_low_confidence_domains()
        
        # Priorizar aprendizado
        priorities = self.prioritize_learning(gaps, {})
        
        # Criar roadmap em fases
        roadmap = {
            "fase_1_immediate": [],
            "fase_2_short_term": [],
            "fase_3_medium_term": [],
            "fase_4_long_term": []
        }
        
        for i, priority in enumerate(priorities):
            if i < 2:
                roadmap["fase_1_immediate"].append(priority)
            elif i < 5:
                roadmap["fase_2_short_term"].append(priority)
            elif i < 8:
                roadmap["fase_3_medium_term"].append(priority)
            else:
                roadmap["fase_4_long_term"].append(priority)
        
        # Adicionar metadados
        roadmap["timestamp"] = datetime.now().isoformat()
        roadmap["total_priorities"] = len(priorities)
        roadmap["generated_from"] = {
            "gaps_detected": len(gaps),
            "underexplored_domains": len(underexplored),
            "low_confidence_domains": len(low_confidence)
        }
        
        return roadmap
    
    def suggest_skills(self) -> List[Dict]:
        """Sugere skills a desenvolver."""
        priorities = self.prioritize_learning([], {})
        
        suggestions = []
        
        for priority in priorities[:5]:  # Top 5 prioridades
            target = priority["target"]
            priority_type = priority["type"]
            
            if priority_type == "domain_expansion":
                # Sugerir skills baseadas no domínio
                domain_skills = self._get_domain_skills(target)
                suggestions.extend(domain_skills)
            elif priority_type == "term_documentation":
                suggestions.append({
                    "skill": "technical-documentation",
                    "action": "Documentar termos técnicos não explicados",
                    "priority": priority["urgency"],
                    "estimated_effort": "medium"
                })
        
        return suggestions
    
    def _get_domain_skills(self, domain: str) -> List[Dict]:
        """Obtém skills sugeridas para um domínio."""
        # Mapeamento de domínio para skills
        domain_skills_map = {
            "android": [
                {"skill": "android-deep-dive", "action": "Explorar padrões avançados Android", "priority": "high", "estimated_effort": "high"},
                {"skill": "android-testing", "action": "Melhorar estratégias de teste Android", "priority": "medium", "estimated_effort": "medium"}
            ],
            "ecossistema": [
                {"skill": "ecosystem-architecture", "action": "Estudar arquitetura do ecossistema", "priority": "high", "estimated_effort": "high"},
                {"skill": "ecosystem-optimization", "action": "Otimizar performance do ecossistema", "priority": "medium", "estimated_effort": "medium"}
            ],
            "desenvolvimento": [
                {"skill": "devops-automation", "action": "Expandir automação DevOps", "priority": "high", "estimated_effort": "high"},
                {"skill": "containerization", "action": "Aprofundar em Docker/Kubernetes", "priority": "medium", "estimated_effort": "medium"}
            ],
            "devops": [
                {"skill": "infrastructure-as-code", "action": "Expandir IaC com Terraform", "priority": "high", "estimated_effort": "high"},
                {"skill": "ci-cd-pipelines", "action": "Melhorar pipelines CI/CD", "priority": "medium", "estimated_effort": "medium"}
            ]
        }
        
        return domain_skills_map.get(domain, [
            {
                "skill": f"{domain}-exploration",
                "action": f"Explorar domínio {domain}",
                "priority": "medium",
                "estimated_effort": "medium"
            }
        ])
    
    def integrate_with_agent_10(self) -> Dict:
        """Integra com agente 10-Aprendizado."""
        # Gerar roadmap
        roadmap = self.generate_roadmap()
        
        # Sugerir skills
        skills = self.suggest_skills()
        
        # Preparar integração
        integration = {
            "agent_10_context": {
                "roadmap": roadmap,
                "suggested_skills": skills,
                "learning_priorities": self.prioritize_learning([], {})[:5]
            },
            "integration_status": "ready",
            "message": "Dados de metacognição preparados para agente 10-Aprendizado",
            "timestamp": datetime.now().isoformat()
        }
        
        # Em produção, isso chamaria o agente 10 diretamente
        # Por agora, apenas retorna os dados preparados
        
        return integration
    
    def get_full_report(self) -> Dict:
        """Gera relatório completo de priorização de aprendizado."""
        roadmap = self.generate_roadmap()
        skills = self.suggest_skills()
        integration = self.integrate_with_agent_10()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "roadmap": roadmap,
            "suggested_skills": skills,
            "agent_10_integration": integration,
            "summary": {
                "total_priorities": roadmap["total_priorities"],
                "immediate_actions": len(roadmap["fase_1_immediate"]),
                "suggested_skills_count": len(skills),
                "agent_10_ready": integration["integration_status"] == "ready"
            }
        }
        
        return report


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python learning_prioritizer.py prioritize|generate-roadmap|suggest-skills|integrate-agent10|report")
        sys.exit(1)
    
    command = sys.argv[1]
    prioritizer = LearningPrioritizer()
    
    if command == "prioritize":
        gaps = prioritizer.gap_detector.analyze_unanswered_questions()
        confidence = {}
        priorities = prioritizer.prioritize_learning(gaps, confidence)
        print(json.dumps(priorities, indent=2, ensure_ascii=False))
    
    elif command == "generate-roadmap":
        roadmap = prioritizer.generate_roadmap()
        print(json.dumps(roadmap, indent=2, ensure_ascii=False))
    
    elif command == "suggest-skills":
        skills = prioritizer.suggest_skills()
        print(json.dumps(skills, indent=2, ensure_ascii=False))
    
    elif command == "integrate-agent10":
        integration = prioritizer.integrate_with_agent_10()
        print(json.dumps(integration, indent=2, ensure_ascii=False))
    
    elif command == "report":
        report = prioritizer.get_full_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()