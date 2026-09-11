"""
FASE 7 - Compensation Engine (Motor de Compensação Pull/Push)

O tecido encolhe (pull) ao longo da direção da costura e expande (push)
na direção perpendicular. Este motor ajusta os pontos para compensar.
"""

import math
from typing import List, Tuple
from ...core.stitches.stitch_primitives import StitchPoint, StitchPath, StitchCommand
from ...core.design.embroidery_design import StitchType, FabricType


# Tabelas de compensação por tecido (mm)
PULL_COMPENSATION = {
    FabricType.COTTON: 0.3,
    FabricType.KNIT: 0.8,
    FabricType.DENIM: 0.2,
    FabricType.FLEECE: 0.6,
    FabricType.POLYESTER: 0.3,
    FabricType.SILK: 0.4,
    FabricType.LEATHER: 0.1,
    FabricType.CAP: 0.4,
    FabricType.WOOL: 0.3,
    FabricType.LINEN: 0.25,
    FabricType.CUSTOM: 0.3,
}

PUSH_COMPENSATION = {
    FabricType.COTTON: 0.2,
    FabricType.KNIT: 0.5,
    FabricType.DENIM: 0.1,
    FabricType.FLEECE: 0.4,
    FabricType.POLYESTER: 0.2,
    FabricType.SILK: 0.3,
    FabricType.LEATHER: 0.05,
    FabricType.CAP: 0.3,
    FabricType.WOOL: 0.2,
    FabricType.LINEN: 0.15,
    FabricType.CUSTOM: 0.2,
}


class CompensationEngine:
    """Motor de compensação de pull/push."""

    def __init__(self):
        self.pull_table = PULL_COMPENSATION
        self.push_table = PUSH_COMPENSATION

    def apply(self, path: StitchPath,
              pull: float = 0.0, push: float = 0.0,
              stitch_type: StitchType = StitchType.FILL,
              fabric: FabricType = FabricType.COTTON) -> StitchPath:
        """Aplica compensação de pull/push nos pontos."""
        if not path.points:
            return path

        if pull == 0 and push == 0:
            pull = self.pull_table.get(fabric, 0.3)
            push = self.push_table.get(fabric, 0.2)

        result = StitchPath()
        stitch_points = [p for p in path.points if p.command == StitchCommand.STITCH]

        if len(stitch_points) < 2:
            result.points = list(path.points)
            return result

        for i, p in enumerate(path.points):
            if p.command != StitchCommand.STITCH:
                result.add_stitch_absolute(p.x, p.y, p.command)
                continue

            if i == 0 or i == len(path.points) - 1:
                result.add_stitch_absolute(p.x, p.y, p.command)
                continue

            prev_pt = None
            next_pt = None
            for j in range(i - 1, -1, -1):
                if path.points[j].command == StitchCommand.STITCH:
                    prev_pt = path.points[j]
                    break
            for j in range(i + 1, len(path.points)):
                if path.points[j].command == StitchCommand.STITCH:
                    next_pt = path.points[j]
                    break

            if prev_pt is None or next_pt is None:
                result.add_stitch_absolute(p.x, p.y, p.command)
                continue

            dx = next_pt.x - prev_pt.x
            dy = next_pt.y - prev_pt.y
            seg_len = math.sqrt(dx * dx + dy * dy)

            if seg_len < 0.01:
                result.add_stitch_absolute(p.x, p.y, p.command)
                continue

            perp_x = -dy / seg_len
            perp_y = dx / seg_len

            stitch_len = math.sqrt(
                (next_pt.x - p.x) ** 2 + (next_pt.y - p.y) ** 2
            )

            pull_factor = pull * (stitch_len / 12.0)
            push_factor = push * (stitch_len / 12.0)

            if stitch_type == StitchType.SATIN:
                nx, ny = perp_x, perp_y
                comp_x = nx * push_factor
                comp_y = ny * push_factor
            else:
                align_x = dx / seg_len
                align_y = dy / seg_len
                comp_x = align_x * pull_factor + perp_x * push_factor
                comp_y = align_y * pull_factor + perp_y * push_factor

            result.add_stitch_absolute(p.x + comp_x, p.y + comp_y, p.command)

        return result

    def get_compensation(self, fabric: FabricType,
                         stitch_length: float = 4.0) -> Tuple[float, float]:
        """Retorna valores de compensação para um tecido."""
        pull = self.pull_table.get(fabric, 0.3)
        push = self.push_table.get(fabric, 0.2)

        factor = stitch_length / 12.0
        return (pull * factor, push * factor)

    def compute_for_object(self, stitch_type: StitchType,
                           fabric: FabricType,
                           density: float = 0.4) -> Tuple[float, float]:
        """Calcula compensação ideal para um objeto."""
        pull = self.pull_table.get(fabric, 0.3)
        push = self.push_table.get(fabric, 0.2)

        if stitch_type == StitchType.SATIN:
            push *= 1.5
        elif stitch_type in (StitchType.TATAMI, StitchType.FILL):
            pull *= 1.2

        if density > 0.6:
            pull *= 1.1
            push *= 1.1

        return (round(pull, 2), round(push, 2))
