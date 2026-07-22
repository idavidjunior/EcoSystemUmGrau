import re
import json
from datetime import datetime


class GoalAnalyzer:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def analyze(self, raw_goal):
        self.session.log(f"Analyzing goal: {raw_goal[:80]}...")
        goal_lower = raw_goal.lower()

        analysis = {
            "raw": raw_goal,
            "objective": self._extract_objective(raw_goal),
            "domain": self._detect_domain(goal_lower),
            "task_type": self._detect_task_type(goal_lower),
            "technologies": self._detect_technologies(goal_lower),
            "requirements": self._extract_requirements(goal_lower),
            "success_criteria": [],
            "complexity": self._estimate_complexity(goal_lower),
            "estimated_phases": [],
            "dependencies": [],
            "constraints": [],
            "analyzed_at": datetime.now().isoformat(),
        }

        analysis["success_criteria"] = self._generate_success_criteria(analysis)
        analysis["estimated_phases"] = self._generate_phases(analysis)
        analysis["constraints"] = self._detect_constraints(raw_goal, goal_lower)
        analysis["dependencies"] = self._detect_dependencies(analysis)

        self.session.record_decision(
            f"Goal analyzed: {analysis['task_type']} in {analysis['domain']} "
            f"(complexity: {analysis['complexity']}/10)"
        )
        self.session.save_context({**self.session.load_context(), "goal_analysis": analysis})

        return analysis

    def _extract_objective(self, raw):
        cleaned = re.sub(r'(?i)^(create|build|make|develop|criar|construir|fazer|desenvolver)\s+a\s+', '', raw)
        cleaned = re.sub(r'(?i)^(create|build|make|develop|criar|construir|fazer|desenvolver)\s+an?\s+', '', cleaned)
        cleaned = re.sub(r'(?i)^(i want to|preciso de|need|quero|gostaria de|would like to)\s+', '', cleaned)
        return cleaned.strip().capitalize()

    def _detect_domain(self, goal):
        domains = {
            "android": ["android", "apk", "mobile", "app", "aplicativo"],
            "web": ["web", "website", "site", "html", "frontend", "backend", "api", "rest"],
            "python": ["python", "script", "flask", "django", "pytorch", "tensorflow"],
            "database": ["database", "banco", "sql", "mongodb", "postgres", "mysql"],
            "devops": ["deploy", "docker", "kubernetes", "ci/cd", "pipeline"],
            "desktop": ["desktop", "windows", "executavel", "exe"],
            "machine_learning": ["machine learning", "ia", "ai", "neural", "modelo", "treinar"],
            "general": []
        }
        for domain, keywords in domains.items():
            if any(k in goal for k in keywords):
                return domain
        return "general"

    def _detect_task_type(self, goal):
        if any(w in goal for w in ["criar", "create", "build", "make", "develop", "construir", "fazer"]):
            return "creation"
        if any(w in goal for w in ["fix", "corrigir", "repair", "bug", "error", "issue", "problema"]):
            return "fix"
        if any(w in goal for w in ["refactor", "improve", "melhorar", "optimize", "otimizar"]):
            return "improvement"
        if any(w in goal for w in ["test", "testar", "validate", "verify"]):
            return "validation"
        if any(w in goal for w in ["learn", "aprender", "study", "estudar", "understand"]):
            return "learning"
        return "creation"

    def _detect_technologies(self, goal):
        techs = {
            "android": ["android", "apk", "kotlin", "java"],
            "python": ["python", "flask", "django", "pytorch"],
            "javascript": ["javascript", "node", "react", "vue", "angular", "typescript"],
            "flutter": ["flutter", "dart"],
            "docker": ["docker", "container"],
            "git": ["git", "github"],
            "database": ["sql", "mysql", "postgres", "mongodb", "sqlite"],
            "html": ["html", "css", "web"],
        }
        detected = []
        for tech, keywords in techs.items():
            if any(k in goal for k in keywords):
                detected.append(tech)
        return detected if detected else ["unknown"]

    def _extract_requirements(self, goal):
        requirements = []

        bullet_pattern = re.findall(r'(?:^|\n)\s*[-*]\s*(.+?)(?:\n|$)', goal)
        if bullet_pattern:
            requirements.extend(bullet_pattern)

        numbered = re.findall(r'(?:^|\n)\s*\d+[.)]\s*(.+?)(?:\n|$)', goal)
        if numbered:
            requirements.extend(numbered)

        with_keywords = re.findall(r'(?i)(?:preciso|need|requer|requires|deve ter|must have|tem que ter)[:\s]+(.+?)(?:\.|,|\n|$)', goal)
        if with_keywords:
            requirements.extend(with_keywords)

        return requirements if requirements else ["Understand and implement the requested functionality"]

    def _estimate_complexity(self, goal):
        score = 3
        complex_words = ["android", "app", "application", "database", "api", "full", "complete",
                        "aplicativo", "banco", "sistema", "integrated", "multi", "distributed"]
        score += sum(2 for w in complex_words if w in goal)

        tech_count = len(self._detect_technologies(goal))
        score += tech_count * 2

        req_count = len(self._extract_requirements(goal))
        if req_count > 5:
            score += 3
        elif req_count > 2:
            score += 1

        return min(score, 10)

    def _generate_success_criteria(self, analysis):
        criteria = []
        if analysis["domain"] == "android":
            criteria.append("APK compilado sem erros")
            criteria.append("Aplicativo abre no dispositivo")
            criteria.append("Funcoes principais funcionando")
        elif analysis["domain"] == "web":
            criteria.append("Servidor inicia sem erros")
            criteria.append("Pagina carrega no navegador")
            criteria.append("API responde corretamente")
        elif analysis["domain"] == "python":
            criteria.append("Script executa sem erros")
            criteria.append("Saida esperada gerada")
        else:
            criteria.append("Codigo compila/executa sem erros")
            criteria.append("Funcionalidade implementada conforme requisitos")
            criteria.append("Testes basicos aprovados")

        criteria.append("Codigo versionado no Git")
        criteria.append("Documentacao minima gerada")
        return criteria

    def _generate_phases(self, analysis):
        phases = [
            {"phase": 1, "name": "Analise", "description": "Analisar requisitos e ambiente"},
            {"phase": 2, "name": "Planejamento", "description": "Criar estrategia e plano de execucao"},
            {"phase": 3, "name": "Implementacao", "description": "Desenvolver a solucao"},
            {"phase": 4, "name": "Testes", "description": "Validar funcionamento"},
            {"phase": 5, "name": "Entrega", "description": "Finalizar e apresentar resultado"},
        ]
        if analysis["complexity"] >= 7:
            phases.insert(3, {"phase": 6, "name": "Revisao", "description": "Revisar e refinar implementacao"})
        return phases

    def _detect_constraints(self, raw, goal):
        constraints = []
        if any(w in goal for w in ["windows", "powershell"]):
            constraints.append("Windows environment")
        if not any(w in raw for w in ["--no-git", "no git"]):
            constraints.append("Must use Git versioning")
        if any(w in goal for w in ["sdk puro", "pure sdk", "no androidx", "no gradle"]):
            constraints.append("Pure Android SDK (no AndroidX/Gradle)")
        return constraints

    def _detect_dependencies(self, analysis):
        deps = []
        if "android" in analysis["technologies"]:
            deps.extend(["Android SDK", "Java/JDK", "Build tools"])
        if "python" in analysis["technologies"]:
            deps.append("Python 3.x")
        if "docker" in analysis["technologies"]:
            deps.extend(["Docker", "Docker Compose"])
        if "node" in analysis["technologies"] or "javascript" in analysis["technologies"]:
            deps.extend(["Node.js", "npm"])
        return deps
