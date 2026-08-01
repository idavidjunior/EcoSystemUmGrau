---
tags: [framework]
aliases: [OODA-Nav]
date: 2026-08-01
---

# OODA-Nav

Adaptacao do ciclo Observe-Orient-Decide-Act de Boyd para navegacao automatizada. Ciclo completo <3s. Repetir a cada interacao

Observe (0.5s): scan da tela, identificar elementos visiveis, estado atual, modais. Orient (0.5s): reconhecer framework, padroes de layout, estrutura familiar. Decide (0.3s): escolher metodo de interacao, seletor, fallback chain. Act (1-3s): executar interacao, esperar resposta, verificar resultado. Feedback loop: se Act falhou, voltar para Observe e recomecar
