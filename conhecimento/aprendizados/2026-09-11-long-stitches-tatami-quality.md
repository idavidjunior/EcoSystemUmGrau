---
tipo: erro
tags: [embroidery, tatami, quality-engine, long-stitches, max-stitch-length, stitch-planner]
data: 2026-09-11
contexto: FASE 5/13/18 do EmbroideryEngine. O QualityEngine reportava centenas de "long stitches" (>12mm) mesmo após correções de split no TatamiEngine.
decisao: Aplicar o pós-processamento _enforce_max_stitch_length no path final combinado (underlay + main_path + compensação) no StitchPlanner, e corrigir o QualityEngine para não medir distância STITCH contra ponto anterior não-STITCH.
impacto: Score de qualidade subiu de 84.5 para 96.5; long stitches por objeto caíram para 0 (exceto saltos JUMP legítimos).
---

## Problema
O QualityEngine (`_check_stitch_lengths`) comparava cada STITCH com `points[i-1]`, sem verificar o comando anterior. Quando um JUMP precedia um STITCH, a distância era medida como "long stitch" — falso positivo.

Além disso, o `_enforce_max_stitch_length` do TatamiEngine rodava apenas dentro de `generate()` sobre o `main_path`, mas o StitchPlanner combina underlay + main_path + compensação. O enforce precisava ser aplicado ao path final.

## Causas
1. `_check_stitch_lengths` media STITCH contra o ponto imediatamente anterior (que podia ser JUMP/TRIM/etc.), sem rastrear o último STITCH real.
2. O enforce de max_stitch_length não cobria underlay nem o path combinado final.
3. `StitchCommand.TIE_ON` não existe — o correto é `TIE_IN` (causava AttributeError).

## Correções aplicadas
- `quality_engine.py`: `_check_stitch_lengths` agora rastreia `last_stitch` e reseta para `None` em comandos não-STITCH e não-TIE (JUMP/TRIM/etc.). `_check_long_jumps` usa `last_anchor` (STITCH/TIE_OFF/TIE_IN).
- `stitch_planner.py`: aplica `tatami_engine._enforce_max_stitch_length(path)` após a compensação, sobre o path final.
- `segmentation_engine.py`: `remove_small_objects(min_size=...)` → `max_size=...` (deprecation do scikit-image 0.26).

## Resultado
- Score: 84.5 → 96.5
- Issues: 6 → 2 (8 stitches curtos em Region_3; 6 saltos longos legítimos em Region_0)
- Long stitches por objeto: 0 (os que restam são JUMP-separados, classificados como "saltos", não "stitches")