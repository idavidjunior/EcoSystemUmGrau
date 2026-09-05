---
tags: [chars, contem, continua, opencodeopencode, padrao, sinal]
aliases: [Narracao seletiva por relevancia no narrador Edge]
date: 2026-08-28
---

# Narracao seletiva por relevancia no narrador Edge

**Fonte:** opencode+opencode

O narrador (thread interna de scripts/widget_edge.py) e a voz do Jarvis (bridge via
JARVIS_SYSTEM.md) falam agora apenas eventos relevantes, silenciando conteudo comum.

## O que muda

1. `_deve_narrar` (widget_edge.py): o passo 6 deixou de ser fallback "conteudo" e
   passou a retornar `(False, "sem relevancia")` quando o texto nao contem sinal de
   conclusao/resultado/erro/importancia nas primeiras 200 chars.
2. `JARVIS_SYSTEM.md`: item 7 na clausula de comunicacao em audio determina silencio
   quando nao ha evento que valha a pena.
3. Constituicao → AGENTS.md → deployed: paragrafo "Narracao seletiva por relevancia
   (28/08/2026)" adicionado a CLAUSULA PETREA COMUNICACAO CONTINUA EM AUDIO.

## Validacao

- `python scripts/sync_rules.py update` → 24 regras sincronizadas, deployed ok.
- `python scripts/preflight_check.py` → TODOS TESTES PASSARAM.
- Teste manual do `_deve_narrar`:
  - "Vou compilar o app agora..." → SILEN (frase de processo)
  - "Pronto, instalado no celular com suce
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]