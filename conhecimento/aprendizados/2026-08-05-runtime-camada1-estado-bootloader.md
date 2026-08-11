---
tipo: padrao
tags: [runtime, bootloader, estado-persistente, continuidade, arquitetura]
data: 2026-08-05
contexto: Transformar o Ecossistema Jarvis em Runtime de IA persistente. Camada 1: estado persistente + bootloader + restauracao automatica.
decisao: Criar scripts/runtime_state.py (estado em runtime/state.json) e scripts/runtime_boot.py (bootloader). Boot obrigatorio integrado ao AGENTS.md e ao Maestro.
impacto: Nenhuma conversa e sessao isolada. Toda sessao restaura o estado do Runtime antes de processar.
---

# Runtime Persistente — Camada 1: Estado + Bootloader (2026-08-05)

## Contexto
O Ecossistema Jarvis deve virar um Runtime de IA persistente onde a LLM é só o
motor de inferência. Governança, memória, regras e continuidade pertencem ao
ecossistema. Camada 1 = estado persistente + boot automático em toda sessão.

## Decisão de Arquitetura
- **`scripts/runtime_state.py`** — estado persistente em `runtime/state.json`:
  projeto ativo, objetivo atual, última tarefa, contexto operacional, agentes
  ativos, memória carregada, pendências, checkpoints, histórico resumido.
  CLI: `status | set | add-agent | drop-agent | pending | checkpoint | restore |
  list | note | reset`. Checkpoints em `runtime/checkpoints/` (máx 30).
- **`scripts/runtime_boot.py`** — Bootloader: verifica integridade (Constituição,
  AGENTS.md, memória, dirs, imports), restaura estado, carrega memória relevante
  (top 5) + preferências via memory_engine, emite relatório de boot e ativa modo
  operacional. Flags: `--status`, `--check`, `--report`.
- **AGENTS.md** — bloco "RUNTIME PERSISTENTE — BOOT OBRIGATÓRIO" (fora do bloco
  gerado por sync_rules): todo agente DEVE rodar `runtime_boot.py` antes de
  processar, ler o relatório, salvar checkpoint em tarefas importantes e
  atualizar `last_task`/`note`.
- **00-maestro.md** — passo 0 obrigatório: executar boot antes de classificar.

## Detalhes técnicos
- Estado usa escrita atômica (`tmp` + `os.replace`) para evitar corrupção.
- Checkpoint guarda cópia do estado inteiro; restore sobrescreve o atual.
- Limite de 30 checkpoints com cleanup automático.
- Integridade do boot: falha em qualquer item = exit 1 (mas ainda mostra estado).

## Lição
- Bootloader precisa criar os diretórios (`_ensure_dirs`) ANTES de verificar
  integridade — na 1ª execução os paths não existiam e o check falhava.

## Próximos passos (camada 2)
- Kernel permanente (autoridade máxima: regras, prioridades, formatos, validação)
- Constituição imutável com cláusulas absolutas
- (Registradas como pendências no runtime state)

## Conexoes

- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]