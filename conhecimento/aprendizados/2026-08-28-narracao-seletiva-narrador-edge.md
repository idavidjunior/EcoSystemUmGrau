---
tipo: padrao
tags: [narrador, widget, audio, fala, selecao, relevancia, jarvis, tts]
data: 2026-08-28
contexto: "Usuario reclamou que o narrador fala sem parar e sem criterio. A causa era dupla: o filtro _deve_narrar do widget_edge.py tinha fallback 'conteudo' que narrava qualquer texto longo, e as clausulas de audio da Constituicao/AGENTS.md e do JARVIS_SYSTEM.md mandavam narrar 'o tempo todo' sem delimitar relevancia."
decisao: "Implementada narracao seletiva por relevancia. widget_edge.py: o passo 6 do _deve_narrar passou a retornar False com motivo 'sem relevancia' para texto sem sinal de conclusao, silenciando rotina. JARVIS_SYSTEM.md: adicionado item 7 a clausula de comunicacao em audio, determinando silencio quando nao ha evento relevante. Constituicao (00-system-rules.md): adicionado paragrafo 'Narracao seletiva por relevancia (28/08/2026)'; sincronizado via sync_rules.py update nas 3 camadas."
impacto: "Narrador fala apenas conclusoes, erros, resultados, bloqueios, descobertas e alertas. Validado com testes unitarios do _deve_narrar: 'processo' e 'rotina' silenciam; 'conclusao', 'erro' e 'resultado' narram. Preflight 100% passou."
---
# Narracao seletiva por relevancia no narrador Edge

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
  - "Pronto, instalado no celular com sucesso" → NARRA (conclusao)
  - "Achei um erro no build e corrigi" → NARRA (conclusao)
  - "Processando os arquivos de configuracao do projeto" → SILEN (sem relevancia)
  - "O teste passou, tudo sincronizado com o GitHub" → NARRA (conclusao)

## Coonections

- [[2026-08-13-parar-fala-corrida-flag]]
- [[oficializacao-narrador-edge-cerebro-vivo]]
- [[aprendizado-regra-de-fala-resumida-do-jarvis]]

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
- [[pronúncia-járvis-escrita-sem-acento-fala-com-acento]]