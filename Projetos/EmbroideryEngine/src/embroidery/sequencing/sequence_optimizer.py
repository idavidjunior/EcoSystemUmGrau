"""
FASE 12 - Sequence Optimizer

Otimiza a ordem de costura dos objetos para minimizar:
- Saltos (jumps)
- Cortes (trims)
- Distância total percorrida
- Número de mudanças de cor
"""

import math
from typing import List, Tuple
from ...core.design.embroidery_design import EmbroideryDesign, EmbroideryObject


class SequenceOptimizer:
    """Otimiza sequência de costura do design."""

    def optimize(self, design: EmbroideryDesign) -> EmbroideryDesign:
        """Otimiza a ordem dos objetos no design."""
        if not design.objects:
            return design

        groups = self._group_by_color(design.objects)
        ordered_groups = self._order_color_groups(groups, design)
        optimized = self._optimize_within_groups(ordered_groups)

        design.objects = optimized
        return design

    def _group_by_color(self, objects: List[EmbroideryObject]) -> dict:
        """Agrupa objetos por cor."""
        groups = {}
        for obj in objects:
            ci = obj.color_index
            if ci not in groups:
                groups[ci] = []
            groups[ci].append(obj)
        return groups

    def _order_color_groups(self, groups: dict,
                            design: EmbroideryDesign) -> List[Tuple[int, list]]:
        """Ordena grupos de cor por proximidade (nearest neighbor)."""
        if not groups:
            return []

        color_indices = list(groups.keys())
        ordered = []
        used = set()

        current_idx = color_indices[0]
        ordered.append((current_idx, groups[current_idx]))
        used.add(current_idx)

        while len(used) < len(color_indices):
            best_dist = float('inf')
            best_color = None

            current_center = self._group_center(groups[current_idx])

            for ci in color_indices:
                if ci in used:
                    continue
                center = self._group_center(groups[ci])
                dist = math.sqrt(
                    (current_center[0] - center[0]) ** 2 +
                    (current_center[1] - center[1]) ** 2
                )
                if dist < best_dist:
                    best_dist = dist
                    best_color = ci

            if best_color is not None:
                ordered.append((best_color, groups[best_color]))
                used.add(best_color)
                current_idx = best_color

        return ordered

    def _group_center(self, objects: List[EmbroideryObject]) -> Tuple[float, float]:
        """Centroide médio de um grupo de objetos."""
        cx = 0
        cy = 0
        count = 0
        for obj in objects:
            ox, oy = obj.center
            cx += ox
            cy += oy
            count += 1
        if count == 0:
            return (0, 0)
        return (cx / count, cy / count)

    def _optimize_within_groups(self, ordered_groups: List[Tuple[int, list]]) -> List[EmbroideryObject]:
        """Dentro de cada grupo de cor, ordena por nearest neighbor."""
        result = []
        for color_idx, objects in ordered_groups:
            if not objects:
                continue
            if len(objects) == 1:
                result.extend(objects)
                continue

            sorted_objs = self._tsp_nearest_neighbor(objects)
            result.extend(sorted_objs)

        return result

    def _tsp_nearest_neighbor(self, objects: List[EmbroideryObject]) -> List[EmbroideryObject]:
        """TSP simples por nearest neighbor para ordenar objetos."""
        if not objects:
            return []

        remaining = list(objects)
        ordered = [remaining.pop(0)]

        while remaining:
            current_center = ordered[-1].center
            best_idx = 0
            best_dist = float('inf')

            for i, obj in enumerate(remaining):
                dist = math.sqrt(
                    (current_center[0] - obj.center[0]) ** 2 +
                    (current_center[1] - obj.center[1]) ** 2
                )
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            ordered.append(remaining.pop(best_idx))

        return ordered

    def estimate_improvement(self, design: EmbroideryDesign) -> dict:
        """Estima melhoria com a otimização."""
        if not design.objects:
            return {"total_distance_before": 0, "total_distance_after": 0}

        dist_before = self._total_group_distance(design.objects)

        optimized = self.optimize(design)
        dist_after = self._total_group_distance(optimized.objects)

        return {
            "total_distance_before": dist_before,
            "total_distance_after": dist_after,
            "savings_percent": ((dist_before - dist_after) / max(dist_before, 1)) * 100
        }

    def _total_group_distance(self, objects: List[EmbroideryObject]) -> float:
        """Distância total entre centros de objetos."""
        total = 0
        for i in range(1, len(objects)):
            c1 = objects[i - 1].center
            c2 = objects[i].center
            total += math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
        return total
