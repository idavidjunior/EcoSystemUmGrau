"""
FASE 4 - Satin Engine (Motor de Satin)

Costura alternada entre dois lados de uma coluna.
Usado para bordas, colunas, lettering, detalhes finos.
O segredo: paralelismo, uniformidade, controle de ângulo.
"""

import math
from typing import List, Tuple, Optional
from ...core.stitches.stitch_primitives import StitchPoint, StitchPath, StitchCommand
from ...core.design.embroidery_design import StitchType


class SatinEngine:
    """Motor de costura satin (colunas estreitas, alternância de lados)."""

    def __init__(self, max_stitch_length: float = 12.0,
                 min_stitch_length: float = 0.5,
                 max_satin_width: float = 12.0):
        self.max_stitch_length = max_stitch_length
        self.min_stitch_length = min_stitch_length
        self.max_satin_width = max_satin_width

    def generate(self, left_rail: List[Tuple[float, float]],
                 right_rail: List[Tuple[float, float]],
                 color_index: int = 0,
                 density: float = 0.4) -> StitchPath:
        """Gera satin entre dois trilhos (rails)."""
        if not left_rail or not right_rail:
            return StitchPath()

        n_left = len(left_rail)
        n_right = len(right_rail)
        n = max(n_left, n_right)

        pairs = []
        for i in range(n):
            li = min(i, n_left - 1)
            ri = min(i, n_right - 1)
            pairs.append((left_rail[li], right_rail[ri]))

        result = StitchPath()
        result.add_stitch_absolute(pairs[0][0][0], pairs[0][0][1], StitchCommand.STITCH)
        result.add_stitch_absolute(pairs[0][1][0], pairs[0][1][1], StitchCommand.STITCH)

        for i in range(1, len(pairs)):
            lx, ly = pairs[i][0]
            rx, ry = pairs[i][1]
            result.add_stitch_absolute(rx, ry, StitchCommand.STITCH)
            if i + 1 < len(pairs):
                nlx, nly = pairs[i + 1][0]
                result.add_stitch_absolute(nlx, nly, StitchCommand.STITCH)

        return result

    def generate_from_contour(self, contour: List[Tuple[float, float]],
                              width: float = 6.0,
                              angle: float = 0.0,
                              color_index: int = 0,
                              density: float = 0.4) -> StitchPath:
        """Gera satin a partir de um contorno fechado, extraindo trilhos."""
        if len(contour) < 3:
            return StitchPath()

        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        projections = []
        for p in contour:
            proj = p[0] * cos_a + p[1] * sin_a
            projections.append((proj, p))
        projections.sort(key=lambda x: x[0])

        mid = len(projections) // 2
        rail_a = [p[1] for p in projections[:mid]]
        rail_b = [p[1] for p in projections[mid:]]

        rail_a.sort(key=lambda p: p[0] * cos_a + p[1] * sin_a)
        rail_b.sort(key=lambda p: p[0] * cos_a + p[1] * sin_a)

        n = max(len(rail_a), len(rail_b))
        if len(rail_a) < n:
            rail_a = self._resample_rail(rail_a, n)
        if len(rail_b) < n:
            rail_b = self._resample_rail(rail_b, n)

        return self.generate(rail_a, rail_b, color_index, density)

    def generate_column(self, points: List[Tuple[float, float]],
                        width: float = 6.0,
                        color_index: int = 0) -> StitchPath:
        """Gera satin ao longo de uma polilinha central com largura fixa."""
        if len(points) < 2:
            return StitchPath()

        left_rail = []
        right_rail = []

        for i in range(len(points)):
            if i < len(points) - 1:
                dx = points[i + 1][0] - points[i][0]
                dy = points[i + 1][1] - points[i][1]
            else:
                dx = points[i][0] - points[i - 1][0]
                dy = points[i][1] - points[i - 1][1]

            seg_len = math.sqrt(dx * dx + dy * dy)
            if seg_len > 0:
                nx = -dy / seg_len
                ny = dx / seg_len
            else:
                nx, ny = 0, 1

            half_w = width / 2.0
            left_rail.append((
                points[i][0] + half_w * nx,
                points[i][1] + half_w * ny
            ))
            right_rail.append((
                points[i][0] - half_w * nx,
                points[i][1] - half_w * ny
            ))

        return self.generate(left_rail, right_rail, color_index)

    def _resample_rail(self, rail: List[Tuple[float, float]],
                       target_count: int) -> List[Tuple[float, float]]:
        """Resample um rail para ter target_count pontos."""
        if len(rail) < 2 or target_count < 2:
            return list(rail)

        total_length = 0.0
        for i in range(1, len(rail)):
            dx = rail[i][0] - rail[i-1][0]
            dy = rail[i][1] - rail[i-1][1]
            total_length += math.sqrt(dx * dx + dy * dy)

        if total_length == 0:
            return [rail[0]] * target_count

        result = [rail[0]]
        step = total_length / (target_count - 1)
        accumulated = 0.0

        for i in range(1, len(rail)):
            dx = rail[i][0] - rail[i-1][0]
            dy = rail[i][1] - rail[i-1][1]
            seg_len = math.sqrt(dx * dx + dy * dy)
            if seg_len == 0:
                continue

            remaining = seg_len
            t_prev = 0.0
            while remaining > 0 and len(result) < target_count:
                needed = step - accumulated
                t_next = min(1.0, t_prev + needed / seg_len)
                px = rail[i-1][0] + dx * t_next
                py = rail[i-1][1] + dy * t_next
                result.append((px, py))

                actual = math.sqrt(
                    (px - (rail[i-1][0] + dx * t_prev)) ** 2 +
                    (py - (rail[i-1][1] + dy * t_prev)) ** 2
                )
                accumulated += actual
                remaining -= actual
                t_prev = t_next
                if accumulated >= step:
                    accumulated = 0

        while len(result) < target_count:
            result.append(rail[-1])
        return result[:target_count]
