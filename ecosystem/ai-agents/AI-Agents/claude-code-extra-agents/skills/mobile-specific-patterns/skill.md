---
name: mobile-specific-patterns
description: |
  Padrões mobile (iOS/Android/React Native/Flutter): ciclo de app, bateria, rede instável e UX nativa.
  Trigger phrases: "mobile patterns", "react native", "flutter", "ios", "android"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Mobile-Specific Patterns — Produto Bom no Mundo Real

## Objetivo
Projetar apps móveis resilientes a rede ruim, limitações de dispositivo e ciclos de vida agressivos.

## Considerações críticas
- App lifecycle (foreground/background/terminated)
- Consumo de bateria e uso de CPU
- Armazenamento local seguro
- Variabilidade de conexão

## Padrões recomendados
- Offline queue para ações essenciais
- Sync incremental em background com limites
- Permissões pedidas no contexto de uso
- Feature flags por plataforma/versão

## Qualidade de UX
- First render rápido
- Estados de vazio/loading/erro claros
- Recuperação após perda de rede
- Acessibilidade nativa (fonte dinâmica, leitor de tela)

## Checklist técnico
- Crash reporting por versão de app?
- Deep links cobertos por testes?
- Push notifications idempotentes?
- Compatibilidade com versões mínimas suportadas?

## Anti-patterns
- Assumir rede estável sempre
- Sincronização agressiva drenando bateria
- UI inconsistente com padrões da plataforma
- Armazenar segredo em plaintext

## Saída esperada do agente
- Arquitetura mobile por camada
- Estratégia offline/sync
- Lista de riscos por plataforma
- Plano de testes em dispositivos reais