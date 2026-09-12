---
tags: [agente, comando, celular, scrcpy]
aliases: [EcoCell]
date: 2026-09-12
---

# ecocell — Espelho de Celular via scrcpy

**Categoria:** agentes
**Fonte:** config/agents/ecocell.md

## Papel

Abre espelho de tela do celular via scrcpy (daemon com reconexão automática, fallback encoding, screenrecord+ffplay).

## Gatilho

`@ecocell` ou `/ecocell`

## Responsabilidades

- Iniciar `scrcpy_daemon.py --once` em background
- Aguardar 3s e verificar log
- Confirmar "Device alvo" sem erro
- Reportar erro se ADV falhar

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[scrcpy-daemon]] — daemon scrcpy
- [[adb-perito]] — skill ADB
- [[android-diagnostics]] — diagnóstico Android
- [[clausula-ecocell]] — cláusula pétrea