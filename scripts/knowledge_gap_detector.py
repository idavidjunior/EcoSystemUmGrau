#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""knowledge_gap_detector.py — Identificação de Lacunas de Conhecimento.

Análise de perguntas sem resposta satisfatória, detecção de domínios pouco
explorados, identificação de termos técnicos não explicados e mapeamento de
fronteiras de competência.

Uso:
  python scripts/knowledge_gap_detector.py analyze-questions  # Analisa perguntas
  python scripts/knowledge_gap_detector.py detect-domains     # Detecta domínios pouco explorados
  python scripts/knowledge_gap_detector.py find-terms         # Encontra termos não explicados
  python scripts/knowledge_gap_detector.py map-boundaries      # Mapeia fronteiras de competência

Saída JSON: {lacunas, dominios, termos, fronteiras, timestamp}
"""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
CONHECIMENTO = ROOT / "conhecimento"
LER_RUNTIME = ROOT / "ler-runtime"

# Estado persistente do knowledge gap detector
STATE_FILE = RUNTIME / "knowledge_gap_detector_state.json"

# Domínios de conhecimento do ecossistema
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


class KnowledgeGapDetector:
    """Detector de lacunas de conhecimento."""
    
    def __init__(self):
        self.state = self._load_state()
        self._gaps_db = self.state.get("gaps_db", {})
        self._term_analysis = self.state.get("term_analysis", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do knowledge gap detector."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "gaps_db": {},
            "term_analysis": {},
            "last_analysis": None,
            "total_gaps_detected": 0
        }
    
    def _save_state(self):
        """Salva estado persistente do knowledge gap detector."""
        self.state["last_analysis"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def analyze_unanswered_questions(self) -> List[Dict]:
        """Analisa perguntas sem resposta satisfatória."""
        # Carregar conversa única
        conversa_file = ROOT / "conversa_unica.json"
        
        if not conversa_file.exists():
            return []
        
        try:
            with open(conversa_file, "r", encoding="utf-8") as f:
                conversa = json.load(f)
        except Exception:
            return []
        
        gaps = []
        
        # Verificar se conversa é lista ou dict
        if isinstance(conversa, list):
            # Formato de lista (turnos diretos)
            for turno in conversa:
                if not isinstance(turno, dict):
                    continue
                usuario = turno.get("usuario", "")
                jarvis = turno.get("jarvis", "")
                
                # Indicadores de resposta insatisfatória
                if not jarvis or len(jarvis) < 50:
                    gaps.append({
                        "tipo": "resposta_curta",
                        "pergunta": usuario,
                        "resposta": jarvis,
                        "timestamp": turno.get("timestamp", "")
                    })
                elif any(indicador in jarvis.lower() for indicador in ["não sei", "não tenho", "incerto", "não consigo"]):
                    gaps.append({
                        "tipo": "incerteza",
                        "pergunta": usuario,
                        "resposta": jarvis,
                        "timestamp": turno.get("timestamp", "")
                    })
        elif isinstance(conversa, dict):
            # Formato de dict com campo turnos
            for turno in conversa.get("turnos", []):
                if not isinstance(turno, dict):
                    continue
                usuario = turno.get("usuario", "")
                jarvis = turno.get("jarvis", "")
                
                # Indicadores de resposta insatisfatória
                if not jarvis or len(jarvis) < 50:
                    gaps.append({
                        "tipo": "resposta_curta",
                        "pergunta": usuario,
                        "resposta": jarvis,
                        "timestamp": turno.get("timestamp", "")
                    })
                elif any(indicador in jarvis.lower() for indicador in ["não sei", "não tenho", "incerto", "não consigo"]):
                    gaps.append({
                        "tipo": "incerteza",
                        "pergunta": usuario,
                        "resposta": jarvis,
                        "timestamp": turno.get("timestamp", "")
                    })
        
        # Atualizar banco de lacunas
        self._gaps_db["unanswered_questions"] = gaps
        self.state["total_gaps_detected"] = len(gaps)
        self._save_state()
        
        return gaps
    
    def detect_underexplored_domains(self) -> List[Dict]:
        """Detecta domínios pouco explorados."""
        # Carregar knowledge graph do LER
        knowledge_file = LER_RUNTIME / "knowledge" / "knowledge_graph.json"
        
        if not knowledge_file.exists():
            return []
        
        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                knowledge_graph = json.load(f)
        except Exception:
            return []
        
        # Contar padrões por domínio
        domain_counts = Counter()
        
        for pattern in knowledge_graph.get("patterns", []):
            source = pattern.get("source", "")
            
            # Mapear source para domínio
            if "android" in source.lower():
                domain_counts["android"] += 1
            elif "ler" in source.lower():
                domain_counts["ler"] += 1
            elif "mp3player" in source.lower():
                domain_counts["multimidia"] += 1
            elif "opencode" in source.lower():
                domain_counts["ecossistema"] += 1
            elif "devops" in source.lower():
                domain_counts["devops"] += 1
            elif "node" in source.lower():
                domain_counts["desenvolvimento"] += 1
            else:
                domain_counts["geral"] += 1
        
        # Identificar domínios pouco explorados
        underexplored = []
        
        for domain in DOMAINS:
            count = domain_counts.get(domain, 0)
            
            # Domínio é pouco explorado se tem < 10 padrões
            if count < 10:
                underexplored.append({
                    "dominio": domain,
                    "count": count,
                    "status": "underexplored",
                    "priority": "high" if count < 5 else "medium"
                })
            elif count < 20:
                underexplored.append({
                    "dominio": domain,
                    "count": count,
                    "status": "moderate",
                    "priority": "low"
                })
        
        # Atualizar banco de lacunas
        self._gaps_db["underexplored_domains"] = underexplored
        self._save_state()
        
        return underexplored
    
    def find_unexplained_terms(self) -> List[Dict]:
        """Encontra termos técnicos não explicados."""
        # Carregar conhecimento/aprendizados
        aprendizados_dir = CONHECIMENTO / "aprendizados"
        
        if not aprendizados_dir.exists():
            return []
        
        # Coletar todos os arquivos de aprendizado
        aprendizados_files = list(aprendizados_dir.glob("*.md"))
        
        # Lista de termos técnicos comuns que deveriam ser explicados
        technical_terms = [
            "API", "endpoint", "deployment", "container", "Docker", "pipeline",
            "CI/CD", "git", "commit", "branch", "merge", "pull request",
            "MCP", "LLM", "TTS", "STT", "WebSocket", "JSON", "REST",
            "SDK", "framework", "biblioteca", "dependência", "package",
            "script", "shell", "PowerShell", "Python", "TypeScript",
            "react", "vue", "flutter", "android", "ios", "web",
            "docker", "kubernetes", "terraform", "infraestrutura",
            "cloud", "server", "client", "backend", "frontend",
        ]
        
        unexplained = []
        
        for aprendizado_file in aprendizados_files:
            try:
                with open(aprendizado_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            # Buscar termos técnicos no conteúdo
            for term in technical_terms:
                if term.lower() in content.lower():
                    # Verificar se o termo é explicado
                    explanation_pattern = rf"{term}.*?:|{term}.*é|{term}.*significa"
                    if not re.search(explanation_pattern, content, re.IGNORECASE):
                        unexplained.append({
                            "termo": term,
                            "arquivo": aprendizado_file.name,
                            "contexto": "Termo mencionado sem explicação",
                            "timestamp": datetime.now().isoformat()
                        })
        
        # Deduplicar termos
        unique_terms = {}
        for item in unexplained:
            key = f"{item['termo']}_{item['arquivo']}"
            if key not in unique_terms:
                unique_terms[key] = item
        
        unexplained = list(unique_terms.values())
        
        # Atualizar análise de termos
        self._term_analysis["unexplained_terms"] = unexplained
        self._save_state()
        
        return unexplained
    
    def map_competence_boundaries(self) -> Dict:
        """Mapeia fronteiras de competência."""
        # Carregar knowledge graph
        knowledge_file = LER_RUNTIME / "knowledge" / "knowledge_graph.json"
        
        if not knowledge_file.exists():
            return {"error": "Knowledge graph não encontrado"}
        
        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                knowledge_graph = json.load(f)
        except Exception:
            return {"error": "Erro ao carregar knowledge graph"}
        
        # Analisar padrões para identificar fronteiras
        patterns = knowledge_graph.get("patterns", [])
        
        # Contar ações por tipo
        action_counts = Counter()
        for pattern in patterns:
            action = pattern.get("action", "unknown")
            action_counts[action] += 1
        
        # Identificar competências e lacunas
        competencies = {
            "strong": [],
            "moderate": [],
            "weak": [],
            "unknown": []
        }
        
        for action, count in action_counts.items():
            if count >= 10:
                competencies["strong"].append({"action": action, "count": count})
            elif count >= 5:
                competencies["moderate"].append({"action": action, "count": count})
            elif count >= 1:
                competencies["weak"].append({"action": action, "count": count})
            else:
                competencies["unknown"].append({"action": action, "count": count})
        
        # Calcular score de competência geral
        total_patterns = len(patterns)
        strong_count = len(competencies["strong"])
        weak_count = len(competencies["weak"])
        
        if total_patterns > 0:
            competence_score = (strong_count / total_patterns) * 100
        else:
            competence_score = 0
        
        boundaries = {
            "total_patterns": total_patterns,
            "competence_score": competence_score,
            "competencies": competencies,
            "frontier_summary": {
                "strong_competencies": len(competencies["strong"]),
                "moderate_competencies": len(competencies["moderate"]),
                "weak_competencies": len(competencies["weak"]),
                "overall_status": "high" if competence_score >= 50 else "medium" if competence_score >= 30 else "low"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Atualizar banco de lacunas
        self._gaps_db["competence_boundaries"] = boundaries
        self._save_state()
        
        return boundaries
    
    def generate_gap_report(self) -> Dict:
        """Gera relatório completo de lacunas de conhecimento."""
        unanswered = self.analyze_unanswered_questions()
        underexplored = self.detect_underexplored_domains()
        unexplained = self.find_unexplained_terms()
        boundaries = self.map_competence_boundaries()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "unanswered_questions": {
                "count": len(unanswered),
                "items": unanswered[:10]  # Primeiros 10
            },
            "underexplored_domains": {
                "count": len(underexplored),
                "items": underexplored
            },
            "unexplained_terms": {
                "count": len(unexplained),
                "items": unexplained[:10]  # Primeiros 10
            },
            "competence_boundaries": boundaries,
            "overall_assessment": self._calculate_overall_assessment(unanswered, underexplored, unexplained, boundaries),
            "recommendations": self._generate_gap_recommendations(unanswered, underexplored, unexplained)
        }
        
        return report
    
    def _calculate_overall_assessment(self, unanswered: List, underexplored: List, unexplained: List, boundaries: Dict) -> str:
        """Calcula avaliação geral de lacunas."""
        score = 100
        
        # Penalidade por perguntas não respondidas
        score -= len(unanswered) * 2
        
        # Penalidade por domínios pouco explorados
        score -= len(underexplored) * 5
        
        # Penalidade por termos não explicados
        score -= len(unexplained)
        
        # Penalidade por competência fraca
        if boundaries.get("competence_score", 0) < 30:
            score -= 20
        elif boundaries.get("competence_score", 0) < 50:
            score -= 10
        
        if score >= 80:
            return "good"
        elif score >= 60:
            return "moderate"
        elif score >= 40:
            return "needs_improvement"
        else:
            return "critical"
    
    def _generate_gap_recommendations(self, unanswered: List, underexplored: List, unexplained: List) -> List[str]:
        """Gera recomendações baseadas em lacunas."""
        recommendations = []
        
        if len(unanswered) > 10:
            recommendations.append(f"Investigar {len(unanswered)} perguntas sem resposta satisfatória")
        
        if len(underexplored) > 3:
            recommendations.append(f"Expandir conhecimento em {len(underexplored)} domínios pouco explorados")
        
        if len(unexplained) > 20:
            recommendations.append(f"Documentar {len(unexplained)} termos técnicos não explicados")
        
        high_priority_domains = [d for d in underexplored if d.get("priority") == "high"]
        if high_priority_domains:
            domain_names = [d["dominio"] for d in high_priority_domains]
            recommendations.append(f"Priorizar aprendizado em: {', '.join(domain_names)}")
        
        if not recommendations:
            recommendations.append("Nenhuma lacuna crítica identificada - sistema estável")
        
        return recommendations


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python knowledge_gap_detector.py analyze-questions|detect-domains|find-terms|map-boundaries|report")
        sys.exit(1)
    
    command = sys.argv[1]
    detector = KnowledgeGapDetector()
    
    if command == "analyze-questions":
        gaps = detector.analyze_unanswered_questions()
        print(json.dumps(gaps, indent=2, ensure_ascii=False))
    
    elif command == "detect-domains":
        domains = detector.detect_underexplored_domains()
        print(json.dumps(domains, indent=2, ensure_ascii=False))
    
    elif command == "find-terms":
        terms = detector.find_unexplained_terms()
        print(json.dumps(terms, indent=2, ensure_ascii=False))
    
    elif command == "map-boundaries":
        boundaries = detector.map_competence_boundaries()
        print(json.dumps(boundaries, indent=2, ensure_ascii=False))
    
    elif command == "report":
        report = detector.generate_gap_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()