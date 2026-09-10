# Relatório de Core Web Vitals — Ciclo 7 (bloco J)

Medição real com Playwright (Chromium) + PerformanceObserver, página servida por `server.py` do lab.
Atraso artificial de 500ms no asset hero (loopback não produz gargalo de rede natural).

## Medições (09/09/2026)

| Métrica | Antes | Depois (corrigida) | Threshold Good | Status |
|---|---|---|---|---|
| LCP | 844 ms | 408 ms | <= 2500 ms | Good |
| CLS | 0.127 | 0.000 | <= 0.1 | Good |
| INP | 0 ms (sem interação) | 16 ms | <= 200 ms | Good |

## Correções aplicadas

1. Imagem hero com `width`/`height` explícitos e `preload` — CLS 0.127 → 0.000, LCP 844 → 408ms.
2. `lang="pt-BR"`, `meta viewport`, h1 único, alt descritivo em todas as imagens.
3. Label associado via `for`/`id` no campo de email.
4. Contraste texto/fundo calculado >= 4.5 (AA).
5. Botão com texto visível e altura >= 24px, foco visível.

## Limitações

INP é medido intra-page (clique real no botão de newsletter), sem simulação de rede de campo. LCP/CLS dependem do atraso artificial do lab para serem mensuráveis em loopback — valores absolutos não representam campo, mas a comparação antes/depois é válida.

Fonte: `benchmarks/ciclo-7-cwv.json`