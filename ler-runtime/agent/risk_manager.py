import json
from datetime import datetime


class RiskManager:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def assess(self, goal_analysis, strategy=None):
        self.session.log("Assessing risks...")
        risks = []

        risks.extend(self._assess_environment_risks())
        risks.extend(self._assess_goal_risks(goal_analysis))
        risks.extend(self._assess_technical_risks(goal_analysis))
        risks.extend(self._assess_external_risks(goal_analysis))
        risks.extend(self._assess_dependency_risks(goal_analysis))
        risks.extend(self._assess_api_risks(goal_analysis))
        risks.extend(self._assess_permission_risks())
        risks.extend(self._assess_strategy_risks(strategy) if strategy else [])

        for risk in risks:
            risk["mitigation_plan"] = self._generate_mitigation(risk)
            risk["contingency"] = self._generate_contingency(risk)

        critical = [r for r in risks if r.get("severity") == "critical"]
        high = [r for r in risks if r.get("severity") == "high"]

        assessment = {
            "risks": risks,
            "critical_count": len(critical),
            "high_count": len(high),
            "total_risks": len(risks),
            "can_proceed": len(critical) == 0,
            "mitigation_plan_count": len(risks),
            "assessed_at": datetime.now().isoformat(),
        }

        self.session.record_decision(
            f"Risk assessment: {len(critical)} critical, {len(high)} high, "
            f"{len(risks)} total, {len(risks)} mitigation plans. "
            f"Can proceed: {assessment['can_proceed']}"
        )
        self.session.save_context({**self.session.load_context(), "risk_assessment": assessment})
        return assessment

    def _assess_environment_risks(self):
        return [
            {
                "id": "env_001", "category": "environment",
                "description": "Ferramentas necessarias podem nao estar instaladas",
                "severity": "high", "likelihood": "medium",
                "impact": "Bloqueia execucao", "affected_area": "setup"
            },
            {
                "id": "env_002", "category": "environment",
                "description": "Permissoes de arquivo insuficientes",
                "severity": "medium", "likelihood": "low",
                "impact": "Falha ao criar/modificar arquivos", "affected_area": "execution"
            },
            {
                "id": "env_003", "category": "environment",
                "description": "Sistema operacional incompativel com ferramentas requeridas",
                "severity": "medium", "likelihood": "low",
                "impact": "Comandos especificos de SO falham", "affected_area": "execution"
            },
        ]

    def _assess_goal_risks(self, analysis):
        risks = []
        complexity = analysis.get("complexity", 5)
        if complexity >= 8:
            risks.append({
                "id": "goal_001", "category": "complexity",
                "description": "Objetivo de alta complexidade requer multiplas iteracoes",
                "severity": "high", "likelihood": "high",
                "impact": "Tempo de execucao prolongado", "affected_area": "planning"
            })
        if not analysis.get("requirements"):
            risks.append({
                "id": "goal_002", "category": "ambiguity",
                "description": "Objetivo sem requisitos explicitos pode levar a resultado insatisfatorio",
                "severity": "medium", "likelihood": "high",
                "impact": "Escopo mal definido", "affected_area": "analysis"
            })
        if analysis.get("domain") == "android":
            risks.append({
                "id": "goal_003", "category": "technical",
                "description": "Ambiente Android requer SDK e build tools instalados",
                "severity": "high", "likelihood": "medium",
                "impact": "Falha na compilacao do APK", "affected_area": "execution"
            })
        return risks

    def _assess_technical_risks(self, analysis):
        risks = []
        techs = analysis.get("technologies", ["unknown"])
        if "unknown" in techs:
            risks.append({
                "id": "tech_001", "category": "technical",
                "description": "Tecnologias nao identificadas - risco de ferramenta ausente",
                "severity": "medium", "likelihood": "medium",
                "impact": "Necessidade de instalar dependencias nao previstas",
                "affected_area": "setup"
            })
        if len(techs) > 2:
            risks.append({
                "id": "tech_002", "category": "technical",
                "description": f"Multiplas tecnologias ({', '.join(techs)}) aumentam complexidade de integracao",
                "severity": "medium", "likelihood": "high",
                "impact": "Problemas de compatibilidade entre tecnologias",
                "affected_area": "integration"
            })
        return risks

    def _assess_external_risks(self, analysis):
        risks = []
        domain = analysis.get("domain", "general")
        if domain == "web":
            risks.append({
                "id": "ext_001", "category": "external",
                "description": "Servicos web podem estar indisponiveis durante execucao",
                "severity": "medium", "likelihood": "low",
                "impact": "Falha ao baixar dependencias ou acessar APIs",
                "affected_area": "execution"
            })
        if analysis.get("task_type") == "fix":
            risks.append({
                "id": "ext_002", "category": "external",
                "description": "Causa raiz pode estar em dependencia externa fora do controle",
                "severity": "high", "likelihood": "medium",
                "impact": "Impossibilidade de corrigir sem atualizacao de terceiros",
                "affected_area": "fix"
            })
        return risks

    def _assess_dependency_risks(self, analysis):
        risks = []
        deps = analysis.get("dependencies", [])
        for dep in deps:
            risks.append({
                "id": f"dep_{deps.index(dep)}",
                "category": "dependency",
                "description": f"Dependencia '{dep}' pode nao estar disponivel ou ter versao incompativel",
                "severity": "high", "likelihood": "medium",
                "impact": f"Bloqueio se {dep} nao estiver instalado",
                "affected_area": "setup"
            })
        return risks

    def _assess_api_risks(self, analysis):
        risks = []
        goal = str(analysis.get("raw", "")).lower()
        if any(w in goal for w in ["api", "rest", "http", "endpoint", "service"]):
            risks.append({
                "id": "api_001", "category": "api",
                "description": "API externa pode ter rate limiting, autenticacao ou mudancas de contrato",
                "severity": "high", "likelihood": "medium",
                "impact": "Falha na comunicacao com API externa",
                "affected_area": "integration"
            })
            risks.append({
                "id": "api_002", "category": "api",
                "description": "Formato de resposta da API pode ser diferente do esperado",
                "severity": "medium", "likelihood": "medium",
                "impact": "Parsing incorreto dos dados recebidos",
                "affected_area": "implementation"
            })
        return risks

    def _assess_permission_risks(self):
        return [
            {
                "id": "perm_001", "category": "permission",
                "description": "Script pode exigir permissoes administrativas",
                "severity": "medium", "likelihood": "low",
                "impact": "Falha ao executar comandos que requerem elevacao",
                "affected_area": "execution"
            },
            {
                "id": "perm_002", "category": "permission",
                "description": "Diretorio de saida pode ter restricoes de escrita",
                "severity": "low", "likelihood": "low",
                "impact": "Falha ao salvar artefatos gerados",
                "affected_area": "output"
            },
        ]

    def _assess_strategy_risks(self, strategy):
        risks = []
        if strategy:
            risk_level = strategy.get("risk", "medium")
            if risk_level in ("high", "very high"):
                risks.append({
                    "id": "strat_001", "category": "strategy",
                    "description": f"Estrategia '{strategy['name']}' possui risco {risk_level}",
                    "severity": "high" if risk_level == "very high" else "medium",
                    "likelihood": "medium",
                    "impact": "Falha na execucao da estrategia",
                    "affected_area": "strategy"
                })
            if strategy.get("parallel_execution", False):
                risks.append({
                    "id": "strat_002", "category": "strategy",
                    "description": "Execucao paralela aumenta complexidade de coordenacao",
                    "severity": "medium", "likelihood": "high",
                    "impact": "Conflitos entre execucoes paralelas",
                    "affected_area": "coordination"
                })
        return risks

    def _generate_mitigation(self, risk):
        category = risk.get("category", "")
        severity = risk.get("severity", "medium")

        mitigations = {
            "environment": "Verificar instalacao das ferramentas antes de executar. Usar fallback nativo do SO.",
            "complexity": "Dividir em etapas menores. Validar cada etapa antes de prosseguir. Usar checkpoint frequente.",
            "ambiguity": "Esclarecer requisitos com o usuario antes de iniciar. Documentar decisoes.",
            "technical": "Verificar SDK e dependencias. Usar versoes compativeis. Testar em ambiente isolado.",
            "external": "Implementar fallback local quando possivel. Usar cache de respostas.",
            "dependency": "Verificar instalacao antes de usar. Documentar versoes necessarias. Usar virtualenv/container.",
            "api": "Implementar retry com backoff. Validar schema da resposta. Usar mock em testes.",
            "permission": "Verificar permissoes antes de executar. Tentar diretorio alternativo se necessario.",
            "strategy": "Ter plano de fallback pronto. Reavaliar apos cada falha. Alternar para estrategia mais segura.",
        }

        mitigation = mitigations.get(category, "Monitorar e agir conforme necessario.")
        if severity in ("critical", "high"):
            mitigation += " [ACAO REQUERIDA ANTES DE PROSSEGUIR]"

        return mitigation

    def _generate_contingency(self, risk):
        category = risk.get("category", "")
        contingencies = {
            "environment": "Instalar ferramentas automaticamente ou usar alternativas nativas.",
            "complexity": "Reduzir escopo para funcionalidades essenciais apenas.",
            "ambiguity": "Documentar suposicoes e prosseguir com melhor estimativa.",
            "technical": "Buscar versao alternativa ou tecnologia substituta.",
            "external": "Usar dados mockados ou cached para continuar execucao.",
            "dependency": "Instalar dependencia automaticamente ou usar versao portavel.",
            "api": "Usar fallback com dados offline ou implementar mock.",
            "permission": "Solicitar elevacao de privilegio ou usar diretorio diferente.",
            "strategy": "Selecionar proxima melhor estrategia do ranking.",
        }
        return contingencies.get(category, "Avaliar impacto e decidir entre retry, fallback ou abortar.")
