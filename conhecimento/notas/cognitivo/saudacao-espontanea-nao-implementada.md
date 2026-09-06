---
tags: [cognitivo, falhas, general, memória, pendências, reconectava]
aliases: [saudacao espontanea nao implementada]
date: 2026-08-23
---

# saudacao espontanea nao implementada

**Dominio:** general

---
tipo: erro
tags: [saudacao, autoapresentacao, clausula-petrea, boot, primeira-mensagem]
data: 2026-08-23
contexto: "Cláusula pétrea de autoapresentação automática na primeira mensagem de cada sessão (AGENTS.md e Constituição) exige saudação curta (máx 3-4 linhas), espontânea, variando o tom a cada sessão, informando que EcoSystemUmGrau está ativo e operante, com leve contexto (projeto ativo, memória, pendências)."
decisao: "Registrar erro e definir implementação: criar mecanismo de detecção 

---
tipo: erro
tags: [voxumgrau, heartbeat, grace-period, websocket, meia-morte]
data: 2026-09-05
contexto: Correção da "meia-morte" do VoxUmGrau — reconexão em loop porque a bridge fica ~45s em setup sequencial (saudação LLM/TTS) sem ler o socket, e o app contava 3 falhas de pong e reconectava.
decisao: O grace period de 90s do heartbeat é uma janela FIXA desde conectar(). NUNCA zerar gracePeriodAteMs ao receber o primeiro pong — a bridge responde o ping inicial (via prim) e depois mergulha no 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]