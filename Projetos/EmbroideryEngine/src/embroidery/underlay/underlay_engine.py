"""
FASE 6 - Underlay Engine (Motor de Underlay / Base)

Gera camadas de suporte sob a costura principal.
O underlay é invisível no resultado final, mas essencial para:
- Estabilizar o tecido
- Prevenir distorção (pull/push)
- Dar volume e elevação
- Suportar costuras longas
Tipos: edge_run, center_run, zigzag, double_zigzag, fill, contour
"""

import math
from typing import List, Tuple, Optional
from ...core.stitches.stitch_primitives import StitchPoint, StitchPath, StitchCommand
from ...core.design.embroidery_design import UnderlayType, StitchType


class UnderlayEngine:
    """Motor de geração de underlay (base de suporte)."""

    def __init__(self, max_stitch_length: float = 12.0):
        self.max_stitch_length = max_stitch_length

    def generate(self, contour: List[Tuple[float, float]],
                 underlay_type: UnderlayType,
                 stitch_type: StitchType = StitchType.FILL,
                 density: float = 0.6,
                 angle: float = 0.0,
                 width: float = 0.0) -> StitchPath:
        """Gera underlay baseado no tipo especificado."""
        if underlay_type == UnderlayType.NONE:
            return StitchPath()

        generators = {
            UnderlayType.EDGE_RUN: self._edge_run,
            UnderlayType.CENTER_RUN: self._center_run,
            UnderlayType.ZIGZAG: self._zigzag,
            UnderlayType.DOUBLE_ZIGZAG: self._double_zigzag,
            UnderlayType.FILL: self._fill_underlay,
            UnderlayType.CONTOUR: self._contour,
        }

        gen_func = generators.get(underlay_type)
        if gen_func:
            return gen_func(contour, density, angle, width)
        return StitchPath()

    def generate_for_satin(self, left_rail: List[Tuple[float, float]],
                           right_rail: List[Tuple[float, float]],
                           underlay_type: UnderlayType = UnderlayType.ZIGZAG,
                           density: float = 0.6) -> StitchPath:
        """Gera underlay específico para satin (entre dois trilhos)."""
        if underlay_type == UnderlayType.NONE:
            return StitchPath()

        if underlay_type == UnderlayType.CENTER_RUN:
            return self._center_run_between_rails(left_rail, right_rail, density)
        elif underlay_type == UnderlayType.ZIGZAG:
            return self._zigzag_between_rails(left_rail, right_rail, density)
        elif underlay_type == UnderlayType.DOUBLE_ZIGZAG:
            return self._double_zigzag_between_rails(left_rail, right_rail, density)

        return StitchPath()

    def _edge_run(self, contour: List[Tuple[float, float]],
                  density: float, angle: float, width: float) -> StitchPath:
        """Costura ao longo da borda, uma ou duas vezes."""
        result = StitchPath()
        if len(contour) < 2:
            return result

        for p in contour:
            result.add_stitch_absolute(p[0], p[1], StitchCommand.STITCH)

        if len(contour) > 2:
            result.add_stitch_absolute(contour[0][0], contour[0][1], StitchCommand.STITCH)

        return result

    def _center_run(self, contour: List[Tuple[float, float]],
                    density: float, angle: float, width: float) -> StitchPath:
        """Costura pela linha central do contorno."""
        if len(contour) < 3:
            return self._edge_run(contour, density, angle, width)

        cx = sum(p[0] for p in contour) / len(contour)
        cy = sum(p[1] for p in contour) / len(contour)

        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        projections = []
        for p in contour:
            proj = (p[0] - cx) * cos_a + (p[1] - cy) * sin_a
            projections.append((proj, p))
        projections.sort(key=lambda x: x[0])

        n = len(projections)
        start = projections[n // 4][1]
        end = projections[3 * n // 4][1]

        result = StitchPath()
        self._add_line_with_splits(result, start[0], start[1], end[0], end[1])
        return result

    def _zigzag(self, contour: List[Tuple[float, float]],
                density: float, angle: float, width: float) -> StitchPath:
        """Zigzag dentro do contorno."""
        result = StitchPath()
        if len(contour) < 3:
            return result

        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rotated = [(p[0] * cos_a - p[1] * sin_a,
                     p[0] * sin_a + p[1] * cos_a) for p in contour]

        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)

        y = min_y + density
        first = True
        while y < max_y:
            intersections = self._scan_line(rotated, y)
            if len(intersections) >= 2:
                intersections.sort()
                x1 = intersections[0]
                x2 = intersections[-1]

                ox1 = x1 * cos_a + y * sin_a
                oy1 = -x1 * sin_a + y * cos_a
                ox2 = x2 * cos_a + y * sin_a
                oy2 = -x2 * sin_a + y * cos_a

                if first:
                    result.add_stitch_absolute(ox1, oy1, StitchCommand.STITCH)
                    first = False
                else:
                    result.add_stitch_absolute(ox1, oy1, StitchCommand.STITCH)

                result.add_stitch_absolute(ox2, oy2, StitchCommand.STITCH)
            y += density

        return result

    def _double_zigzag(self, contour: List[Tuple[float, float]],
                       density: float, angle: float, width: float) -> StitchPath:
        """Dois zigzags sobrepostos."""
        zz1 = self._zigzag(contour, density, angle, width)
        zz2 = self._zigzag(contour, density, angle + 90, width)

        result = StitchPath()
        result.points = zz1.points
        if zz2.points:
            for p in zz2.points:
                result.points.append(p)
        return result

    def _fill_underlay(self, contour: List[Tuple[float, float]],
                       density: float, angle: float, width: float) -> StitchPath:
        """Preenchimento leve como base."""
        return self._zigzag(contour, density * 1.5, angle, width)

    def _contour(self, contour: List[Tuple[float, float]],
                 density: float, angle: float, width: float) -> StitchPath:
        """Contorno em escala reduzida (inset)."""
        if len(contour) < 3:
            return StitchPath()

        cx = sum(p[0] for p in contour) / len(contour)
        cy = sum(p[1] for p in contour) / len(contour)

        inset = []
        inset_dist = 1.0
        for i, p in enumerate(contour):
            dx = p[0] - cx
            dy = p[1] - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > inset_dist:
                scale = (dist - inset_dist) / dist
                inset.append((cx + dx * scale, cy + dy * scale))
            else:
                inset.append(p)

        return self._edge_run(inset, density, angle, width)

    def _center_run_between_rails(self, left: List[Tuple[float, float]],
                                  right: List[Tuple[float, float]],
                                  density: float) -> StitchPath:
        """Linha central entre dois trilhos de satin."""
        result = StitchPath()
        n = min(len(left), len(right))

        for i in range(n):
            mid_x = (left[i][0] + right[i][0]) / 2
            mid_y = (left[i][1] + right[i][1]) / 2
            result.add_stitch_absolute(mid_x, mid_y, StitchCommand.STITCH)

        return result

    def _zigzag_between_rails(self, left: List[Tuple[float, float]],
                              right: List[Tuple[float, float]],
                              density: float) -> StitchPath:
        """Zigzag entre dois trilhos de satin."""
        result = StitchPath()
        n = min(len(left), len(right))

        for i in range(n):
            if i % 2 == 0:
                result.add_stitch_absolute(left[i][0], left[i][1], StitchCommand.STITCH)
            else:
                result.add_stitch_absolute(right[i][0], right[i][1], StitchCommand.STITCH)

        return result

    def _double_zigzag_between_rails(self, left: List[Tuple[float, float]],
                                     right: List[Tuple[float, float]],
                                     density: float) -> StitchPath:
        """Dois zigzags entre trilhos."""
        zz1 = self._zigzag_between_rails(left, right, density)
        result = StitchPath()
        result.points = zz1.points

        offset = density * 0.3
        for i in range(len(left)):
            mid_x = (left[i][0] + right[i][0]) / 2 + offset
            mid_y = (left[i][1] + right[i][1]) / 2 + offset
            result.add_stitch_absolute(mid_x, mid_y, StitchCommand.STITCH)

        return result

    def _add_line_with_splits(self, path: StitchPath,
                              x1: float, y1: float, x2: float, y2: float):
        """Adiciona uma linha dividida no comprimento máximo."""
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)

        path.add_stitch_absolute(x1, y1, StitchCommand.STITCH)

        if dist <= self.max_stitch_length:
            path.add_stitch_absolute(x2, y2, StitchCommand.STITCH)
        else:
            num = max(1, int(math.ceil(dist / self.max_stitch_length)))
            for s in range(1, num + 1):
                t = s / num
                path.add_stitch_absolute(x1 + dx * t, y1 + dy * t, StitchCommand.STITCH)

    def _scan_line(self, polygon: List[Tuple[float, float]], y: float) -> List[float]:
        """Scan line intersections."""
        intersections = []
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            y1 = polygon[i][1]
            y2 = polygon[j][1]
            if (y1 <= y < y2) or (y2 <= y < y1):
                if y1 != y2:
                    x = polygon[i][0] + (y - y1) / (y2 - y1) * (polygon[j][0] - polygon[i][0])
                    intersections.append(x)
        return intersections

    def select_underlay(self, stitch_type: StitchType,
                        width: float, area: float,
                        fabric: str = "cotton") -> UnderlayType:
        """Seleciona automaticamente o tipo de underlay."""
        if stitch_type in (StitchType.RUN, StitchType.TRIPLE_RUN):
            return UnderlayType.NONE

        if width < 3.0:
            return UnderlayType.CENTER_RUN
        elif width < 8.0:
            return UnderlayType.EDGE_RUN
        elif area < 200.0:
            return UnderlayType.ZIGZAG
        elif area < 500.0:
            return UnderlayType.DOUBLE_ZIGZAG
        else:
            return UnderlayType.FILL
