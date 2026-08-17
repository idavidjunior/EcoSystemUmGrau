---
tags: [cognitivo, config, desugardebugfiledependencies, etapa, general, unificada]
aliases: [# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU +]
date: 2026-08-17
---

# # 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

**Dominio:** general

# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

InvestigaÃ§Ã£o exaustiva do ciclo 

---
tipo: erro
tags: [android, gradle, ram, build, performance, xmx, tail-scale, adb]
data: 2026-08-03
fonte: tarefa
contexto: Build do projeto VoxUmGrau (Android, Kotlin/Compose) travava no gradlew assembleDebug — processo era morto pelo timeout do shell tool (>10 minutos) na etapa desugarDebugFileDependencies.
decisao: Diagnosticada falta de memória RAM (máquina com 4GB total / apenas 256MB livres) combinada com Gradle daemon configurado com -Xmx2048m, causando thrashing de memória e slowness 

---
tipo: aprendizado
tags: [vis-network, uso-real, mtime, atividade, tamanho, pythonw, windows, processo-gui]
data: 2026-08-04
contexto: Implementar "tamanho por uso real" no grafo do conhecimento (nós quentes vs frios) e corrigir terminal python abrindo junto ao widget.
decisao: (1) Metrica de atividade: usar o mtime do arquivo .md de cada nota como proxy de uso real. atv = max(0, min(1, 1 - dias/90)), clamped em 0.12 (nunca some). Guardado em n['atv'] e injetado no node JS. (2) size combina g

---
tipo: aprendizado
tags: [widget, labels, etiquetas, menus, localStorage, persistencia, pywebview, vis-network]
data: 2026-08-04
contexto: Usuario pediu: (1) etiquetas (labels) DESATIVADAS por padrao, ativadas pelo botao 'T'; (2) ocultar os menus (barra de legendas + painel lateral) com um clique persistindo a escolha.
decisao: (1) Inverter semantica de labelsOcultos: oculto e o PADRAO. Regra: oculto = localStorage.getItem('labelsOcultos') !== 'false'. Ou seja: ausente, 'true' ou qualquer out

---
tipo: erro
tags: [grafo, widget, pywebview, bug, teste, harness, node, vis-network, tdz]
data: 2026-08-06
contexto: Varredura + correção um-a-um de todos os bugs do widget grafo desktop (Cerebro Vivo), seguida de teste completo via harness headless Node.
decisao: Corrigir 8 bugs e validar com harness Node que executa os blocos JS reais do HTML gerado (stubs de DOM/vis/localStorage/bridge), mais subprocesso do widget real.
impacto: Painel de controles voltou a funcionar (tema, velocidade, orb

﻿# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

InvestigaÃ§Ã£o exaustiva do ciclo 

# 2026-08-16: MicrofoneManager — device WDM-KS int16 e referências por import

**Categoria:** erro
**Contexto:** Implementação dos 8 passos de evolução do microfone do JARVIS (device persistente, hot-plug, wake word, streaming STT, enhancement, bridge, health check, config unificada) no EcoSystemUmGrau.

## Problema 1: float32 corrompe no driver WDM-KS

O device 11 (Microfone Realtek HD Audio Mic input, hostapi WDM-KS) entrega dados corrompidos (RMS ~1e18, NaN) quando capturado com dtype float32
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]