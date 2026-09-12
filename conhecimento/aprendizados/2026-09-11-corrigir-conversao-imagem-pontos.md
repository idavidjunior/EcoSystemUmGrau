---
tipo: erro
tags: [conversor-bordado, embroidery-engine, digitizer-pipeline, coordenadas, conversao-mm-px, editor]
data: 2026-09-11
contexto: Usuário relatou que "a imagem não está sendo convertida em pontos". O fluxo desejado é: carregar imagem → converter em pontos → editar os pontos.
decisao: Corrigir a conversão de coordenadas mm→px (o pipeline centraliza no canvas, então é preciso mapear a bbox do design de volta ao espaço da imagem) e corrigir a renderização no editor (refresh_canvas retornava cedo sem binding <Configure>).
impacto: Imagem agora é convertida em pontos reais distribuídos corretamente pela imagem; editor renderiza os pontos e permite centralizar (Ctrl+M), duplicar, mover com setas.
---

## Bug raiz (imagem não virava pontos)
O `DigitizerPipeline.digitize` centraliza o design no canvas de 200mm. Isso significa que os contornos do `EmbroideryObject` estão em coordenadas mm **centradas na origem** (ex.: bbox `-12.1 a +12.1`) e o eixo Y cresce para cima.

O `motor_bordado.digitizar` multiplicava essas coords por `scale_px = 1/scale_mm` assumindo que eram coords absolutas da imagem. Isso gerava:
- Coordenadas negativas → máscara cortada no canto (0,0)
- Bounds todos `(0,0,...)` com tamanhos pequenos e inconsistentes
- Pontos fora da imagem / não visíveis

### Correção: `_build_transform(design, img_w, img_h)`
- Computa a bbox total do design em mm
- Escala para caber na imagem preservando proporção (`scale = min(img_w/design_w, img_h/design_h)`)
- Centraliza (`off_x`, `off_y`)
- Inverte o eixo Y (imagem cresce para baixo): `py = off_y + (1-fy)*out_h`
- Retorna `mm_to_px` e `px_to_mm`

Aplicado a contornos (rasterização de máscara) e pontos reais (`generated_stitches`).
Clamp final: pontos limitados a `[0, img_w-1]` x `[0, img_h-1]`.

## Bug secundário (editor não renderizava)
`refresh_canvas` retornava cedo quando `winfo_width() <= 1`, e não havia binding de `<Configure>`. Na abertura o canvas ainda tem largura 1 → nada era desenhado.

### Correção no editor_bordado.py
- `_auto_fitted = False` e `on_canvas_configure`: auto-fit na primeira vez + re-render nas demais
- `draw_region` agora desenha os pontos reais otimizados (`region.points`) com amostragem para performance, fallback para máscara
- `center_selected` (Ctrl+M): centraliza o objeto selecionado no centro da tela
- Atalhos novos: Ctrl+M (centralizar), Ctrl+D (duplicar), Ctrl+0 (ajustar), Ctrl+1 (100%), Ctrl+A (selecionar), setas (nudge), +/=/- (zoom)
- `select_all` e `duplicate_selected` implementados

## Resultado
- Fluxo carregar → converter → editar funciona
- test_image.png: 5 regiões, 1015 pontos reais, distribuídos corretamente (x/y dentro de 0-199px)
- Editor: 1015 pontos renderizados (era 0 antes)