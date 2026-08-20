---
tipo: padrao
tags: [etapa24, interface, jarvis, ui, state-management, event-bus, bridge-integration, dedup, reconnection, terminal-renderer]
data: 2026-08-18
contexto: Implementação da Etapa 24 — Interface do Jarvis no EcoSystemUmGrau
decisao: Criar camada de apresentação em jarvis_interface.py: UIState (singleton central, thread-safe, snapshot-based), EventBus (wildcard support), Message model (5 roles com factory methods), MessageDeduplicator (content-based MD5 hash, 300s window), Presenters (backend→UI format com error_for_user separando user_message de technical), BridgeIntegration (processa protocolo WebSocket existente do jarvis_bridge.py), TerminalRenderer (texto), ReconnectionHandler (exponential backoff), UIRouter (10 tipos de evento backend→UI). 132 testes adversariais. Nenhum módulo existente alterado. Bug encontrado: reset() não limpava messages e dedup usava UUID em vez de content hash.
impacto: A interface agora é uma camada separada do cérebro. UIState é a fonte confiável de estado. BridgeIntegration processa mensagens do WebSocket existente sem duplicar infraestrutura. MessageDeduplicator garante idempotência visual. ReconnectionHandler evita reconexão infinita com backoff. A separação permite evoluir UI sem afetar core.
```

## Aprendizado

1. **UI não é o cérebro**: a interface apenas recebe eventos, apresenta estado, envia intenção e recebe resultado. Nunca mover lógica de negócio para a UI. cognitive_core, mission_loop, memory, permissions ficam no backend.

2. **Singleton + reset() é perigoso**: UIState como singleton é conveniente para acesso global, mas exige que reset() limpe TODOS os campos (incluindo messages e _seen_ids). Esquecer um campo causa contaminação entre testes/uses.

3. **Content-based dedup > ID-based dedup**: quando o produtor cria IDs novos a cada chamada (UUID), a dedup por ID não funciona. Content hash (MD5 do conteúdo) é mais robusto para mensagens de texto.

4. **Snapshot-based views previnem race conditions**: get_full_view() retorna cópia do estado, não referência. Isso permite que a UI leia estado sem lock, enquanto o backend escreve com lock.

5. **Error separation é essencial**: Presenters.error_for_user() separa user_message (compreensível) de technical (para diagnóstico). Nunca mostrar traceback completo ao usuário.

6. **Exponential backoff com jitter para reconexão**: ReconnectionHandler usa base_delay × 2^attempt com max_delay. Isso evita reconexão imediata (thundering herd) e reconexão infinita (max_attempts).

7. **EventBus com wildcard permite monitoring**: registrar listener em '*' captura todos os eventos sem modificar cada emissor. Útil para logging, debugging e observabilidade.

8. **Protocolo existente deve ser respeitado**: BridgeIntegration adapta ao protocolo JSON do jarvis_bridge.py (tipo/texto/id para Android, type/text para EcoDashboard) em vez de criar novo protocolo.

## Conexões

- [[2026-08-18-etapa23-observability-reliability]]
- [[2026-08-18-etapa22-self-assessment-self-improvement]]
