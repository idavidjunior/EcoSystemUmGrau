---
tags: [cognitivo, system_design]
aliases: [Estrategia de loop autonomo: planejar-executar-verificar-corrigir]
date: 2026-08-01
---

# Estrategia de loop autonomo: planejar-executar-verificar-corrigir

**Dominio:** system_design

Qualquer sistema autonomo segue um ciclo fechado: (1) Planejar: decompor objetivo em passos verificaveis. (2) Executar: rodar cada passo com ferramentas reais. (3) Verificar: validar saida contra criterios objetivos (git diff, test pass, compilacao). (4) Corrigir: se falhou, registrar causa, replanejar, tentar de novo. O loop termina apenas quando TODOS os criterios de sucesso sao atingidos. Nao use max_iterations como criterio de parada — use deteccao de estagnacao (nenhum progresso em N iteracoes).
