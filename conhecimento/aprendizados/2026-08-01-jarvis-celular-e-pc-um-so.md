# Jarvis do celular e do PC: um só cérebro (arquitetura sincronizada)

- **Data:** 01/08/2026
- **Sessão:** Verificação da sincronização entre o app Android e o opencode no PC

## Conclusão
**Não existem dois Járvis diferentes.** O app do celular (VoxUmGrau) não tem
inteligência própria — é um cliente de voz que conversa com o MESMO `opencode serve`
que roda no PC. Quando o usuário fala com o celular, quem responde é o mesmo
assistente que opera no computador.

## Como a sincronização acontece (arquitetura)
1. **Cérebro único:** app Android → WebSocket → `jarvis_bridge.py` (porta 8765) →
   `opencode serve` (porta 8767, com failover 8768). O app envia a fala, a ponte
   monta o prompt e chama a API `/session/{id}/message` do opencode.
2. **Sessão compartilhada:** a ponte reusa a mesma sessão "Jarvis"
   (`/session` com título "Jarvis") — o celular e o PC conversam na mesma linha
   de histórico.
3. **Personalidade única:** o prompt de sistema (`JARVIS_SYSTEM.md`, 28KB) é
   carregado do disco compartilhado. Mesmo prompt → mesma personalidade, tom,
   pronúncias (SSML) e regras.
4. **Conhecimento único:** o prompt referencia `CONHECIMENTO.md` (base exportada),
   as notas Obsidian (`conhecimento/notas/`, 293+ notas) e o catálogo de
   habilidades (`Habilidades/manifesto_geral.json`, 40 habilidades).
5. **Evolução compartilhada:** aprendizado registrado no PC (knowledge_graph.json,
   CONHECIMENTO.md, notas, regras, memória) é lido pelo celular na próxima
   mensagem — porque tudo vive no mesmo disco/volume.

## Implicação prática
- Ao evoluir (adicionar habilidade, corrigir bug, registrar decisão, atualizar
  regra, pronúncia), o celular automaticamente passa a saber, sem deploy.
- O que falta para "o mesmo em tudo" já é garantido pela arquitetura: mesmo
  cérebro + mesmo prompt + mesmo conhecimento + mesmo catálogo de habilidades.
- TTS/STT do celular são locais (SpeechRecognizer do Android), mas o raciocínio
  e o conhecimento são 100% do PC → unificados.

## Detalhes de implementação (para futuras melhorias)
- `PORTA_SERVE=8767` (env `OPENCODE_SERVE_PORT`), reserva 8768.
- Basic Auth: `opencode` + `OPENCODE_SERVER_PASSWORD` (em `scripts/.env`).
- `Cliente._get_session()` reusa sessão existente; cria "Jarvis" se não houver.
- `Cliente._ensure_serve()` inicia o serve automaticamente com limpeza de
  socket zumbi e failover de porta.
- Barge-in (interrupção de fala) agora suportado no PC (ESC/Enter/voz) —
  mesmo conceito da interrupção do app.
