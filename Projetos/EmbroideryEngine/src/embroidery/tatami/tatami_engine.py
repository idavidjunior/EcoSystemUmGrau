"""
FASE 5 - Tatami Engine (Motor de Preenchimento)

Preenche áreas grandes com linhas paralelas ou em ziguezague.
Suporta: tatami clássico, program split, spiral, cross-stitch, padrões.
"""

import math
from typing import List, Tuple, Optional
from ...core.stitches.stitch_primitives import StitchPoint, StitchPath, StitchCommand
from ...core.design.embroidery_design import StitchType


class TatamiEngine:
    """Motor de preenchimento tatami (áreas grandes)."""

    def __init__(self, max_stitch_length: float = 12.0, min_stitch_length: float = 0.5):
        self.max_stitch_length = max_stitch_length
        self.min_stitch_length = min_stitch_length

    def generate(self, contour: List[Tuple[float, float]],
                 stitch_type: StitchType = StitchType.TATAMI,
                 density: float = 0.4,
                 angle: float = 0.0,
                 color_index: int = 0,
                 holes: Optional[List[List[Tuple[float, float]]]] = None) -> StitchPath:
        """Gera preenchimento tatami para um contorno fechado."""
        if len(contour) < 3:
            return StitchPath()

        if stitch_type == StitchType.SPIRAL:
            return self._spiral_fill(contour, density, color_index)
        elif stitch_type == StitchType.CROSS_STITCH:
            return self._cross_stitch_fill(contour, density, angle, color_index)
        elif stitch_type == StitchType.PROGRAM_SPLIT:
            return self._program_split_fill(contour, density, angle, color_index)
        else:
            return self._tatami_fill(contour, density, angle, color_index, holes)

    def _tatami_fill(self, contour: List[Tuple[float, float]],
                     density: float, angle: float,
                     color_index: int,
                     holes: Optional[List[List[Tuple[float, float]]]] = None) -> StitchPath:
        """Tatami clássico: scan lines paralelas com alternância de direção."""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rotated = [(p[0] * cos_a - p[1] * sin_a,
                     p[0] * sin_a + p[1] * cos_a) for p in contour]

        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)

        result = StitchPath()
        first_stitch = True
        direction = 1

        y = min_y + density / 2
        while y <= max_y:
            intersections = self._scan_line(rotated, y)
            if len(intersections) >= 2:
                intersections.sort()
                scan_points = []
                i = 0
                while i < len(intersections) - 1:
                    x1 = intersections[i]
                    x2 = intersections[i + 1]
                    if holes:
                        mid_x = (x1 + x2) / 2
                        orig_mid = (mid_x * cos_a + y * sin_a,
                                    -mid_x * sin_a + y * cos_a)
                        in_hole = any(
                            self._point_in_polygon(orig_mid, hole)
                            for hole in holes
                        )
                        if not in_hole:
                            scan_points.append((x1, x2))
                    else:
                        scan_points.append((x1, x2))
                    i += 2

                for x1, x2 in scan_points:
                    if direction == 1:
                        pts = [(x1, y), (x2, y)]
                    else:
                        pts = [(x2, y), (x1, y)]

                    for px, py in pts:
                        orig_x = px * cos_a + py * sin_a
                        orig_y = -px * sin_a + py * cos_a

                        if first_stitch:
                            result.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)
                            first_stitch = False
                        else:
                            last = result.points[-1]
                            dist = math.sqrt((orig_x - last.x) ** 2 + (orig_y - last.y) ** 2)
                            if dist > self.max_stitch_length:
                                result.add_stitch_absolute(orig_x, orig_y, StitchCommand.JUMP)
                            result.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)

            direction *= -1
            y += density

        return result

    def _program_split_fill(self, contour: List[Tuple[float, float]],
                            density: float, angle: float,
                            color_index: int) -> StitchPath:
        """Program split: alterna direção de preenchimento a cada poucas linhas."""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rotated = [(p[0] * cos_a - p[1] * sin_a,
                     p[0] * sin_a + p[1] * cos_a) for p in contour]

        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)

        result = StitchPath()
        first_stitch = True
        block_size = 3

        y = min_y + density / 2
        line_num = 0
        while y <= max_y:
            intersections = self._scan_line(rotated, y)
            if len(intersections) >= 2:
                intersections.sort()
                block = line_num // block_size
                direction = 1 if block % 2 == 0 else -1

                i = 0
                while i < len(intersections) - 1:
                    x1 = intersections[i]
                    x2 = intersections[i + 1]

                    if direction == 1:
                        pts = [(x1, y), (x2, y)]
                    else:
                        pts = [(x2, y), (x1, y)]

                    for px, py in pts:
                        orig_x = px * cos_a + py * sin_a
                        orig_y = -px * sin_a + py * cos_a

                        if first_stitch:
                            result.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)
                            first_stitch = False
                        else:
                            last = result.points[-1]
                            dist = math.sqrt((orig_x - last.x) ** 2 + (orig_y - last.y) ** 2)
                            if dist > self.max_stitch_length:
                                result.add_stitch_absolute(orig_x, orig_y, StitchCommand.JUMP)
                            result.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)

                    i += 2

            line_num += 1
            y += density

        return result

    def _spiral_fill(self, contour: List[Tuple[float, float]],
                     density: float, color_index: int) -> StitchPath:
        """Preenchimento em espiral a partir do centro."""
        if len(contour) < 3:
            return StitchPath()

        cx = sum(p[0] for p in contour) / len(contour)
        cy = sum(p[1] for p in contour) / len(contour)

        max_dist = max(
            math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2)
            for p in contour
        )

        result = StitchPath()
        result.add_stitch_absolute(cx, cy, StitchCommand.STITCH)

        angle = 0
        radius = 0
        step_angle = density / max(max_dist * 0.1, 0.1)
        step_radius = density * 0.02

        while radius < max_dist:
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            if self._point_in_polygon((x, y), contour):
                result.add_stitch_absolute(x, y, StitchCommand.STITCH)

            angle += step_angle
            radius += step_radius

            if angle > math.pi * 2:
                angle -= math.pi * 2

        return result

    def _cross_stitch_fill(self, contour: List[Tuple[float, float]],
                           density: float, angle: float,
                           color_index: int) -> StitchPath:
        """Preenchimento em cruz (cross-stitch pattern)."""
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rotated = [(p[0] * cos_a - p[1] * sin_a,
                     p[0] * sin_a + p[1] * cos_a) for p in contour]

        min_x = min(p[0] for p in rotated)
        max_x = max(p[0] for p in rotated)
        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)

        result = StitchPath()
        first_stitch = True
        cell = density * 3

        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                center = (x + cell / 2, y + cell / 2)
                orig_center = (center[0] * cos_a + center[1] * sin_a,
                               -center[0] * sin_a + center[1] * cos_a)

                if self._point_in_polygon(orig_center, contour):
                    size = cell * 0.4
                    corners = [
                        (x + cell / 2 - size, y + cell / 2 - size),
                        (x + cell / 2 + size, y + cell / 2 + size),
                        (x + cell / 2 + size, y + cell / 2 - size),
                        (x + cell / 2 - size, y + cell / 2 + size),
                    ]

                    for cx, cy in corners:
                        orig = (cx * cos_a + cy * sin_a, -cx * sin_a + cy * cos_a)
                        if first_stitch:
                            result.add_stitch_absolute(orig[0], orig[1], StitchCommand.STITCH)
                            first_stitch = False
                        else:
                            result.add_stitch_absolute(orig[0], orig[1], StitchCommand.STITCH)

                x += cell
            y += cell

        return result

    def _scan_line(self, polygon: List[Tuple[float, float]], y: float) -> List[float]:
        """Scan line: encontra interseções com o polígono."""
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

    def _point_in_polygon(self, point: Tuple[float, float],
                          polygon: List[Tuple[float, float]]) -> bool:
        """Ray casting point-in-polygon."""
        x, y = point
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
