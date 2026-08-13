import re
import json
from datetime import datetime


class GoalSpecification:
    def __init__(self, objective, requirements, constraints, dependencies,
                 assumptions, acceptance_criteria, definition_of_done, risks):
        self.objective = objective
        self.requirements = requirements
        self.constraints = constraints
        self.dependencies = dependencies
        self.assumptions = assumptions
        self.acceptance_criteria = acceptance_criteria
        self.definition_of_done = definition_of_done
        self.risks = risks

    def to_dict(self):
        return {
            "objective": self.objective,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "assumptions": self.assumptions,
            "acceptance_criteria": self.acceptance_criteria,
            "definition_of_done": self.definition_of_done,
            "risks": self.risks,
        }

    def to_spec_markdown(self, componente=".", tags=None,
                         entradas_saidas=None, casos_borda=None,
                         testes_relacionados=None):
        """Gera a spec markdown do ecossistema no formato specs/template.md.

        Cada seção espelha um campo desta GoalSpecification (objective,
        requirements, constraints, dependencies, assumptions,
        acceptance_criteria, definition_of_done, risks). Não grava arquivo:
        o chamador decide onde persistir — fail-soft, 100% stdlib.
        """

        def _slug(texto):
            t = re.sub(r'[^a-z0-9]+', '-', texto.strip().lower()).strip('-')
            return t[:60] or 'componente'

        def _items(itens, bullet='-'):
            if not itens:
                return f'{bullet} _nenhum declarado_'
            return '\n'.join(f'{bullet} {i}' for i in itens)

        hoje = datetime.now().strftime('%Y-%m-%d')
        id_spec = 'spec-' + _slug(componente if componente and componente != '.' else self.objective)
        nome = componente if componente and componente != '.' else _slug(self.objective)
        tags_txt = '[' + ', '.join(tags or []) + ']'

        riscos = []
        for r in (self.risks or []):
            if isinstance(r, dict):
                riscos.append(f"- {r.get('risk', r)} — severidade {r.get('severity', 'baixa')}")
            else:
                riscos.append(f'- {r}')
        if not riscos:
            riscos = ['- _nenhum declarado_']

        dod = '\n'.join(f'- [ ] {i}' for i in (self.definition_of_done or []))
        if not dod:
            dod = '- [ ] _nenhum declarado_'

        return (
            '---\n'
            f'id: {id_spec}\n'
            'versao: 0.1.0\n'
            'status: proposta\n'
            f'componente: {componente if componente else "."}\n'
            f'tags: {tags_txt}\n'
            f'data: {hoje}\n'
            '---\n'
            f'\n# Spec — {nome}\n'
            f'\n## Objetivo\n\n{self.objective or "_nenhum declarado_"}\n'
            f'\n## Requisitos\n\n{_items(self.requirements, "1.")}\n'
            f'\n## Restrições\n\n{_items(self.constraints)}\n'
            f'\n## Dependências\n\n{_items(self.dependencies)}\n'
            f'\n## Premissas\n\n{_items(self.assumptions)}\n'
            '\n## Entradas e Saídas\n'
            f'\n{_items(entradas_saidas or ["Entrada: _definir_ (derivado da análise de requisitos).", "Saída: _definir_ (derivado da análise de requisitos).", "Efeito colateral: _definir_."])}'
            '\n\n## Casos de Borda\n'
            f'\n{_items(casos_borda or ["_definir_ (condições-limite da análise, ver princípio do teste adversarial)."])}'
            f'\n\n## Critérios de Aceitação\n\n{_items(self.acceptance_criteria)}'
            f'\n\n## Definition of Done\n\n{dod}'
            f'\n\n## Riscos\n\n' + '\n'.join(riscos) +
            '\n\n## Testes Relacionados\n'
            f'\n{_items(testes_relacionados or ["_definir_ (caminho do teste que cobre esta spec)"])}'
            '\n'
        )


class GoalAnalyzer:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def analyze(self, raw_goal):
        self.session.log(f"Analyzing goal: {raw_goal[:80]}...")
        goal_lower = raw_goal.lower()

        requirements = self._extract_requirements(goal_lower)
        constraints = self._detect_constraints(raw_goal, goal_lower)
        dependencies = self._detect_dependencies(goal_lower)
        assumptions = self._extract_assumptions(goal_lower)
        risks = self._identify_risks(goal_lower)
        acceptance_criteria = self._generate_acceptance_criteria(requirements)
        definition_of_done = self._generate_definition_of_done(requirements, constraints)

        spec = GoalSpecification(
            objective=self._extract_objective(raw_goal),
            requirements=requirements,
            constraints=constraints,
            dependencies=dependencies,
            assumptions=assumptions,
            acceptance_criteria=acceptance_criteria,
            definition_of_done=definition_of_done,
            risks=risks,
        )

        domain = self._detect_domain(goal_lower)

        analysis = {
            "raw": raw_goal,
            "objective": spec.objective,
            "domain": domain,
            "task_type": self._detect_task_type(goal_lower),
            "technologies": self._detect_technologies(goal_lower),
            "requirements": requirements,
            "constraints": constraints,
            "dependencies": dependencies,
            "assumptions": assumptions,
            "success_criteria": self._generate_success_criteria(domain=domain),
            "complexity": self._estimate_complexity(goal_lower),
            "estimated_phases": [],
            "risks": risks,
            "acceptance_criteria": acceptance_criteria,
            "definition_of_done": definition_of_done,
            "goal_spec": spec.to_dict(),
            "spec_markdown": spec.to_spec_markdown(
                tags=["ler", "goal-analysis"],
                entradas_saidas=self._generate_entradas_saidas(domain, constraints),
                casos_borda=self._generate_casos_borda(domain, constraints, risks),
                testes_relacionados=self._generate_testes_relacionados(domain),
            ),
            "analyzed_at": datetime.now().isoformat(),
        }

        analysis["estimated_phases"] = self._generate_phases(analysis)

        self.session.record_decision(
            f"Goal analyzed: {analysis['task_type']} in {analysis['domain']} "
            f"(complexity: {analysis['complexity']}/10, "
            f"{len(acceptance_criteria)} criteria, "
            f"{len(definition_of_done)} DoD items)"
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

    def _generate_success_criteria(self, domain="general"):
        criteria = []
        if domain == "android":
            criteria.append("APK compilado sem erros")
            criteria.append("Aplicativo abre no dispositivo")
            criteria.append("Funcoes principais funcionando")
        elif domain == "web":
            criteria.append("Servidor inicia sem erros")
            criteria.append("Pagina carrega no navegador")
            criteria.append("API responde corretamente")
        elif domain == "python":
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
        if any(w in goal for w in ["sem ui", "no ui", "headless", "cli only"]):
            constraints.append("Command-line interface only")
        if any(w in goal for w in ["offline", "sem internet", "no network"]):
            constraints.append("Must work offline")
        return constraints

    def _detect_dependencies(self, goal):
        deps = []
        if "android" in goal:
            deps.extend(["Android SDK", "Java/JDK", "Build tools"])
        if "python" in goal:
            deps.append("Python 3.x")
        if "docker" in goal:
            deps.extend(["Docker", "Docker Compose"])
        if "node" in goal or "javascript" in goal:
            deps.extend(["Node.js", "npm"])
        if "git" in goal:
            deps.append("Git")
        return deps

    def _extract_assumptions(self, goal):
        assumptions = []
        goal_lower = goal.lower()
        if "android" in goal_lower:
            assumptions.append("Android SDK is installed and configured")
        if "python" in goal_lower:
            assumptions.append("Python 3.x is available on PATH")
        if "docker" in goal_lower:
            assumptions.append("Docker daemon is running")
        assumptions.append("All dependencies can be installed via standard package managers")
        return assumptions

    def _identify_risks(self, goal):
        risks = []
        goal_lower = goal.lower()
        if "android" in goal_lower:
            risks.append({"risk": "Android SDK version mismatch", "severity": "high"})
        if "api" in goal_lower:
            risks.append({"risk": "External API may be unavailable or rate-limited", "severity": "medium"})
        if "database" in goal_lower:
            risks.append({"risk": "Database schema changes may affect existing data", "severity": "high"})
        risks.append({"risk": "Requirements may be incomplete or ambiguous", "severity": "low"})
        return risks

    def _generate_acceptance_criteria(self, requirements):
        criteria = []
        for req in requirements:
            criteria.append(f"{req} implementado e funcional")
        if not criteria:
            criteria.append("Objetivo geral atingido conforme especificado")
        criteria.append("Nenhum erro critico no funcionamento basico")
        criteria.append("Codigo compila/executa sem erros")
        return criteria

    def _generate_definition_of_done(self, requirements, constraints):
        dod = [
            "Todos os requisitos implementados",
            "Codigo compila e executa sem erros",
            "Testes basicos aprovados",
            "Evidencias de funcionamento coletadas",
            "Auditoria final aprovada",
            "Relatorio final gerado",
        ]
        if any("Git" in c for c in constraints):
            dod.append("Codigo versionado no Git")
        return dod

    def _generate_entradas_saidas(self, domain, constraints):
        base = {
            "android": [
                "Entrada: interface do aplicativo Android (toques, formularios, eventos de sistema).",
                "Saída: comportamento do app atualizado na tela e no dispositivo.",
                "Efeito colateral: dados persistidos localmente no aparelho.",
            ],
            "web": [
                "Entrada: requisições HTTP do navegador (parametros, corpo, cabecalhos).",
                "Saída: resposta HTTP com status, corpo e cabecalhos apropriados.",
                "Efeito colateral: estado atualizado no servidor e no cliente.",
            ],
            "python": [
                "Entrada: argumentos de linha de comando, arquivos e dados do usuario.",
                "Saída: saída processada em stdout, arquivos ou serviços.",
                "Efeito colateral: arquivos alterados ou criados no sistema.",
            ],
            "database": [
                "Entrada: dados a persistir e consultas de leitura/escrita.",
                "Saída: resultados de consulta e confirmacoes de escrita.",
                "Efeito colateral: registros alterados no banco de dados.",
            ],
            "devops": [
                "Entrada: pipeline, infraestrutura e artefatos de build.",
                "Saída: ambiente provisionado e artefatos publicados.",
                "Efeito colateral: recursos de infraestrutura criados ou alterados.",
            ],
            "desktop": [
                "Entrada: interacoes de interface de usuario e eventos do sistema.",
                "Saída: janelas, dialogos e estado visual atualizados.",
                "Efeito colateral: configuracoes e dados persistidos localmente.",
            ],
            "machine_learning": [
                "Entrada: conjunto de dados de treinamento e avaliacao.",
                "Saída: modelo treinado e metricas de desempenho.",
                "Efeito colateral: artefatos de modelo e metricas persistidos.",
            ],
        }
        items = base.get(domain, [
            "Entrada: entrada fornecida pelo usuario ou pelo sistema.",
            "Saída: resultado processado conforme o objetivo.",
            "Efeito colateral: estado do sistema alterado.",
        ])
        if any("Git" in c for c in constraints):
            items[-1] = items[-1] + " E versionado no Git."
        return items

    def _generate_casos_borda(self, domain, constraints, risks):
        cases = []
        for c in constraints:
            cl = c.lower()
            if "offline" in cl:
                cases.append("Operação sem conectividade de rede")
            elif "command" in cl and "line" in cl:
                cases.append("Uso sem interface gráfica")
        for r in risks:
            rl = r.get("risk", "").lower()
            if "api" in rl and ("unavailable" in rl or "rate" in rl):
                cases.append("Serviço externo indisponível ou com rate limit (timeout/retry/fallback)")
            elif "schema" in rl:
                cases.append("Migração de schema com dados existentes (backup/rollback)")
            elif "sdk" in rl:
                cases.append("SDK/ferramentas de build ausentes ou com versão incompatível")
            elif "ambiguous" in rl or "incomplete" in rl:
                cases.append("Requisitos ambíguos ou incompletos")
        cases.append("Entradas vazias ou inválidas")
        cases.append("Execução repetida (idempotência e estado parcial)")
        return cases

    def _generate_testes_relacionados(self, domain):
        base = {
            "android": [
                "Testes unitários/instrumentados do módulo do app (diretório de testes do aplicativo).",
            ],
            "web": [
                "Testes de API e de contrato das rotas HTTP (suíte de testes do backend).",
            ],
            "python": [
                "Testes unitários em um diretório de testes (unittest/pytest).",
            ],
            "database": [
                "Testes de migração e de consultas contra o schema versionado.",
            ],
            "devops": [
                "Validação de pipeline em ambiente de staging (CI).",
            ],
            "desktop": [
                "Testes manuais automatizados dos fluxos de interface (smoke).",
            ],
            "machine_learning": [
                "Validação de avaliação do modelo (holdout, métricas).",
            ],
        }
        items = base.get(domain, [
            "Teste funcional do fluxo principal correspondente a esta spec.",
        ])
        items.append("Teste de regressão: repetir o fluxo principal após alterações")
        return items
