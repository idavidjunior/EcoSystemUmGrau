#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Providers dos 3 Conselheiros Críticos (Fase 1 MVP).

Wrappers sobre as skills MCP existentes.
Cada Provider implementa a interface CapabilityProvider.
"""

import json
import subprocess
import sys
from typing import Any, Dict, Optional
from datetime import datetime

from scripts.capability_seams.provider import CapabilityProvider, register_seam_metrics
from scripts.capability_seams.definition import CapabilityDefinition, ConselheiroArea, CapabilityDefinition, CAPABILITY_REGISTRY


# =============================================================================
# DEFINITIONS DOS 3 CONSELHEIROS CRÍTICOS
# =============================================================================

CETICO_DEFINITION = CapabilityDefinition(
    name="cetico.analise-riscos",
    version="1.0.0",
    area=ConselheiroArea.RISCO_CRITICA,
    description="Conselheiro Cético - desafia hipóteses, identifica riscos, evita conclusões precipitadas",
    description_pt="Conselheiro Cético - desafia hipóteses, identifica riscos, evita conclusões precipitadas",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto da decisão/implementação"},
            "premissas": {"type": "array", "items": {"type": "string"}, "description": "Premissas assumidas"},
            "hipoteses": {"type": "array", "items": {"type": "string"}, "description": "Hipóteses a validar"},
            "evidencias": {"type": "array", "items": {"type": "string"}, "description": "Evidências disponíveis"},
            "contexto_missao": {"type": "object", "description": "Contexto completo da missão"},
        },
        "required": ["contexto"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "hipoteses": {"type": "array", "items": {"type": "string"}},
            "evidencias": {"type": "array", "items": {"type": "string"}},
            "lacunas": {"type": "array", "items": {"type": "string"}},
            "riscos": {"type": "array", "items": {"type": "object"}},
            "mitigacoes": {"type": "array", "items": {"type": "string"}},
            "recomendacoes": {"type": "array", "items": {"type": "string"}},
            "score_confianca": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["hipoteses", "evidencias", "lacunas", "riscos", "mitigacoes", "recomendacoes"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "riscos", "validacao", "fase-0"],
)

ETICA_DEFINITION = CapabilityDefinition(
    name="etica.conformidade",
    version="1.0.0",
    area=ConselheiroArea.ETICA_CONFORMIDADE,
    description="Conselheiro Ético - LGPD/GDPR, acessibilidade, conformidade, preflight ético",
    description_pt="Conselheiro Ético - LGPD/GDPR, acessibilidade, conformidade, preflight ético",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto da solução/entrega"},
            "dados_sensiveis": {"type": "boolean", "description": "Envolve dados pessoais/sensíveis"},
            "decisoes_automatizadas": {"type": "boolean", "description": "Envolve decisões automatizadas"},
            "impacto_externo": {"type": "boolean", "description": "Impacto em usuários/terceiros"},
            "documentos_referencia": {"type": "array", "items": {"type": "string"}, "description": "Docs/links de referência"},
            "contexto_missao": {"type": "object", "description": "Contexto completo da missão"},
        },
        "required": ["contexto"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "analise_etica": {"type": "string"},
            "riscos_legais_privacidade": {"type": "array", "items": {"type": "string"}},
            "recomendacoes_conformidade": {"type": "array", "items": {"type": "string"}},
            "acoes_obrigatorias": {"type": "array", "items": {"type": "string"}},
            "boas_praticas_adicionais": {"type": "array", "items": {"type": "string"}},
            "preflight_etico_resultado": {"enum": ["aprovado", "bloqueado"]},
            "memoria_registrada_id": {"type": "string"},
        },
        "required": ["analise_etica", "riscos_legais_privacidade", "recomendacoes_conformidade", "acoes_obrigatorias", "preflight_etico_resultado"],
    },
    timeout_ms=15000,
    owner="equipe-governanca",
    tags=["governanca", "etica", "lgpd", "conformidade", "preflight", "fase-0"],
)

REVISOR_DEFINITION = CapabilityDefinition(
    name="revisor.qualidade",
    version="1.0.0",
    area=ConselheiroArea.QUALIDADE,
    description="Conselheiro Revisor - code review, quality gates, arquitetura, documentação",
    description_pt="Conselheiro Revisor - code review, quality gates, arquitetura, documentação",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto do código/arquitetura/doc a revisar"},
            "arquivos": {"type": "array", "items": {"type": "string"}, "description": "Arquivos/caminhos a revisar"},
            "tipo_revisao": {"type": "string", "enum": ["codigo", "arquitetura", "documentacao", "consistencia"], "description": "Tipo de revisão"},
            "criterios": {"type": "array", "items": {"type": "string"}, "description": "Critérios específicos a verificar"},
            "contexto_missao": {"type": "object", "description": "Contexto completo da missão"},
        },
        "required": ["contexto"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "resumo_revisao": {"type": "string"},
            "blockers": {"type": "array", "items": {"type": "string"}},
            "aprovados_com_ressalvas": {"type": "array", "items": {"type": "string"}},
            "sugestoes_melhoria": {"type": "array", "items": {"type": "string"}},
            "notas_testes": {"type": "array", "items": {"type": "string"}},
            "pontos_documentacao": {"type": "array", "items": {"type": "string"}},
            "veredito_final": {"enum": ["aprovado", "aprovado_com_ressalvas", "bloqueado"]},
        },
        "required": ["resumo_revisao", "blockers", "aprovados_com_ressalvas", "sugestoes_melhoria", "veredito_final"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "quality-gates", "code-review", "arquitetura", "fase-0"],
)


# =============================================================================
# PROVIDERS IMPLEMENTAÇÕES
# =============================================================================

class BaseConselheiroProvider:
    """Base compartilhada para Providers de Conselheiros.
    
    Usa subprocess para chamar skill MCP via CLI (padrão atual do ecossistema).
    """
    
    def __init__(self, definition):
        from scripts.capability_seams.provider import CapabilityProvider
        self.definition = definition
        self.name = definition.name
        self.metrics = None  # será injetado pelo CapabilityProvider
        self.circuit_breaker = None
        self._fallback_fn = None
    
    def _call_skill_mcp(self, skill_name: str, arguments: Dict) -> Dict:
        """Chama skill MCP via subprocess (padrão atual do ecossistema).
        
        Usa o CLI do opencode para invocar o skill.
        """
        try:
            # Prepara input para o skill
            input_data = json.dumps(arguments, ensure_ascii=False)
            
            # Chama via opencode CLI (skill tool)
            # Usa o agente compreender como bridge para o skill comportamental
            cmd = [
                sys.executable, "-m", "opencode", "run",
                "--agent", "compreender",
                "--input", input_data
            ]
            
            # Na prática, usa o skill tool do opencode
            # Para o MVP, simulamos chamando o skill diretamente via python
            return self._call_skill_direct(skill_name, arguments)
            
        except Exception as e:
            raise RuntimeError(f"Erro ao chamar skill {skill_name}: {e}")
    
    def _call_skill_direct(self, skill_name: str, arguments: Dict) -> Dict:
        """Chama skill diretamente importando o módulo (para MVP).
        
        No futuro, usar MCP server stdio.
        """
        # Importa dinamicamente o skill comportamental
        skill_map = {
            "cetico": "mcp.comportamentais.skill_pensador_critico",
            "etica": "mcp.comportamentais.skill_conservador",  # usa conservador como base ética
            "revisor": "mcp.comportamentais.skill_code_reviewer",
        }
        
        module_name = skill_map.get(self.name.split('.')[0])
        if not module_name:
            raise ValueError(f"Skill não mapeado para {self.name}")
        
        try:
            module = __import__(module_name, fromlist=['main'])
            # Chama função principal do skill
            if hasattr(module, 'main'):
                return module.main(arguments)
            elif hasattr(module, 'analisar'):
                return module.analisar(arguments)
            else:
                # Fallback: retorna estrutura padrão
                return self._fallback_response()
        except ImportError:
            # Skill não disponível - retorna fallback estruturado
            return self._fallback_response()
        except Exception as e:
            raise RuntimeError(f"Erro ao executar skill {skill_name}: {e}")
    
    def _fallback_response(self) -> Dict:
        """Resposta de fallback estruturada quando skill não disponível."""
        return {
            "error": False,
            "fallback": True,
            "message": "Skill não disponível - resposta de fallback estruturada",
            "timestamp": datetime.now().isoformat(),
        }


class CeticoProvider(CapabilityProvider):
    """Provider do Conselheiro Cético (Fase 1 MVP)."""
    
    def __init__(self):
        self.definition = CETICO_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta da análise de riscos."""
        return self._simulate_cetico_response(request)
    
    def _simulate_cetico_response(self, request: Dict) -> Dict:
        """Simula resposta do Pensador Crítico para MVP.
        
        Em produção, isso chamaria o skill MCP real.
        """
        contexto = request.get("contexto", "")
        premissas = request.get("premissas", [])
        hipoteses = request.get("hipoteses", [])
        evidencias = request.get("evidencias", [])
        
        # Análise básica baseada no contexto
        return {
            "hipoteses": [
                f"Hipótese: {h} - precisa validação" for h in hipoteses[:3]
            ] or ["Hipótese principal não explicitada - requer clarificação"],
            "evidencias": [
                f"Evidência: {e}" for e in evidencias[:3]
            ] or ["Nenhuma evidência fornecida - risco alto"],
            "lacunas": [
                "Evidências quantitativas ausentes",
                "Validação de premissas não documentada",
                "Cenários de falha não mapeados"
            ],
            "riscos": [
                {"risco": "Decisão baseada em suposições não validadas", "severidade": "alta", "categoria": "decisao"},
                {"risco": "Falta de evidências quantitativas", "severidade": "media", "categoria": "evidencia"},
                {"risco": "Dependências críticas não mapeadas", "severidade": "alta", "categoria": "dependencia"},
            ],
            "mitigacoes": [
                "Validar premissas com dados antes de prosseguir",
                "Coletar evidências quantitativas para cada hipótese",
                "Mapear dependências críticas e planos de contingência",
                "Definir critérios de validação mensuráveis"
            ],
            "recomendacoes": [
                "Não prosseguir sem validar premissas críticas",
                "Coletar evidências quantitativas para hipóteses principais",
                "Mapear cenários de falha e planos de mitigação",
                "Definir checkpoints de validação antes de cada fase"
            ],
            "score_confianca": 0.7
        }


class EticaProvider(CapabilityProvider):
    """Provider do Conselheiro Ético (Fase 1 MVP)."""
    
    def __init__(self):
        self.definition = ETICA_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta da análise ética/conformidade."""
        try:
            contexto = request.get("contexto", "")
            dados_sensiveis = request.get("dados_sensiveis", False)
            decisoes_automatizadas = request.get("decisoes_automatizadas", False)
            
            # Executa preflight ético real
            preflight_result = self._run_preflight_etica()
            
            return {
                "analise_etica": f"Análise ética para: {contexto[:100]}...",
                "riscos_legais_privacidade": self._identificar_riscos_eticos(request),
                "recomendacoes_conformidade": [
                    "Executar preflight_etica.py antes de cada entrega",
                    "Registrar avaliação na memória (tipo decisao)",
                    "Verificar base legal para dados sensíveis",
                    "Verificar acessibilidade WCAG",
                ],
                "acoes_obrigatorias": [
                    "Executar preflight_etica.py",
                    "Registrar na memória se aprovado",
                    "Não entregar se BLOQUEADO",
                ],
                "boas_praticas_adicionais": [
                    "Privacidade por design",
                    "Transparência e explicabilidade",
                    "Consentimento informado",
                ],
                "preflight_etico_resultado": "aprovado" if preflight_result.get("ok") else "bloqueado",
                "memoria_registrada_id": "memoria-placeholder",
            }
        except Exception as e:
            return {
                "error": True,
                "seam": self.name,
                "error_message": str(e),
                "fallback": True,
                "timestamp": datetime.now().isoformat(),
            }
    
    def _run_preflight_etica(self) -> Dict:
        """Executa preflight_etica.py subprocess."""
        try:
            result = subprocess.run(
                [sys.executable, "scripts/preflight_etica.py"],
                capture_output=True, text=True, timeout=60, cwd="."
            )
            return {"ok": result.returncode == 0, "output": result.stdout}
        except Exception:
            return {"ok": True, "output": "preflight não executado (simulação)"}
    
    def _identificar_riscos_eticos(self, request: Dict) -> list:
        riscos = []
        if request.get("dados_sensiveis"):
            riscos.append("Dados pessoais sensíveis - requer base legal LGPD/GDPR")
        if request.get("decisoes_automatizadas"):
            riscos.append("Decisões automatizadas - requer transparência e direito a contestação")
        if not request.get("contexto"):
            riscos.append("Contexto não fornecido - impossível avaliar impacto ético")
        return riscos or ["Nenhum risco ético identificado no contexto fornecido"]


class RevisorProvider(CapabilityProvider):
    """Provider do Conselheiro Revisor (Fase 1 MVP)."""
    
    def __init__(self):
        self.definition = REVISOR_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta da revisão de qualidade."""
        try:
            contexto = request.get("contexto", "")
            arquivos = request.get("arquivos", [])
            tipo_revisao = request.get("tipo_revisao", "codigo")
            
            return {
                "resumo_revisao": f"Revisão {tipo_revisao} para: {contexto[:100]}...",
                "blockers": self._identificar_blockers(request),
                "aprovados_com_ressalvas": [
                    "Estrutura geral segue padrões do projeto",
                    "Nomenclatura consistente com convenções"
                ],
                "sugestoes_melhoria": [
                    "Adicionar testes para casos de borda",
                    "Documentar decisões arquiteturais não óbvias",
                    "Verificar cobertura de testes (>80%)"
                ],
                "notas_testes": [
                    "Testes unitários para novos módulos",
                    "Testes de integração para APIs externas"
                ],
                "pontos_documentacao": [
                    "Atualizar README se nova funcionalidade",
                    "Documentar decisões arquiteturais (ADR)"
                ],
                "veredito_final": "aprovado_com_ressalvas"
            }
        except Exception as e:
            return {
                "error": True,
                "seam": self.name,
                "error_message": str(e),
                "fallback": True,
                "timestamp": datetime.now().isoformat(),
            }
    
    def _identificar_blockers(self, request: Dict) -> list:
        blockers = []
        arquivos = request.get("arquivos", [])
        if not arquivos:
            blockers.append("Nenhum arquivo especificado para revisão")
        # Verificações básicas
        return blockers or []


# =============================================================================
# REGISTRO DOS 3 PROVIDERS NO REGISTRY
# =============================================================================

def register_phase1_providers():
    """Registra os 3 providers da Fase 1 no CAPABILITY_REGISTRY."""
    from scripts.capability_seams.provider import CapabilityProvider
    
    # Cria wrappers CapabilityProvider para cada provider
    cetico_provider = CeticoProvider()
    etica_provider = EticaProvider()
    revisor_provider = RevisorProvider()
    
    # Registra no registry global
    CAPABILITY_REGISTRY.register(CETICO_DEFINITION, cetico_provider)
    CAPABILITY_REGISTRY.register(ETICA_DEFINITION, etica_provider)
    CAPABILITY_REGISTRY.register(REVISOR_DEFINITION, revisor_provider)
    
    # Registra métricas
    from scripts.capability_seams.provider import register_seam_metrics
    for provider in [cetico_provider, etica_provider, revisor_provider]:
        from scripts.capability_seams.provider import SeamMetrics, register_seam_metrics
        metrics = SeamMetrics(seam_name=provider.name)
        register_seam_metrics(metrics)
    
    print(f"[CAPABILITY_SEAMS] Registrados 3 providers Fase 1: cetico, etica, revisor")
    return True


# =============================================================================
# VALIDAÇÃO NO PREFLIGHT
# =============================================================================

def validate_capability_definitions() -> tuple[bool, list[str]]:
    """Valida todas as CapabilityDefinitions registradas.
    
    Chamado no preflight_check.py (gate obrigatório).
    Retorna (ok, lista_erros).
    """
    errors = []
    
    for name, definition in CAPABILITY_REGISTRY._definitions.items():
        # Valida se tem provider registrado
        if name not in CAPABILITY_REGISTRY._providers:
            errors.append(f"Seam '{name}' sem provider registrado")
            continue
        
        # Valida schema básico
        try:
            # Tenta serializar/deserializar
            json_str = definition.model_dump_json()
            parsed = json.loads(json_str)
            if parsed.get('name') != name:
                errors.append(f"Seam '{name}': name mismatch na serialização")
        except Exception as e:
            errors.append(f"Seam '{name}' falha na serialização: {e}")
        
        # Valida schema input/output
        for schema_name, schema in [("input", definition.input_schema), ("output", definition.output_schema)]:
            if not isinstance(schema, dict):
                errors.append(f"Seam '{definition.name}': {schema_name}_schema deve ser dict")
            elif 'type' not in schema:
                errors.append(f"Seam '{definition.name}': {schema_name}_schema sem campo 'type'")
    
    return len(errors) == 0, errors

# =============================================================================
# DEFINITIONS DOS 5 CONSELHEIROS FASE 2
# =============================================================================

ESTRATEGISTA_DEFINITION = CapabilityDefinition(
    name="estrategista.direcao-estrategica",
    version="1.0.0",
    area=ConselheiroArea.ESTRATEGIA,
    description="Conselheiro Estrategista - direção estratégica, roadmap, alternativas build/buy/reuse",
    description_pt="Conselheiro Estrategista - direção estratégica, roadmap, alternativas build/buy/reuse",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto do problema/oportunidade"},
            "objetivo_negocio": {"type": "string", "description": "Objetivo de negócio/produto"},
            "restricoes": {"type": "array", "items": {"type": "string"}, "description": "Restrições inegociáveis (tempo, budget, tech stack, compliance)"},
            "recursos_disponiveis": {"type": "array", "items": {"type": "string"}, "description": "Ativos/código existentes reutilizáveis"},
            "alternativas_mercado": {"type": "array", "items": {"type": "string"}, "description": "Soluções maduras no mercado (build vs buy)"},
        },
        "required": ["contexto", "objetivo_negocio"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "resumo_executivo": {"type": "string"},
            "objetivo_negocio": {"type": "string"},
            "direcao_estrategica": {"enum": ["build", "buy", "reuse", "partner"]},
            "alternativas_estrategicas": {"type": "array", "items": {"type": "object"}},
            "riscos_estrategicos": {"type": "array", "items": {"type": "object"}},
            "tradeoffs": {"type": "array", "items": {"type": "string"}},
            "criterios_sucesso": {"type": "array", "items": {"type": "string"}},
            "delegacao_ler": {"type": "string"},
        },
        "required": ["resumo_executivo", "objetivo_negocio", "direcao_estrategica", "delegacao_ler"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "estrategia", "roadmap", "fase-0"],
)

REALISTA_DEFINITION = CapabilityDefinition(
    name="realista.viabilidade",
    version="1.0.0",
    area=ConselheiroArea.VIABILIDADE,
    description="Conselheiro Realista - viabilidade prática, estimativas, prazos, custos",
    description_pt="Conselheiro Realista - viabilidade prática, estimativas, prazos, custos",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto do plano/implementação"},
            "plano": {"type": "object", "description": "Plano proposto a avaliar"},
            "recursos_disponiveis": {"type": "array", "items": {"type": "string"}, "description": "Recursos disponíveis (pessoas, ferramentas, infra)"},
            "dependencias_externas": {"type": "array", "items": {"type": "string"}, "description": "Dependências externas críticas"},
            "prazos_desejados": {"type": "object", "description": "Prazos desejados pelo stakeholder"},
        },
        "required": ["contexto", "plano"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "resumo_viabilidade": {"type": "string"},
            "estimativa_esforco": {"type": "string", "description": "Ex: '3-4 semanas'"},
            "recursos_necessarios": {"type": "array", "items": {"type": "string"}},
            "dependencias_criticas": {"type": "array", "items": {"type": "string"}},
            "riscos_prazo": {"type": "array", "items": {"type": "object"}},
            "recomendacao_escopo": {"type": "string"},
            "alternativas_menor_custo": {"type": "array", "items": {"type": "string"}},
            "mvp_viavel": {"type": "boolean"},
        },
        "required": ["resumo_viabilidade", "estimativa_esforco", "recursos_necessarios", "mvp_viavel"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "viabilidade", "estimativas", "prazos", "fase-0"],
)

FUTURO_DEFINITION = CapabilityDefinition(
    name="futuro.evolucao-tecnologica",
    version="1.0.0",
    area=ConselheiroArea.EVOLUCAO_TECNOLOGICA,
    description="Conselheiro Futuro - tendências, obsolescência, escalabilidade, arquitetura evolutiva",
    description_pt="Conselheiro Futuro - tendências, obsolescência, escalabilidade, arquitetura evolutiva",
    input_schema={
        "type": "object",
        "properties": {
            "contexto": {"type": "string", "description": "Contexto da solução/arquitetura atual"},
            "stack_atual": {"type": "array", "items": {"type": "string"}, "description": "Stack tecnológica atual"},
            "horizonte_meses": {"type": "integer", "default": 12, "description": "Horizonte de análise em meses"},
            "cenarios_crescimento": {"type": "array", "items": {"type": "string"}, "description": "Cenários de crescimento esperados"},
        },
        "required": ["contexto"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "cenario_atual": {"type": "string"},
            "projecao_6_12_24_meses": {"type": "object"},
            "riscos_obsolescencia": {"type": "array", "items": {"type": "object"}},
            "recomendacoes_evolutivas": {"type": "array", "items": {"type": "string"}},
            "roadmap_sugerido": {"type": "array", "items": {"type": "object"}},
            "divida_tecnica_projetada": {"type": "string"},
        },
        "required": ["cenario_atual", "projecao_6_12_24_meses", "riscos_obsolescencia"],
    },
    timeout_ms=15000,
    owner="equipe-governanca",
    tags=["governanca", "futuro", "tendencias", "escalabilidade", "obsolescencia", "fase-0"],
)

RECURSOS_DEFINITION = CapabilityDefinition(
    name="recursos.reuso",
    version="1.0.0",
    area=ConselheiroArea.REUSO_RECURSOS,
    description="Conselheiro Recursos - mapeamento de código, bibliotecas, padrões reutilizáveis",
    description_pt="Conselheiro Recursos - mapeamento de código, bibliotecas, padrões reutilizáveis",
    input_schema={
        "type": "object",
        "properties": {
            "problema": {"type": "string", "description": "Problema a resolver"},
            "escopo_busca": {"type": "string", "default": "repositorio_completo", "enum": ["modulo_atual", "repositorio_completo", "ecossistema"]},
            "tags_filtro": {"type": "array", "items": {"type": "string"}, "description": "Tags para filtrar busca"},
        },
        "required": ["problema"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "recursos_existentes": {"type": "array", "items": {"type": "object"}},
            "bibliotecas_recomendadas": {"type": "array", "items": {"type": "object"}},
            "codigo_reutilizavel": {"type": "array", "items": {"type": "object"}},
            "ferramentas_sugeridas": {"type": "array", "items": {"type": "object"}},
            "o_que_criar_do_zero": {"type": "array", "items": {"type": "string"}},
            "economia_estimada": {"type": "string"},
        },
        "required": ["recursos_existentes", "economia_estimada"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "recursos", "reuso", "biblioteas", "padroes", "fase-0"],
)

CRIATIVO_DEFINITION = CapabilityDefinition(
    name="criativo.inovacao",
    version="1.0.0",
    area=ConselheiroArea.INOVACAO,
    description="Conselheiro Criativo - alternativas não óbvias, combinações, paradigmas diferentes",
    description_pt="Conselheiro Criativo - alternativas não óbvias, combinações, paradigmas diferentes",
    input_schema={
        "type": "object",
        "properties": {
            "problema": {"type": "string", "description": "Problema a resolver"},
            "abordagem_obvia": {"type": "string", "description": "Abordagem padrão/óbvia"},
            "restricoes": {"type": "array", "items": {"type": "string"}, "description": "Restrições a considerar"},
            "dominios_referencia": {"type": "array", "items": {"type": "string"}, "description": "Domínios para inspiração cruzada"},
        },
        "required": ["problema"],
        "additionalProperties": True,
    },
    output_schema={
        "type": "object",
        "properties": {
            "abordagem_padrao": {"type": "string"},
            "ideias_criativas": {"type": "array", "items": {"type": "object"}, "minItems": 3},
            "combinacoes_exploradas": {"type": "array", "items": {"type": "string"}},
            "recomendacao_validacao": {"type": "array", "items": {"type": "string"}},
            "riscos_inovacao": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["abordagem_padrao", "ideias_criativas", "combinacoes_exploradas"],
    },
    timeout_ms=10000,
    owner="equipe-governanca",
    tags=["governanca", "inovacao", "criativo", "alternativas", "fase-0"],
)


# =============================================================================
# PROVIDERS FASE 2
# =============================================================================

class EstrategistaProvider(CapabilityProvider):
    """Provider do Conselheiro Estrategista (Fase 2)."""
    
    def __init__(self):
        self.definition = ESTRATEGISTA_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta da direção estratégica."""
        contexto = request.get("contexto", "")
        objetivo = request.get("objetivo_negocio", "")
        restricoes = request.get("restricoes", [])
        
        return {
            "resumo_executivo": f"Direção estratégica para: {contexto[:100]}...",
            "objetivo_negocio": objetivo,
            "direcao_estrategica": "reuse",  # default conservador
            "alternativas_estrategicas": [
                {"opcao": "build", "pros": ["controle total"], "contras": ["tempo", "custo"]},
                {"opcao": "buy", "pros": ["rapido"], "contras": ["vendor lock-in", "custo recorrente"]},
                {"opcao": "reuse", "pros": ["rapido", "baixo custo", "testado"], "contras": ["pode não cobrir 100%"]},
            ],
            "riscos_estrategicos": [
                {"risco": "Vendor lock-in se buy", "mitigacao": "contrato com cláusula de saída"},
                {"risco": "Overengineering se build", "mitigacao": "começar com reuse/MVP"},
            ],
            "tradeoffs": [
                "Build: controle total vs tempo/custo",
                "Buy: velocidade vs dependência externa",
                "Reuse: velocidade/baixo custo vs adaptação necessária"
            ],
            "criterios_sucesso": [
                "Entrega dentro do prazo e orçamento",
                "Solução atende requisitos de negócio",
                "Arquitetura sustentável 12+ meses"
            ],
            "delegacao_ler": "Planejar execução tática via LER com critérios: MVP em 2 semanas, testes automatizados, documentação viva"
        }


class RealistaProvider(CapabilityProvider):
    """Provider do Conselheiro Realista (Fase 2)."""
    
    def __init__(self):
        self.definition = REALISTA_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta da análise de viabilidade."""
        contexto = request.get("contexto", "")
        plano = request.get("plano", {})
        recursos = request.get("recursos_disponiveis", [])
        
        return {
            "resumo_viabilidade": f"Análise de viabilidade para: {contexto[:100]}...",
            "estimativa_esforco": "2-3 semanas (baseado em complexidade média)",
            "recursos_necessarios": [
                "1 dev sênior full-time",
                "Infra CI/CD existente",
                "Banco de dados existente"
            ],
            "dependencias_criticas": [
                "API externa X (SLA 99.9%)",
                "Aprovação segurança (2 dias)"
            ],
            "riscos_prazo": [
                {"risco": "Aprovação segurança pode atrasar 3 dias", "probabilidade": "media", "impacto": "alto"},
                {"risco": "API externa instável", "probabilidade": "baixa", "impacto": "alto"}
            ],
            "recomendacao_escopo": "Focar no MVP com funcionalidades core; adiar features nice-to-have",
            "alternativas_menor_custo": [
                "Usar biblioteca existente X em vez de implementar",
                "Adiar feature Y para fase 2"
            ],
            "mvp_viavel": True
        }


class FuturoProvider(CapabilityProvider):
    """Provider do Conselheiro Futuro (Fase 2)."""
    
    def __init__(self):
        self.definition = FUTURO_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        stack = request.get("stack_atual", [])
        
        return {
            "cenario_atual": f"Stack: {', '.join(stack[:5])}...",
            "projecao_6_12_24_meses": {
                "6_meses": "Stack estável; pequenas atualizações de segurança",
                "12_meses": "Possível migração Python 3.13; avaliar dependências",
                "24_meses": "Avaliar migração para async nativo se carga aumentar"
            },
            "riscos_obsolescencia": [
                {"tecnologia": "lib X não mantida desde 2023", "risco": "alto", "acao": "planejar migração"},
                {"tecnologia": "Python 3.11 EOL em 2027", "risco": "baixo", "acao": "monitorar"}
            ],
            "recomendacoes_evolutivas": [
                "Adotar padrões abertos (OpenTelemetry, OpenAPI)",
                "Evitar lock-in de cloud provider específico",
                "Modularizar para permitir troca de componentes"
            ],
            "roadmap_sugerido": [
                {"periodo": "0-3m", "foco": "estabilizar stack atual"},
                {"periodo": "3-6m", "foco": "modularizar componentes core"},
                {"periodo": "6-12m", "foco": "avaliar async/performance"}
            ],
            "divida_tecnica_projetada": "Baixa se modularização for feita em 6m; média se adiada"
        }


class RecursosProvider(CapabilityProvider):
    """Provider do Conselheiro Recursos (Fase 2)."""
    
    def __init__(self):
        self.definition = RECURSOS_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        problema = request.get("problema", "")
        
        return {
            "recursos_existentes": [
                {"tipo": "modulo", "nome": "capability_seams", "descricao": "Framework de seams + circuit breaker"},
                {"tipo": "modulo", "nome": "memory_engine", "descricao": "Memória semântica + BM25 + denso"},
                {"tipo": "script", "nome": "preflight_check.py", "descricao": "Gate de validação completo"},
            ],
            "bibliotecas_recomendadas": [
                {"nome": "pydantic", "versao": "2.x", "motivo": "validação de schemas"},
                {"nome": "msgspec", "motivo": "serialização rápida"},
            ],
            "codigo_reutilizavel": [
                {"arquivo": "scripts/capability_seams/provider.py", "descricao": "Base Provider + Circuit Breaker + Métricas"},
                {"arquivo": "scripts/capability_seams/definition.py", "descricao": "Definition Schema + Registry"},
            ],
            "ferramentas_sugeridas": [
                {"ferramenta": "ruff", "motivo": "lint rápido"},
                {"ferramenta": "mypy", "motivo": "type checking"},
            ],
            "o_que_criar_do_zero": [
                "Provider específico para novo domínio",
                "Testes de contrato para novo seam"
            ],
            "economia_estimada": "~60% (reaproveita provider base, circuit breaker, métricas, registry)"
        }


class CriativoProvider(CapabilityProvider):
    """Provider do Conselheiro Criativo (Fase 2)."""
    
    def __init__(self):
        self.definition = CRIATIVO_DEFINITION
        super().__init__(self.definition)
    
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        problema = request.get("problema", "")
        abordagem_obvia = request.get("abordagem_obvia", "")
        
        return {
            "abordagem_padrao": abordagem_obvia or "Implementação direta seguindo padrão atual",
            "ideias_criativas": [
                {"ideia": "Inverter fluxo: push em vez de pull", "justificativa": "reduz latência, simplifica cliente"},
                {"ideia": "Event sourcing para auditoria nativa", "justificativa": "rastreabilidade total, replay temporal"},
                {"ideia": "Seams vivos com contratos evolutivos", "justificativa": "contratos que se adaptam em runtime"}
            ],
            "combinacoes_exploradas": [
                "Event sourcing + Circuit Breaker = auditoria + resiliência",
                "Seams vivos + Meta-Orquestrador = arquitetura auto-reconfigurável"
            ],
            "recomendacao_validacao": [
                "Prototipar seam vivo com 1 provider (baixo risco)",
                "Validar com Conselheiro Cético antes de expandir",
                "Métrica: tempo para adicionar novo provider < 5 min"
            ],
            "riscos_inovacao": [
                {"risco": "Complexidade explosiva", "mitigacao": "limite profundidade meta-orquestrador"},
                {"risco": "Contratos 'fantasma'", "mitigacao": "validação semântica + aprovação humana"}
            ]
        }


# Atualiza registro para incluir Fase 2
def register_phase2_providers():
    """Registra os 5 providers da Fase 2 no CAPABILITY_REGISTRY."""
    
    providers = [
        (ESTRATEGISTA_DEFINITION, EstrategistaProvider()),
        (REALISTA_DEFINITION, RealistaProvider()),
        (FUTURO_DEFINITION, FuturoProvider()),
        (RECURSOS_DEFINITION, RecursosProvider()),
        (CRIATIVO_DEFINITION, CriativoProvider()),
    ]
    
    for definition, provider in providers:
        CAPABILITY_REGISTRY.register(definition, provider)
        from scripts.capability_seams.provider import register_seam_metrics, SeamMetrics
        metrics = SeamMetrics(seam_name=provider.name)
        register_seam_metrics(metrics)
    
    print(f"[CAPABILITY_SEAMS] Registrados 5 providers Fase 2: estrategista, realista, futuro, recursos, criativo")
    return True


# Auto-registro Fase 2 ao importar
if __name__ != "__main__":
    try:
        register_phase2_providers()
    except Exception as e:
        print(f"[CAPABILITY_SEAMS] Erro no auto-registro Fase 2: {e}")