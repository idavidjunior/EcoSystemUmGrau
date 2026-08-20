---
tipo: padrao
tags: [widget, jarvis, ui, features]
data: 2026-08-20
---

# Widget Jarvis - 8 Features Implementadas

## Decisao
Adicionar 8 funcionalidades ao widget flutuante Jarvis para aumentar visibilidade e controle.

## Features
1. **Indicador de conexao** - 3 dots (Narrador, TTS, Bridge) com heartbeat visual
2. **Barra de volume TTS** - Slider 0-100, persistido em widget_state.json
3. **Timer de sono** - Select com 5/15/30/60/120 min, desliga voz automaticamente
4. **Mini painel de tarefas** - Mostra pending tasks de state.json (max 5)
5. **Stats do Model Monitor** - Chip com modelo + custo acumulado
6. **Log de erros** - Toast vermelho flutuante com erros recentes dos logs
7. **Animacao de thinking** - Botao Mic pulsa quando ativo (CSS pulse)
8. **Toggle de tema** - Dark/Neon/Calm, persistido em widget_state.json

## Arquivos alterados
- widget_controle_jarvis.py: 912 -> 1207 linhas
- frases_manager.py: adicionado frases_sleep
- widget_controle.html: atualizado
- widget_unified.html: atualizado

## Impacto
Widget ganha visibilidade completa do ecossistema em uma unica janela flutuante.
