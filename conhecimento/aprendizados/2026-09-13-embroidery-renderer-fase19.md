---
tipo: erro
tags: [embroidery, renderer, fase-19, supersampling, underlay, threadcolor, testes]
data: 2026-09-13
contexto: FASE 19 — EmbroideryRenderer (src/simulation/embroidery_renderer.py). Suíte
  tests/test_embroidery_renderer.py com 12 testes, 7 falhando na 1ª rodada.
decisao: Corrigir a causa raiz da cor (kwargs do ThreadColor), o bug de supersampling
  (coordenadas × ss), o teto de escala com margem (shrink pós-cálculo) e o contrato do
  show_underlay=False (pular underlay, não desenhar opaco). Reescrever testes com
  objetos reais de 300mm e path de underlay detectável pela heurística.
impacto: Suite 12/12 PASSED; demo CLI gera imagem 406x366px correta.
---

# FASE 19 — Correção do EmbroideryRenderer (testes 12/12)

## Bugs encontrados

1. **Causa raiz da cor `(40,0,0)`** — NÃO era bug do renderer. A assinatura real de
   `ThreadColor` é `ThreadColor(name, brand='Generic', code='', r=0, g=0, b=0)`.
   `ThreadColor('teste', 200, 40, 40)` → `brand=200, code=40, r=40, g=0, b=0` →
   `rgb=(40,0,0)`. Corrigir chamadas para kwargs
   `ThreadColor('teste', r=r, g=g, b=b)`.

2. **Bug de supersampling** — em `_draw_segments`/`_draw_jumps` apenas a largura era
   multiplicada por `ss`; as coordenadas não. Com `ss=2` o desenho ocupava só o
   quadrante superior esquerdo e, após downscale, ficava comprimido pela metade.
   Correção: `cx = (pt.x * px_per_mm * s) + ox * s` (idem `cy`), com `s = self.ss`.

3. **Teto de escala com margem** — conteúdo = max_side/(1+2*0.08) ≈ 2068.97, mas o
   arredondamento duplo (w_px round + margin round) podia estourar 1-2px no canvas.
   Correção: shrink pós-cálculo
   `shrink = min(1.0, max_side / max(canvas_w, canvas_h))` e recomputa tudo.

4. **Contrato do `show_underlay=False`** — a lógica só calculava o split quando
   `show_underlay` era True; com False, `main_start=0` e o underlay era desenhado
   como main OPACO (invertendo o contrato "desligar underlay"). Correção: o split é
   sempre calculado quando `underlay_type != 'none'`; com `show_underlay=False` o
   main começa no split e as linhas de underlay são puladas.

## Heurística do joelho (estimate_underlay_split)

- `window = clamp(round(1/density), 5, 25)`; baseline = `median(lengths[:window])`.
- First stitch em `[window, half)` com `lengths[i] < baseline * 0.55` → joelho.
- Mapeia índice de stitch → índice de ponto contando somente comandos de desenho.
- `0` = sem underlay.

## Aprendizados de teste

- `recalculate_metadata()` achata `width_mm/height_mm` para o bbox REAL dos
  objetos → testes de escala precisam de objeto que ocupe 300mm de verdade
  (linha `(0,0)→(300,0)`, `bounds=(0,-5,300,5)`).
- Em `render_object` a origem é `(8 - bounds[0]*10, 8 - bounds[1]*10)` — para
  bounds y=-5, a origem vira y=58, não 8. Cálculo de pixel deve usar a origem real.
- O teste de underlay antigo era malformado: o "main" tinha passos de 40mm, então
  a heurística não detectava joelho → split=0 → imagens iguais. Path de teste:
  underlay com stitches longos (~10mm) + main com zigue-zague curto (~2mm).