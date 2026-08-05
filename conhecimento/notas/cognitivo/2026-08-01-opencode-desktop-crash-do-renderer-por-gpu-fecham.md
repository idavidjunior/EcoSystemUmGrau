---
tags: [cognitivo, desugardebugfiledependencies, etapa, general, minutos, slowness]
aliases: [﻿# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU ]
date: 2026-08-05
---

# ﻿# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

**Dominio:** general

﻿# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

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
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]