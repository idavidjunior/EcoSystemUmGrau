# 2026-09-10 - Ciclo 8 - Aprendizado: produto integrado com WS, sqlite e IA

**Categoria:** padrao
**Contexto:** Construção do Quadro de Notas com IA (produto integrado do Ciclo 8) e validação com teste de integração de 27 checks.
**Decisão:** Integrar as camadas dos ciclos 1-7 num único produto: HTTP sync (ThreadingHTTPServer / ADR-003), broadcast WS em thread asyncio própria (ADR-004), sqlite persistente (ADR-005), segurança OWASP via contrato do Ciclo 6 (ADR-006), IA via cognitive_core `/api/chat`, e CWV medido com Playwright (ADR-007).
**Impacto:** 27/27 checks passando; produto com CRUD real persistente, eventos em tempo real e chat IA. CWV Good (LCP 692ms, CLS 0.000, INP 0ms). Bloco N MASTERED.

## Lições-chave

1. **WebSocket precisa de escuta contínua antes das mutações** — cliente WS recebe apenas eventos emitidos depois de conectado. O primeiro teste falhou em 3 checks de broadcast porque o listener conectava após o POST; a correção foi iniciar um `WsListener` (thread própria acumulando eventos em lista) **antes** da mutação.
2. **Order de inicialização em threads** — `WsListener.__init__` iniciava a thread antes de setar `_duracao`, causando `AttributeError` silencioso dentro da thread e listener "morto". Atributos de instância devem ser definidos antes de `Thread.start()`.
3. **Bind de porta após reinício** — `ws_broadcast.parar()` deve aguardar a thread asyncio terminar (join) antes de liberar a porta; service em RESTART sem isso cai em `Errno 10048` (porta em uso). 
4. **Headers HTTP case-insensitive** — `http.client.HTTPMessage` retorna headers preservando o case original; asserts devem comparar via `.lower()`.
5. **Sanitização de XSS** — o padrão OWASP do Ciclo 6 escapou no *render* (frontend usa `textContent`/`escapeHtml`), não no armazenamento; o teste validou que a resposta API não quebra o contrato (201 com id), mantendo o dado cru no banco como o ciclo anterior fazia.

## Fonte

`conhecimento/web/labs/ciclo-8-produto-quadro-notas/` (produto + teste + medidor CWV)