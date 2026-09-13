---
tipo: padrao
tags: [embroidery, classificador, outline, texto, orientacao, direction-angle, contorno]
data: 2026-09-13
projeto: EmbroideryEngine
---

# ImprovedStitchClassifier — OUTLINE, TEXTO e ORIENTAÇÃO DOMINANTE

## Contexto

O `ObjectClassifier` (objeto legado do pipeline) nunca detectava CONTORNO, nunca
detectava TEXTO e nunca preenchia `direction_angle` (ficava sempre 0.0).
Diagnóstico: `circularity` nunca era calculada na segmentação (sempre 0),
`TRIPLE_RUN` para área pequena era inalcançável (SATIN dominava), e o campo
`direction_angle` existia no dataclass `EmbroideryObject` mas nada preenchia.

## Decisão

Criar módulo NOVO `src/embroidery/classifier/improved_classifier.py` com a classe
`ImprovedStitchClassifier` (não alterar os legados `object_classifier.py` e
`stitch_classifier.py`). Preservar a interface pública `classify(region)` e
`assign_all(regions)`.

## O que o módulo faz

- `classify_with_metadata(region)` → dict com `stitch_type`, `direction_angle`,
  `confidence` e `classification_source` ('heuristic' | 'text_cluster' | 'fallback').
- `classify_all(regions)` (e alias `assign_all`) → injeta `stitch_type`,
  `direction_angle`, `confidence`, `classification_source` em cada dict de região
  e faz detecção contextual de texto (cluster de ≥3 glifos pequenos próximos com
  orientação consistente → RUN).
- Features: regionprops (skimage) quando há máscara; PCA do contorno (numpy puro)
  quando só há contorno. `stroke = 2*area/perimeter`.
- Regras: OUTLINE (hole_fraction > 0.15 + stroke < 5mm), RUN (stroke < 1.5 +
  aspect > 4, ou small+thin), SATIN (width < 12 ou stroke < 8, + ecc > 0.85 ou
  aspect > 2.5), TATAMI (area > 200 + aspect < 2.5), FILL (área ≥ 30 + min_dim ≥ 5),
  fallback → ObjectClassifier.
- Thresholds públicos calibráveis como atributos de classe
  (OUTLINE_HOLE_FRACTION, OUTLINE_MAX_STROKE, etc.).

## Wiring (feito)

- `pipeline/digitizer_pipeline.py`: import e uso trocados
  `ObjectClassifier` → `ImprovedStitchClassifier`.
- `embroidery/planning/stitch_planner.py`: idem (linhas ~190 e ~208).
- `stitch_planner._region_to_object`: adicionado
  `direction_angle=region.get('direction_angle', 0.0)` no construtor do
  `EmbroideryObject`.

## Pitfalls descobertos (IMPORTANTE)

1. **skimage `regionprops.orientation` mede a partir do eixo de LINHAS (vertical)**:
   retângulo/elipse HORIZONTAIS dão ~90° (não 0°). Ao converter para 0–180° ou
   testar ângulo dominante, aceitar 0° e 90° como equivalentes para formas
   horizontais. Não "corrigir" para 0° — quebraria a convenção do motor satin.
2. **`assign_all` é o nome que o pipeline chama**, não `classify_all`. O alias
   `assign_all = classify_all` está no módulo — não remover.
3. **`filled_area` está deprecado no skimage ≥0.26** → usar `area_filled`
   (com fallback `getattr`).
4. **Máscara pequena distorce features**: elipse 50x10mm precisa de máscara ≥
   300px (`2*rx + margem`); máscara 160px cortava a elipse e a largura caía para
   32mm → classificava FILL em vez de SATIN. Sempre criar máscaras de teste com
   folga.
5. **Testes sintéticos**: `draw.rectangle` espera `(row_start, col_start)` e
   `extent=(n_rows, n_cols)` — extents invertidos criam retângulo vertical.

## Validação

- `tests/test_improved_classifier.py`: 6 testes (golden set 11 formas,
  zero regressão vs ObjectClassifier, cluster de texto, ângulo dominante,
  fallback, bounds de confiança). Todos passam.
- Suíte completa: 80 passed (74 existentes + 6 novos), zero regressão.
- E2E: `DigitizerPipeline.digitize` em imagem sintética com coluna 60x6mm →
  1 objeto SATIN com `direction_angle=90.0` propagado até o design.

## Impacto

- Colunas/elipses continuam SATIN (motor satin intacto).
- Regiões grandes continuam TATAMI/FILL (motor tatami intacto).
- Agora é possível quebrar CONTORNO em peças de bordado e direcionar satin/tatami
  pelo ângulo dominante real (campo `direction_angle` finalmente preenchido).