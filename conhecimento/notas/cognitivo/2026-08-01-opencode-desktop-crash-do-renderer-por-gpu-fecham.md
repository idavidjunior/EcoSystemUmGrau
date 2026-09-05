---
tags: [cognitivo, desugardebugfiledependencies, etapa, general, minutos, slowness]
aliases: [# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU +]
date: 2026-08-01
---

# # 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memória

**Dominio:** general

# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memória

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

Investigação exaustiva do ciclo 

---
tipo: erro
tags: [android, gradle, ram, build, performance, xmx, tail-scale, adb]
data: 2026-08-03
fonte: tarefa
contexto: Build do projeto VoxUmGrau (Android, Kotlin/Compose) travava no gradlew assembleDebug — processo era morto pelo timeout do shell tool (>10 minutos) na etapa desugarDebugFileDependencies.
decisao: Diagnosticada falta de memória RAM (máquina com 4GB total / apenas 256MB livres) combinada com Gradle daemon configurado com -Xmx2048m, causando thrashing de memória e slowness 


## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]