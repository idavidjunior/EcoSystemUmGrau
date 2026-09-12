---
tags: [agente, comando, grafo, widget]
aliases: [EcoW]
date: 2026-09-12
---

# ecow — Widget Cérebro Vivo (Grafo 3D)

**Categoria:** agentes
**Fonte:** config/agents/ecow.md

## Papel

Abre o widget Cerebro Vivo (grafo 3D do conhecimento em tempo real) e traz a janela para frente se já estiver aberto.

## Gatilho

`@ecow` ou `/ecow`

## Responsabilidades

- Executar `scripts/ecow.bat` (pythonw widget_grafo.py)
- Aguardar 3s e verificar processo "Cerebro Vivo"
- Confirmar abertura ou foco da janela existente
- Fallback: sugerir `python scripts/widget_grafo.py` manual

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[widget-grafo]] — widget grafo 3D
- [[cerebro-vivo]] — cérebro vivo
- [[clausula-ecow]] — cláusula pétrea
- [[grafo-3d-conhecimento]] — grafo 3D