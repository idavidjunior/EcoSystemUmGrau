---
tipo: decisao
tags: [embroidery, conversor-bordado, embroidery-engine, digitizer-pipeline, integracao]
data: 2026-09-11
contexto: Usuário pediu para melhorar o MOTOR do ConversorBordado mantendo a interface atual (conversor.py), com padrão de qualidade Wilcom/PE-Design. O motor antigo fazia apenas quantização de 6 cores + fill horizontal.
decisao: Criar a ponte motor_bordado.py que usa o DigitizerPipeline do EmbroideryEngine (segmentação, vectorização, classificação tatami/satin/run, underlay, compensação, sequenciamento) e converte o EmbroideryDesign em List[StitchRegion] (formato que visualizador/editor já consomem). O conversor.py troca o extract_regions_from_image e o auto_convert pelo motor profissional, com fallback legado.
impacto: Qualidade do bordado muito superior (score 96.5, tipos de costura corretos, pontos reais otimizados). Interface do usuário inalterada.
---

## Problema
O conversor.py usava um motor muito simples: quantizava a imagem para 6 cores e gerava fill horizontal por pixel. Isso não alcança a qualidade Wilcom/PE-Design desejada.

## Solução
1. Novo módulo `motor_bordado.py` (ponte):
   - `digitizar(path, ...)` → usa `DigitizerPipeline.digitize()` e converte cada `EmbroideryObject` em `StitchRegion`.
   - Rasteriza o contorno (mm) de volta para máscara (pixels) com `_point_in_polygon`.
   - Extrai os pontos reais otimizados (`generated_stitches`) para o StitchSimulator e o save.
   - `obter_score(path)` → retorna o score de qualidade.
2. `conversor.py`:
   - `extract_regions_from_image` agora chama o motor profissional (fallback `_extract_regions_legacy`).
   - Novo `auto_convert_profissional(pattern)` gera o padrão pyembroidery a partir das regiões reais.

## Detalhes técnicos
- Caminho do EmbroideryEngine: `_EMBROIDERY_ROOT` = pai de `src` (para import `src.pipeline`), não o próprio `src`.
- Conversão mm → px: `scale_px = 1.0 / scale_mm`.
- Mapeamento de tipos: tatami/fill/step → FILL; satin → SATIN; run → RUNNING.
- Rasterização de contorno usa ray casting (`_point_in_polygon`) sobre a bbox.

## Resultado
- `test_image.png`: 5 regiões, 4 cores, classificação correta (1 satin, resto fill), score 96.5.
- PES e DST gerados com sucesso (1020 stitches, 5 color changes).
- Interface abre sem erro; fluxo de preview/editor inalterado.