# Jarvis do celular e do PC: um sÃ³ cÃ©rebro (arquitetura sincronizada)

- **Data:** 01/08/2026
- **SessÃ£o:** VerificaÃ§Ã£o da sincronizaÃ§Ã£o entre o app Android e o opencode no PC

## ConclusÃ£o
**NÃ£o existem dois JÃ¡rvis diferentes.** O app do celular (VoxUmGrau) nÃ£o tem
inteligÃªncia prÃ³pria â€” Ã© um cliente de voz que conversa com o MESMO `opencode serve`
que roda no PC. Quando o usuÃ¡rio fala com o celular, quem responde Ã© o mesmo
assistente que opera no computador.

## Como a sincronizaÃ§Ã£o acontece (arquitetura)
1. **CÃ©rebro Ãºnico:** app Android â†’ WebSocket â†’ `jarvis_bridge.py` (porta 8765) â†’
   `opencode serve` (porta 8767, com failover 8768). O app envia a fala, a ponte
   monta o prompt e chama a API `/session/{id}/message` do opencode.
2. **SessÃ£o compartilhada:** a ponte reusa a mesma sessÃ£o "Jarvis"
   (`/session` com tÃ­tulo "Jarvis") â€” o celular e o PC conversam na mesma linha
   de histÃ³rico.
3. **Personalidade Ãºnica:** o prompt de sistema (`JARVIS_SYSTEM.md`, 28KB) Ã©
   carregado do disco compartilhado. Mesmo prompt â†’ mesma personalidade, tom,
   pronÃºncias (SSML) e regras.
4. **Conhecimento Ãºnico:** o prompt referencia `CONHECIMENTO.md` (base exportada),
   as notas Obsidian (`conhecimento/notas/`, 293+ notas) e o catÃ¡logo de
   habilidades (`Habilidades/manifesto_geral.json`, 40 habilidades).
5. **EvoluÃ§Ã£o compartilhada:** aprendizado registrado no PC (knowledge_graph.json,
   CONHECIMENTO.md, notas, regras, memÃ³ria) Ã© lido pelo celular na prÃ³xima
   mensagem â€” porque tudo vive no mesmo disco/volume.

## ImplicaÃ§Ã£o prÃ¡tica
- Ao evoluir (adicionar habilidade, corrigir bug, registrar decisÃ£o, atualizar
  regra, pronÃºncia), o celular automaticamente passa a saber, sem deploy.
- O que falta para "o mesmo em tudo" jÃ¡ Ã© garantido pela arquitetura: mesmo
  cÃ©rebro + mesmo prompt + mesmo conhecimento + mesmo catÃ¡logo de habilidades.
- TTS/STT do celular sÃ£o locais (SpeechRecognizer do Android), mas o raciocÃ­nio
  e o conhecimento sÃ£o 100% do PC â†’ unificados.

## Detalhes de implementaÃ§Ã£o (para futuras melhorias)
- `PORTA_SERVE=8767` (env `OPENCODE_SERVE_PORT`), reserva 8768.
- Basic Auth: `opencode` + `OPENCODE_SERVER_PASSWORD` (em `scripts/.env`).
- `Cliente._get_session()` reusa sessÃ£o existente; cria "Jarvis" se nÃ£o houver.
- `Cliente._ensure_serve()` inicia o serve automaticamente com limpeza de
  socket zumbi e failover de porta.
- Barge-in (interrupÃ§Ã£o de fala) agora suportado no PC (ESC/Enter/voz) â€”
  mesmo conceito da interrupÃ§Ã£o do app.
