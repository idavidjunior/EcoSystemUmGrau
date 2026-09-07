---
tipo: episodio
tags: [sandbox, docker, spec, seguranca, isolamento]
data: 2026-09-07
contexto: pedido de spec para sandbox isolado com Docker como base segura
decisao: spec proposta em specs/eco-sandbox-docker.spec.md com Docker preferencial e degradado sem Docker
impacto: base pronta para implementar scripts/eco_sandbox.py com reuso do security_engine
---

O Docker não está instalado neste host Windows.
O código de agentes hoje roda via subprocesso direto no host.
O security_engine já tem SandboxConfig e validação útil.
O padrão multi-stage com não-root existe em TradingAgents.
A spec nova define execução isolada com rede desligada padrão.
Ela prevê modo degradado quando Docker está ausente.
