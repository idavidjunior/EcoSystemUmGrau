"""
FASE 3 - Run Engine
Costura contínua ao longo de uma polilinha ou curva.
Usado para contornos simples, detalhes finos, outlines.
"""

import math
from typing import List, Tuple, Optional

from ...core.stitches.stitch_primitives import StitchCommand, StitchPoint, StitchPath
from ...core.design.embroidery_design import EmbroideryObject, StitchType


def _interpolate_line(x1, y1, x2, y2, step):
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.01:
        return [(x2, y2)]
    points = []
    dist = 0.0
    while dist < length:
        t = dist / length
        points.append((x1 + dx * t, y1 + dy * t))
        dist += step
    if points:
        last = points[-1]
        if math.sqrt((x2 - last[0]) ** 2 + (y2 - last[1]) ** 2) > step * 0.3:
            points.append((x2, y2))
    else:
        points.append((x2, y2))
    return points


def _smooth_curve(points, segments_per_point=3):
    if len(points) < 3:
        return points[:]
    smoothed = [points[0]]
    n = len(points)
    for i in range(n):
        p0 = points[(i - 1) % n]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n]
        for j in range(1, segments_per_point + 1):
            t = j / segments_per_point
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                        (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                        (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                        (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                        (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            smoothed.append((x, y))
    return smoothed


class RunEngine:
    """
    Gera costura run ao longo de caminhos.
    Tipos: RUN, TRIPLE_RUN, CENTER_RUN, EDGE_RUN, OUTLINE
    """

    def __init__(self, stitch_length=4.0, min_stitch_length=0.5, max_stitch_length=12.0):
        self.stitch_length = stitch_length
        self.min_stitch_length = min_stitch_length
        self.max_stitch_length = max_stitch_length

    def generate(self, obj=None, contour=None, stitch_type=None, color_index=0):
        """Gera pontos de costura. Aceita EmbroideryObject ou parâmetros diretos."""
        if obj is not None and hasattr(obj, 'contour'):
            contour = obj.contour
            stitch_type = obj.stitch_type
            step = obj.density if obj.density > 0 else self.stitch_length
        elif contour is not None:
            step = self.stitch_length
        else:
            return StitchPath()

        if not contour or len(contour) < 2:
            return StitchPath()

        if stitch_type == StitchType.TRIPLE_RUN:
            return self._triple_run(contour, step)
        elif stitch_type == StitchType.CENTER_RUN:
            return self._center_run(contour, step)
        elif stitch_type == StitchType.EDGE_RUN:
            return self._edge_run(contour, step)
        elif stitch_type == StitchType.OUTLINE:
            return self._outline_run(contour, step)
        else:
            return self._simple_run(contour, step)

    def _simple_run(self, points, step):
        path = StitchPath()
        if not points:
            return path
        path.add_stitch(points[0][0], points[0][1], StitchCommand.STITCH)
        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            interp = _interpolate_line(x1, y1, x2, y2, step)
            for px, py in interp[1:]:
                if path.points:
                    last = path.points[-1]
                    dist = math.sqrt((px - last.x) ** 2 + (py - last.y) ** 2)
                    if dist > self.max_stitch_length:
                        path.add_stitch(px, py, StitchCommand.JUMP)
                path.add_stitch(px, py, StitchCommand.STITCH)
        return path

    def _triple_run(self, points, step):
        path_fwd = self._simple_run(points, step)
        reversed_pts = list(reversed(points))
        path_back = self._simple_run(reversed_pts, step)
        path_fwd2 = self._simple_run(points, step)
        result = StitchPath()
        result.points.extend(path_fwd.points)
        result.points.extend(path_back.points)
        result.points.extend(path_fwd2.points)
        return result

    def _center_run(self, contour, step):
        if len(contour) < 3:
            return self._simple_run(contour, step)
        cx = sum(p[0] for p in contour) / len(contour)
        cy = sum(p[1] for p in contour) / len(contour)
        avg_x = sum(p[0] for p in contour) / len(contour)
        sorted_by_dist = sorted(contour, key=lambda p: (p[0] - avg_x) ** 2)
        if len(sorted_by_dist) >= 2:
            return self._simple_run([sorted_by_dist[0], sorted_by_dist[-1]], step)
        return self._simple_run(contour, step)

    def _edge_run(self, contour, step):
        return self._simple_run(contour, step)

    def _outline_run(self, contour, step):
        if len(contour) < 3:
            return self._simple_run(contour, step)
        smoothed = _smooth_curve(contour, segments_per_point=4)
        return self._simple_run(smoothed, step)
