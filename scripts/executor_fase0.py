#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executor Governado — Fase 0: Consulta aos 8 Conselheiros via Capability Seams.

Implementa a consulta obrigatória aos 8 Conselheiros via Capability Registry.
Consolida respostas em "Pareceres do Conselho" e detecta bloqueios.
"""

import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa providers_phase1 para disparar auto-registro
import scripts.capability_seams.providers_phase1
from scripts.capability_seams.definition import CAPABILITY_REGISTRY
from scripts.capability_seams.provider import get_all_seam_metrics


# Ordem obrigatória dos 8 Conselheiros na Fase 0 (conforme EXECUTOR-GOVERNADO.md)
CONSELHEIROS_ORDEM = [
    "estrategista.direcao-estrategica",
    "cetico.analise-riscos", 
    "realista.viabilidade",
    "etica.conformidade",
    "futuro.evolucao-tecnologica",
    "recursos.reuso",
    "criativo.inovacao",
    "revisor.qualidade",
]


@dataclass
class ParecerConselheiro:
    """Parecer individual de um conselheiro."""
    seam_name: str
    area: str
    success: bool
    response: Dict
    latency_ms: float
    timestamp: str
    error: Optional[str] = None


@dataclass
class PareceresConselho:
    """Consolidação dos pareceres dos 8 conselheiros."""
    mission_id: str
    timestamp: str
    pareceres: List[ParecerConselheiro] = field(default_factory=list)
    bloqueios: List[str] = field(default_factory=list)
    consolidadado: bool = False
    
    def adicionar(self, parecer: ParecerConselheiro):
        self.pareceres.append(parecer)
        if not parecer.success:
            self.bloqueios.append(f"{parecer.seam_name}: {parecer.error}")
        elif parecer.response.get("blockers") or parecer.response.get("bloqueios"):
            # Conselheiro pode retornar blockers no response
            blockers = parecer.response.get("blockers") or parecer.response.get("bloqueios", [])
            for b in blockers:
                self.bloqueios.append(f"{parecer.seam_name}: {b}")
    
    def tem_bloqueios(self) -> bool:
        return len(self.bloqueios) > 0
    
    def to_dict(self) -> Dict:
        return {
            "mission_id": self.mission_id,
            "timestamp": self.timestamp,
            "total_consultados": len(self.pareceres),
            "sucessos": sum(1 for p in self.pareceres if p.success),
            "falhas": sum(1 for p in self.pareceres if not p.success),
            "bloqueios": self.bloqueios,
            "pareceres": [
                {
                    "seam": p.seam_name,
                    "area": p.area,
                    "success": p.success,
                    "latency_ms": p.latency_ms,
                    "response": p.response,
                    "error": p.error,
                }
                for p in self.pareceres
            ],
        }
    
    def salvar(self, caminho: str = "contexto/pareceres-conselho.md"):
        """Salva pareceres consolidados em Markdown."""
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        md = [f"# Pareceres do Conselho — Missão {self.mission_id}", 
              f"**Timestamp:** {self.timestamp}",
              f"**Total consultados:** {len(self.pareceres)}",
              f"**Sucessos:** {sum(1 for p in self.pareceres if p.success)}",
              f"**Falhas:** {sum(1 for p in self.pareceres if not p.success)}",
              f"**Bloqueios:** {len(self.bloqueios)}",
              ""]
        
        if self.bloqueios:
            md.append("## ⚠️ BLOQUEIOS DETECTADOS")
            for b in self.bloqueios:
                md.append(f"- {b}")
            md.append("")
        
        md.append("## PARECERES DETALHADOS")
        for p in self.pareceres:
            status = "✅" if p.success else "❌"
            md.append(f"### {status} {p.seam_name} ({p.latency_ms:.1f}ms)")
            md.append(f"**Área:** {p.area}")
            if p.error:
                md.append(f"**Erro:** {p.error}")
            else:
                # Resumo da resposta
                resp = p.response
                if isinstance(resp, dict):
                    for k, v in resp.items():
                        if isinstance(v, (str, int, float, bool)):
                            md.append(f"- **{k}:** {v}")
                        elif isinstance(v, list) and v:
                            md.append(f"- **{k}:** {len(v)} itens")
            md.append("")
        
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(md))


class Fase0Conselheiros:
    """Executa Fase 0: Consulta obrigatória aos 8 Conselheiros via Capability Seams."""
    
    def __init__(self):
        self.registry = CAPABILITY_REGISTRY
        self.metrics = {}
        # Debug: verifica o que tem no registry
        print(f"[DEBUG] Registry definitions: {list(CAPABILITY_REGISTRY._definitions.keys())}")
        print(f"[DEBUG] Registry providers: {list(CAPABILITY_REGISTRY._providers.keys())}")
    
    def executar(self, mission_id: str, contexto: Dict[str, Any]) -> PareceresConselho:
        """Executa consulta a todos os 8 conselheiros em sequência.
        
        Args:
            mission_id: ID único da missão
            contexto: Contexto da missão (problema, objetivo, restrições, etc.)
        
        Returns:
            PareceresConselho consolidado com todos os pareceres e bloqueios.
        """
        print(f"\n{'='*60}")
        print(f"FASE 0 — CONSULTA AOS 8 CONSELHEIROS")
        print(f"Missão: {mission_id}")
        print(f"{'='*60}")
        
        pareceres = PareceresConselho(
            mission_id=mission_id,
            timestamp=datetime.now().isoformat()
        )
        
        contexto_base = {
            "mission_id": mission_id,
            **contexto
        }
        
        for i, seam_name in enumerate(CONSELHEIROS_ORDEM, 1):
            print(f"\n[{i}/8] Consultando {seam_name}...")
            
            provider = self.registry.get_provider(seam_name)
            definition = self.registry.get_definition(seam_name)
            
            if not provider or not definition:
                print(f"  ⚠️  Seam não encontrado: {seam_name}")
                parecer = ParecerConselheiro(
                    seam_name=seam_name,
                    area=definition.area.value if definition else "desconhecida",
                    success=False,
                    response={},
                    latency_ms=0,
                    timestamp=datetime.now().isoformat(),
                    error="Seam não registrado no registry"
                )
                pareceres.adicionar(parecer)
                continue
            
            # Prepara request padronizado
            request = {
                "contexto": contexto.get("problema", "") or contexto.get("objetivo", "") or "Missão sem contexto explícito",
                "contexto_missao": contexto_base,
            }
            
            # Adiciona campos específicos por conselheiro
            request.update(self._preparar_request_especifico(seam_name, contexto))
            
            # Executa com medição de latência
            start = time.time()
            try:
                response = provider.execute(
                    request=request,
                    context={"mission_id": mission_id, **contexto_base}
                )
                latency_ms = (time.time() - start) * 1000
                
                parecer = ParecerConselheiro(
                    seam_name=seam_name,
                    area=definition.area.value,
                    success=True,
                    response=response,
                    latency_ms=latency_ms,
                    timestamp=datetime.now().isoformat()
                )
                print(f"  ✅ {seam_name} — {latency_ms:.1f}ms")
                
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                parecer = ParecerConselheiro(
                    seam_name=seam_name,
                    area=definition.area.value,
                    success=False,
                    response={},
                    latency_ms=latency_ms,
                    timestamp=datetime.now().isoformat(),
                    error=str(e)
                )
                print(f"  ❌ {seam_name} — {latency_ms:.1f}ms — ERRO: {e}")
            
            pareceres.adicionar(parecer)
        
        # Salva consolidado
        # pareceres.consolidar()  # já consolidado via adicionar()
        pareceres.salvar()
        
        # Log de métricas
        self._log_metrics(mission_id)
        
        print(f"\n{'='*60}")
        print(f"FASE 0 CONCLUÍDA")
        print(f"Sucessos: {sum(1 for p in pareceres.pareceres if p.success)}/8")
        print(f"Bloqueios: {len(pareceres.bloqueios)}")
        print(f"Arquivo: contexto/pareceres-conselho.md")
        print(f"{'='*60}\n")
        
        return pareceres
    
    def _preparar_request_especifico(self, seam_name: str, contexto: Dict) -> Dict:
        """Adiciona campos específicos por conselheiro."""
        extra = {}
        
        if "cetico" in seam_name:
            extra.update({
                "premissas": contexto.get("premissas", []),
                "hipoteses": contexto.get("hipoteses", []),
                "evidencias": contexto.get("evidencias", []),
            })
        elif "etica" in seam_name:
            extra.update({
                "dados_sensiveis": contexto.get("dados_sensiveis", False),
                "decisoes_automatizadas": contexto.get("decisoes_automatizadas", False),
            })
        elif "revisor" in seam_name:
            extra.update({
                "arquivos": contexto.get("arquivos", []),
                "tipo_revisao": contexto.get("tipo_revisao", "codigo"),
            })
        elif "estrategista" in seam_name:
            extra.update({
                "objetivo_negocio": contexto.get("objetivo_negocio", ""),
                "restricoes": contexto.get("restricoes", []),
            })
        elif "realista" in seam_name:
            extra.update({
                "plano": contexto.get("plano", {}),
                "recursos_disponiveis": contexto.get("recursos_disponiveis", []),
            })
        elif "futuro" in seam_name:
            extra.update({
                "stack_atual": contexto.get("stack_atual", []),
            })
        elif "recursos" in seam_name:
            extra.update({
                "problema": contexto.get("problema", ""),
            })
        elif "criativo" in seam_name:
            extra.update({
                "abordagem_obvia": contexto.get("abordagem_obvia", ""),
                "restricoes": contexto.get("restricoes", []),
            })
        
        return extra
    
    def _log_metrics(self, mission_id: str):
        """Log métricas consolidadas da Fase 0."""
        from scripts.capability_seams.provider import get_all_seam_metrics
        metrics = get_all_seam_metrics()
        
        log_entry = {
            "mission_id": mission_id,
            "timestamp": datetime.now().isoformat(),
            "phase": "fase_0_conselheiros",
            "seams": metrics  # já é dict com to_dict() aplicado
        }
        
        # Salva em log dedicado
        log_dir = "runtime/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"fase0_metrics_{mission_id}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)


def executar_fase_0(mission_id: str, contexto: Dict[str, Any]) -> Dict:
    """Função de conveniência para invocar Fase 0."""
    fase0 = Fase0Conselheiros()
    pareceres = fase0.executar(mission_id, contexto)
    return pareceres.to_dict()


if __name__ == "__main__":
    # Teste rápido
    resultado = executar_fase_0(
        mission_id="teste-fase0-001",
        contexto={
            "problema": "Implementar módulo de pagamentos",
            "objetivo_negocio": "Permitir pagamentos via PIX e cartão",
            "restricoes": ["PCI-DSS", "LGPD", "prazo 2 semanas"],
            "premissas": ["Stripe disponível", "Equipe conhece Python"],
            "hipoteses": ["Stripe é melhor que Mercado Pago"],
            "evidencias": ["Benchmarks de 2024 mostram Stripe 15% mais barato"],
            "dados_sensiveis": True,
            "decisoes_automatizadas": False,
            "arquivos": ["payment.py", "webhook.py"],
            "tipo_revisao": "codigo",
            "objetivo_negocio": "Módulo de pagamentos",
            "restricoes": ["PCI-DSS", "LGPD"],
            "plano": {"fases": ["integracao", "testes", "deploy"]},
            "recursos_disponiveis": ["1 dev", "CI/CD"],
            "stack_atual": ["Python 3.12", "FastAPI", "PostgreSQL"],
            "problema": "Como evitar duplicação de código de pagamento?",
            "abordagem_obvia": "Criar service PaymentService genérico",
        }
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))