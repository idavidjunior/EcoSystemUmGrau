---
tipo: padrao
tags: [runtime, kernel, constituicao, governanca, arquitetura]
data: 2026-08-05
contexto: Transformar o Ecossistema Jarvis em Runtime de IA persistente. Camada 2: Kernel permanente + Constituicao imutavel.
decisao: Adicionar clausula de soberania (v1.1) a Constituicao e criar scripts/runtime_kernel.py como autoridade maxima com contratos e pipeline.
impacto: Toda resposta passa pelo Kernel. Nenhuma conversa e sessao isolada.
---

# Runtime Persistente — Camada 2: Kernel + Constituicao (2026-08-05)

## Contexto
Camada 1 (estado + bootloader) pronta. Agora o Kernel como autoridade máxima:
controla regras, prioridades, contratos, formatos, sequência e autorização.

## Decisão de Arquitetura
- **Constituição v1.1** (`config/agents/00-system-rules.md`): nova cláusula
  "CLÁUSULA PÉTREA — SOBERANIA DO RUNTIME E DO KERNEL" com 7 regras absolutas:
  nunca ignorar Kernel/Runtime, sempre consultar memória, sempre validar,
  nunca responder sem auditoria, nunca contrariar decisão consolidada sem
  justificativa, nenhuma conversa é sessão isolada.
- **`scripts/runtime_kernel.py`**: Kernel permanente. Carrega as regras
  absolutas da Constituição (parse regex da cláusula pétrea), define o pipeline
  obrigatório de 9 etapas (Boot → Kernel → Memory → Context → Conselho* →
  LER* → Validador → Auditor → Resposta), contratos de entrada (7 campos) e
  saída (5 campos), e `validate_output()`/`authorize_response()` com checagens
  heurísticas contra as regras.
- **Bootloader** integrado: `runtime_boot.py` agora exibe as regras do Kernel
  no relatório de boot.
- **Maestro** atualizado: passo 1 obrigatório = enquadrar no Kernel
  (`contrato-entrada`) e autorizar resposta (`check`) antes de entregar.
- **Sync 3 camadas**: `sync_rules.py update` regenera AGENTS.md; a camada 3
  (Constituição deployada em ~/.config/opencode/agents/) precisa ser copiada
  manualmente (o sync não redeploya) — cópia manual feita.

## Validação
- Kernel carrega 7 regras da Constituição. `check` reprova resposta sem
  validação/justificativa (exit 1) e aprova resposta conforme (exit 0).
- `sync_rules.py check`: 3 camadas consistentes.
- `preflight_check.py`: TODOS TESTES PASSARAM.

## Lição
- O `sync_rules.py update` NÃO redeploya a Constituição para
  `~/.config/opencode/agents/`. Após editar a fonte, copiar manualmente:
  `Copy-Item config/agents/00-system-rules.md ~/.config/opencode/agents/` — senão
  o preflight bloqueia a alteração.

## Próximos passos (camada 3)
- Context Loader inteligente (selecionar docs/memórias relevantes por assunto)
- Auditor adaptativo (somente tarefas de alta criticidade)
- (Registradas como pendências no runtime state)

## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]