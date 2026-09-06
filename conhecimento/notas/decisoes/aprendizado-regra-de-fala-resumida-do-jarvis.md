---
tags: [decisao, encontrados, finais, implementando, opencode, problemas]
aliases: [Aprendizado: Regra de fala resumida do Jarvis]
date: 2026-08-20
---

# Aprendizado: Regra de fala resumida do Jarvis

**Fonte:** opencode

---
tipo: decisao
tags: [jarvis, voz, tts, fala, resumo, narracao, regra]
data: 2026-08-19
contexto: "Usuário David determinou que o Jarvis estava dando detalhes longos demais na fala, deixando o áudio muito comprido. Ele quer que o Jarvis narre apenas um resumo bem simples e curto do que está fazendo, do que está implementando e dos problemas encontrados, dando detalhes somente quando pedido."
decisao: "Criada a Cláusula Pétrea — Fala Resumida no scripts/JARVIS_SYSTEM.md (restaurado do backup de 03/08/2026, que estava ausente e o bridge caía no fallback genérico). Regra: narrar em 1 a 3 frases curtas; nunca detalhes longos, listas, nomes de arquivos em sequência nem etapas técnicas extensas em áudio; detalhes só quando o usuário pedir explicitamente. O JARVIS_SYSTEM.md foi restaurado completo (atualizado com unified_bridge.py, narrador_desktop.py e projetos irmãos atuais) e a nova cláusula foi adicionada no topo."
impacto: "O Jarvis passa a falar apenas resumos curtos e simples, reduzindo drasticamente o tamanho do áudio nas narrações contínuas e nos resumos finais. O system prompt do bridge volta a ser rico (saiu do fallback genérico)."
---

# Aprendizado: Regra de fala resumida do Jarvis

## Resumo

O Jarvis deve narrar em áudio apenas resumos simples e curtos do que está
fazendo. Detalhes somente quando o usuário pedir.

## Descobertas técnicas

- O system prompt do Jarvis vive em `scripts/JARVIS_SYSTEM.md`, carregado pelo
  `jarvis_bridge.py` (linha 109, `SYS_PATH`) com fallback genérico quando
  ausente.
- O arquivo tinha sido removido de `scripts/` e só existia no backup de
  `backups/backup_20260803_212542/scripts/JARVIS_SYSTEM.md`. A bridge caía no
  fallback "Você é Jarvis, especialista no EcoSystemUmGrau e OpenCode", perdendo
  todas as regras de voz, pronúncia, gramática e TV.
- Restaurado o arquivo completo e adicionada a nova cláusula no topo.

## Regra permanente (19/08/2026)

1. Narrar em 1 a 3 frases curtas o que vai fazer, o que está fazendo ou o que
   encontrou.
2. Nunca falar detalhes longos, listas, etapas intermediárias, nomes de
   arquivos em sequência ou explicações técnicas extensas em áudio.
3. Detalhes só quando o usuário pedir explicitamente.
4. Vale para narração contínua, feedback de progresso e resumo final.
5. Regra imutável, a pedido do usuário David.

## Como usar

- `scripts/JARVIS_SYSTEM.md` é a fonte das regras de voz do Jarvis (bridge).
- Qualquer mudança futura de comportamento de fala deve ser registrada lá e na
  memória (`memory_engine.py add`). // ---
tipo: decisao
tags: [jarvis, voz, tts, fala, resumo, narracao, regra]
data: 2026-08-19
contexto: "Usuário David determinou que o Jarvis estava dando detalhes longos demais na fala, deixando o áudio muito comprido. Ele quer que o Jarvis narre apenas um resumo bem simples e curto do que está fazendo, do que está implementando e dos problemas encontrados, dando detalhes somente quando pedido."
decisao: "Criada a Cláusula Pétrea — Fala Resumida no scripts/JARVIS_SYSTEM.md (restaurado do backup de 03/08/2026, que estava ausente e o bridge caía no fallback genérico). Regra: narrar em 1 a 3 frases curtas; nunca detalhes longos, listas, nomes de arquivos em sequência nem etapas técnicas extensas em áudio; detalhes só quando o usuário pedir explicitamente. O JARVIS_SYSTEM.md foi restaurado completo (atualizado com unified_bridge.py, narrador_desktop.py e projetos irmãos atuais) e a nova cláusula foi adicionada no topo."
impacto: "O Jarvis passa a falar apenas resumos curtos e simples, reduzindo drasticamente o tamanho do áudio nas narrações contínuas e nos resumos finais. O system prompt do bridge volta a ser rico (saiu do fallback genérico)."
---

# Aprendizado: Regra de fala resumida do Jarvis

## Resumo

O Jarvis deve narrar em áudio apenas resumos simples e curtos do que está
fazendo. Detalhes somente quando o usuário pedir.

## Descobertas técnicas

- O system prompt do Jarvis vive em `scripts/JARVIS_SYSTEM.md`, carregado pelo
  `jarvis_bridge.py` (linha 109, `SYS_PATH`) com fallback genérico quando
  ausente.
- O arquivo tinha sido removido de `scripts/` e só existia no backup de
  `backups/backup_20260803_212542/scripts/JARVIS_SYSTEM.md`. A bridge caía no
  fallback "Você é Jarvis, especialista no EcoSystemUmGrau e OpenCode", perdendo
  todas as regras de voz, pronúncia, gramática e TV.
- Restaurado o arquivo completo e adicionada a nova cláusula no topo.

## Regra permanente (19/08/2026)

1. Narrar em 1 a 3 frases curtas o que vai fazer, o que está fazendo ou o que
   encontrou.
2. Nunca falar detalhes longos, listas, etapas intermediárias, nomes de
   arquivos em sequência ou explicações técnicas extensas em áudio.
3. Detalhes só quando o usuário pedir explicitamente.
4. Vale para narração contínua, feedback de progresso e resumo final.
5. Regra imutável, a pedido do usuário David.

## Como usar

- `scripts/JARVIS_SYSTEM.md` é a fonte das regras de voz do Jarvis (bridge).
- Qualquer mudança futura de comportamento de fala deve ser registrada lá e na
  memória (`memory_engine.py add`).

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]