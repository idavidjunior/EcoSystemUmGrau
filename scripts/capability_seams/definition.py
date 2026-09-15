#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capability Definition Schema — Contrato único para Conselheiros (Capability Seams).

Define a interface tipada que cada Conselheiro deve implementar.
Validado no preflight_check.py (gate obrigatório).
"""

import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ConselheiroArea(str, Enum):
    """Áreas de atuação dos Conselheiros."""
    ESTRATEGIA = "estrategia"
    RISCO_CRITICA = "risco-critica"
    VIABILIDADE = "viabilidade"
    ETICA_CONFORMIDADE = "etica-conformidade"
    EVOLUCAO_TECNOLOGICA = "evolucao-tecnologica"
    REUSO_RECURSOS = "reuso-recursos"
    INOVACAO = "inovacao"
    QUALIDADE = "qualidade"


class RetryPolicy(BaseModel):
    """Política de retry para o seam."""
    max_attempts: int = Field(default=2, ge=1, le=5)
    backoff_ms: int = Field(default=200, ge=0, le=10000)
    exponential: bool = Field(default=True)


class CapabilityDefinition(BaseModel):
    """Contrato único (Single Source of Truth) para um Conselheiro/Seam.
    
    Validado no preflight_check.py (gate obrigatório).
    Cada Conselheiro deve registrar sua Definition no registry.
    """
    name: str = Field(..., description="Identificador único do seam (ex: 'cetico.analise-riscos')")
    version: str = Field(..., description="Versão semântica (ex: '1.0.0')")
    area: ConselheiroArea = Field(..., description="Área de atuação do conselheiro")
    description: str = Field(..., description="Descrição curta do propósito do seam")
    
    # Contratos de entrada/saída (JSON Schema)
    input_schema: Dict[str, Any] = Field(..., description="Schema JSON da entrada esperada")
    output_schema: Dict[str, Any] = Field(..., description="Schema JSON da saída garantida")
    
    # Políticas de execução
    timeout_ms: int = Field(default=5000, ge=100, le=120000, description="Timeout em ms")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    
    # Controle de idempotência
    idempotency_key_template: str = Field(
        default="{mission_id}:{seam_name}",
        description="Template para chave de idempotência (usa mission_id e seam_name)"
    )
    
    # Metadados
    owner: str = Field(..., description="Responsável pelo seam (ex: 'equipe-governanca')")
    tags: list[str] = Field(default_factory=list, description="Tags para busca/filtro")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Valida semver (simplificado)."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Versão deve seguir semver (ex: '1.0.0')")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Versão deve conter apenas números separados por ponto")
        return v
    
    @field_validator('input_schema', 'output_schema')
    @classmethod
    def validate_json_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Valida que é um JSON Schema válido (básico)."""
        if not isinstance(v, dict):
            raise ValueError("Schema deve ser um objeto JSON")
        if 'type' not in v:
            raise ValueError("Schema deve ter campo 'type'")
        return v
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Retorna a Definition como JSON Schema para validação externa."""
        return self.model_dump(mode='json')
    
    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Valida entrada contra input_schema (básico)."""
        # TODO: implementar validação completa com jsonschema
        return True, None
    
    def validate_output(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Valida saída contra output_schema (básico)."""
        # TODO: implementar validação completa com jsonschema
        return True, None


class CapabilityRegistry:
    """Registry central de Capability Definitions.
    
    Carregado no boot do Executor Governado.
    Validado no preflight_check.py (gate).
    """
    
    def __init__(self):
        self._definitions: Dict[str, CapabilityDefinition] = {}
        self._providers: Dict[str, 'CapabilityProvider'] = {}
    
    def register(self, definition: CapabilityDefinition, provider: 'CapabilityProvider') -> None:
        """Registra uma Definition + Provider."""
        if definition.name in self._definitions:
            raise ValueError(f"Seam já registrado: {definition.name}")
        self._definitions[definition.name] = definition
        self._providers[definition.name] = provider
    
    def get_definition(self, name: str) -> Optional[CapabilityDefinition]:
        return self._definitions.get(name)
    
    def get_provider(self, name: str) -> Optional['CapabilityProvider']:
        return self._providers.get(name)
    
    def list_seams(self) -> list[CapabilityDefinition]:
        return list(self._definitions.values())
    
    def validate_all(self) -> list[str]:
        """Valida todas as definitions registradas.
        Retorna lista de erros (vazio se OK)."""
        errors = []
        for name, defn in self._definitions.items():
            provider = self._providers.get(name)
            if not provider:
                errors.append(f"Seam '{name}' sem provider registrado")
            # Validar schemas
            ok, err = definition.validate_input({})
            if not ok:
                errors.append(f"Seam '{name}' input_schema inválido: {err}")
        return errors
    
    def to_json(self) -> str:
        """Serializa registry para JSON (para persistência/debug)."""
        return json.dumps({
            name: defn.model_dump(mode='json') 
            for name, defn in self._definitions.items()
        }, ensure_ascii=False, indent=2)


# Instância global do registry
CAPABILITY_REGISTRY = CapabilityRegistry()