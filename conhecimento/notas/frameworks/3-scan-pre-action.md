---
tags: [completo, evitar, evitaveis, falhas, framework]
aliases: [3-Scan Pre-Action]
date: 2026-08-12
---

# 3-Scan Pre-Action

Protocolo de 3 scans antes de cada acao para garantir contexto completo e evitar falhas evitaveis

Scan 1 (Estrutura): arvore de elementos, DOM, hierarquia de janelas. Scan 2 (Estado): modais abertos, loadings, notificacoes, teclado visivel. Scan 3 (Alvo): elemento especifico, visibilidade, habilitado, nao obsoleto. So agir apos os 3 scans. 200ms total para os 3 scans em interfaces simples, 800ms em complexas
## Conexoes

- [[cluster-hub-navegacao]]
- [[framework-hub-frameworks]]