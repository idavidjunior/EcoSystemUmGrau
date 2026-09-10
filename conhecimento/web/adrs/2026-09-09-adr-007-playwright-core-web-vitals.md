# 2026-09-09 - Decisão de medição de Core Web Vitals — Playwright + PerformanceObserver (blocos J e D)

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema. O Ciclo 7 (Performance e acessibilidade, blocos J e D) precisa medir LCP/CLS/INP de uma página real e corrigir acessibilidade WCAG básica com evidência. Não há Lighthouse instalado e não queremos depender de ferramenta de build externa; o Playwright já é dependência declarada do roadmap (stack Jedi Python stdlib + playwright). Em loopback a rede local é rápida demais para produzir LCP/CLS mensuráveis.
**Projeto:** EcoSystemUmGrau

## Decisão

Medir Core Web Vitals com **Playwright (sync API)** + **PerformanceObserver** injetado via `add_init_script` antes de toda navegação. O servidor do lab aplica **atraso artificial de 500ms no asset hero** para que LCP e CLS sejam mensuráveis de forma determinística em loopback. A acessibilidade é validada por checagens DOM (lang, h1 único, alt, label for/id, contraste AA calculado via cor computada, botão clicável). Evidência salva em `benchmarks/ciclo-7-cwv.json`.

## Alternativas consideradas

1. **Alternativa A — Playwright + PerformanceObserver** — zero dependência nova (Playwright já está na stack), precisão de LCP/CLS/INP com observers nativos do navegador, gera JSON de evidência; atraso artificial no asset permite medir em loopback onde a rede real não produz gargalo. 18/18 checks passando.
2. **Alternativa B — Lighthouse via npx/CLI** — métricas "field-like", porém adiciona dependência Node/npx que o ecossistema não possui de forma confiável (Ciclos B/C bloqueados justamente pela ausência de Node); não usa a stack já validada.
3. **Alternativa C — Medir apenas com timing de fetch** — simula pouco do que o usuário percebe; sem observador de layout-shift/LCP não há evidência de CLS/INP.

## Por quê

O Ciclo 7 entregou evidência real: 18/18 checks passando. A versão corrigida baixou CLS de 0.127 para 0.000 (imagem com `width`/`height` explícitos + `preload`), LCP de 764ms para 528ms e INP de 0 (sem interação) para 48ms (banda Good < 200ms). Acessibilidade WCAG básica validada (lang, h1 único, alt descritivo, label for/id, contraste AA ≥ 4.5, botão com texto e ≥ 24px). Pelo princípio da mudança mínima segura, mantém-se a stack existente (Playwright) sem adicionar Node/Lighthouse. O `inp` é medido intra-page com clique real no botão; LCP/CLS dependem do atraso artificial do lab, limitação documentada.