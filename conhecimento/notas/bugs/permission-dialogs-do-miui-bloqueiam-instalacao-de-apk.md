---
tags: [bug, treinamentonavegacao]
aliases: [Permission dialogs do MIUI bloqueiam instalacao de APK]
date: 2026-07-29
---

# Bug: Permission dialogs do MIUI bloqueiam instalacao de APK

**Projeto:** treinamento_navegacao

## Causa Raiz
MIUI/HyperOS adiciona dialogs de permissao apos instalacao que nao existem no Android AOSP

## Correcao
Apos adb install, aguardar 3s e aceitar dialog com adb shell input tap com coordenadas do botao 'Permitir'; se falhar, tentar 'Permitir somente durante o uso'
