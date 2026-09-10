---
tipo: decisao
tags: [web, performance, acessibilidade, core-web-vitals, playwright, wcag]
data: 2026-09-09
contexto: Ciclo 7 da trilha de engenharia web — medir CWV de página real e corrigir acessibilidade (blocos J e D).
decisao: Medir LCP/CLS/INP com Playwright sync + PerformanceObserver injetado via add_init_script; atraso artificial (0.5s) no asset hero do servidor permite medir LCP/CLS mensuráveis em loopback; página corrigida usa lang, h1 único, alt descritivo, label for/id, contraste AA e botão com texto/tamanho clicável.
impacto: 18/18 checks OK. Correções: CLS 0.127 -> 0.000, LCP 764ms -> 528ms, INP 48ms (Good). Blocos J e D passaram de DISCOVERED para VALIDATED/3 com evidência em labs/ciclo-7-performance-acessibilidade.
limite: INP é intra-page (clique real em botão), não simula rede real de campo; LCP/CLS dependem do atraso artificial do lab.