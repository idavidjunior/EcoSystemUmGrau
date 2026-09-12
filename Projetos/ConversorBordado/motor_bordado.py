#!/usr/bin/env python3
"""
Motor Profissional de Digitalização - Ponte entre o EmbroideryEngine e o Conversor.

Este módulo substitui o motor de digitalização simples do conversor.py pelo
DigitizerPipeline do EmbroideryEngine, que oferece:
  - Segmentação com limpeza morfológica
  - Vectorização de contornos
  - Classificação de objetos (tatami, satin, run)
  - Underlay, compensação pull/push e sequenciamento otimizado
  - Controle de qualidade com score

Mantém a interface do conversor intacta: o resultado é convertido para a
lista de StitchRegion que o visualizador e o editor já consomem.
"""

import sys
import os
import math
from typing import List, Tuple

import numpy as np
from PIL import Image
from skimage.draw import polygon as sk_polygon

from editor_bordado import StitchRegion, StitchType as EdStitchType


# Caminho para o EmbroideryEngine (pai de src, para imports como src.pipeline)
_EMBROIDERY_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', 'EmbroideryEngine'))
if _EMBROIDERY_ROOT not in sys.path:
    sys.path.insert(0, _EMBROIDERY_ROOT)


def _map_stitch_type(engine_type) -> EdStitchType:
    """Mapeia o StitchType do EmbroideryEngine para o do editor."""
    name = getattr(engine_type, 'name', str(engine_type)).upper()
    if name in ('TATAMI', 'FILL', 'STEP'):
        return EdStitchType.FILL
    if name == 'SATIN':
        return EdStitchType.SATIN
    if name in ('RUN', 'TRIPLE_RUN', 'OUTLINE'):
        return EdStitchType.RUNNING
    return EdStitchType.FILL


def _point_in_polygon(x: float, y: float,
                      poly: List[Tuple[float, float]]) -> bool:
    """Testa se um ponto está dentro de um polígono (ray casting)."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and \
           (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _rasterize_contour(contour: List[Tuple[float, float]],
                       scale_px: float,
                       width_px: int,
                       height_px: int) -> np.ndarray:
    """Rasteriza um contorno (em mm) em uma máscara binária (pixels)."""
    mask = np.zeros((height_px, width_px), dtype=bool)

    pts = [(p[0] * scale_px, p[1] * scale_px) for p in contour]
    if len(pts) < 3:
        return mask

    # Usar ponto-em-polígono sobre a bbox do contorno
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x = max(0, int(min(xs)))
    max_x = min(width_px - 1, int(max(xs)))
    min_y = max(0, int(min(ys)))
    max_y = min(height_px - 1, int(max(ys)))

    # Amostragem com ponto-em-polígono (contornos podem ser concavos)
    for py in range(min_y, max_y + 1):
        for px in range(min_x, max_x + 1):
            if _point_in_polygon(px + 0.5, py + 0.5, pts):
                mask[py, px] = True

    return mask


def _stitches_to_points(generated_stitches) -> List[Tuple[float, float]]:
    """Extrai pontos reais (STITCH) do caminho gerado, convertidos para pixels."""
    points = []
    if generated_stitches is None or not getattr(generated_stitches, 'points', None):
        return points
    for pt in generated_stitches.points:
        cmd = getattr(pt, 'command', None)
        name = getattr(cmd, 'name', str(cmd)).upper()
        if name == 'STITCH':
            points.append((pt.x, pt.y))
    return points


def digitizar(path_imagem: str,
              max_colors: int = 6,
              density: float = 0.4,
              scale_mm: float = 0.2,
              canvas_width_mm: float = 200.0,
              canvas_height_mm: float = 200.0) -> List[StitchRegion]:
    """Digitaliza uma imagem usando o motor profissional do EmbroideryEngine.

    Retorna a lista de StitchRegion pronta para o visualizador/editor.
    """
    from src.pipeline.digitizer_pipeline import DigitizerPipeline

    pipeline = DigitizerPipeline(density=density, max_colors=max_colors,
                                 scale_mm=scale_mm)
    design = pipeline.digitize(path_imagem, canvas_width_mm, canvas_height_mm)

    # Tamanho em pixels da imagem original (para conversão mm -> px)
    img = Image.open(path_imagem)
    img_w, img_h = img.size
    img_rgb = img.convert('RGB')

    # scale_px = pixels por mm (inverso de scale_mm)
    scale_px = 1.0 / scale_mm

    regions = []
    for idx, obj in enumerate(design.objects):
        # Cor
        color = obj.color
        r = int(getattr(color, 'r', 0))
        g = int(getattr(color, 'g', 0))
        b = int(getattr(color, 'b', 0))

        # Rasterizar contorno em máscara
        mask = _rasterize_contour(obj.contour, scale_px, img_w, img_h)

        # Bounds da máscara
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not np.any(rows) or not np.any(cols):
            continue
        minr, maxr = np.where(rows)[0][[0, -1]]
        minc, maxc = np.where(cols)[0][[0, -1]]

        # Recortar máscara para a bbox (formato usado pelo visualizador)
        mask_crop = mask[minr:maxr + 1, minc:maxc + 1]

        # Pontos reais do motor (em mm) convertidos para pixels globais
        raw_points = _stitches_to_points(obj.generated_stitches)
        points = [(p[0] * scale_px, p[1] * scale_px) for p in raw_points]
        if not points:
            # Fallback: amostrar a máscara
            ys, xs = np.where(mask_crop)
            if len(xs) == 0:
                continue
            step = max(1, len(xs) // 500)
            points = [(float(minc + xs[k]), float(minr + ys[k]))
                      for k in range(0, len(xs), step)]

        region = StitchRegion(
            id=idx,
            color=(r, g, b),
            stitch_type=_map_stitch_type(obj.stitch_type),
            density=max(0.1, obj.density),
            angle=float(obj.direction_angle),
            mask=mask_crop,
            bounds=(minr, minc, maxr, maxc),
            points=points,
            visible=obj.visible,
            name=obj.name or f"Região {idx}"
        )
        regions.append(region)

    return regions


def obter_score(path_imagem: str, max_colors: int = 6,
                density: float = 0.4,
                scale_mm: float = 0.2) -> float:
    """Retorna o score de qualidade do design gerado pelo motor."""
    from src.pipeline.digitizer_pipeline import DigitizerPipeline
    from src.quality.quality_engine import QualityEngine

    pipeline = DigitizerPipeline(density=density, max_colors=max_colors,
                                 scale_mm=scale_mm)
    design = pipeline.digitize(path_imagem)

    qe = QualityEngine()
    report = qe.analyze(design)
    return float(report.get('score', 0.0))