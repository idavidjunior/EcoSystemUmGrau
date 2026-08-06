---
tags: [botao, bug, coordenadas, input, tap, treinamentonavegacao]
aliases: [Permission dialogs do MIUI bloqueiam instalacao de APK]
date: 2026-08-06
---

# Permission dialogs do MIUI bloqueiam instalacao de APK

**Projeto:** treinamento_navegacao

## Causa Raiz
MIUI/HyperOS adiciona dialogs de permissao apos instalacao que nao existem no Android AOSP

## Correcao
Apos adb install, aguardar 3s e aceitar dialog com adb shell input tap com coordenadas do botao 'Permitir'; se falhar, tentar 'Permitir somente durante o uso'
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-navegacao]]
- [[css-selector-priority-ladder]]
- [[dom-element-hierarchy-mapping]]
- [[iframecontenteditable-text-entry]]
- [[spa-navigation-detection]]