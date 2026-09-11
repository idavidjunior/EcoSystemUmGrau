"""
FASE 9 - Vectorization Engine

Converte regiões segmentadas em objetos de bordado com geometria vetorial.
"""

import math
from typing import List, Tuple, Dict


class VectorizationEngine:
    """Converte regiões de pixels em objetos vetoriais de bordado."""

    def __init__(self, scale_mm: float = 0.2, simplify_tolerance: float = 1.0):
        self.scale_mm = scale_mm
        self.simplify_tolerance = simplify_tolerance

    def vectorize_region(self, region: Dict) -> Dict:
        """Converte uma região segmentada em objeto vetorial."""
        contour = region['contour']
        if not contour:
            return region

        scaled_contour = [
            (x * self.scale_mm, y * self.scale_mm)
            for x, y in contour
        ]

        min_x = min(p[0] for p in scaled_contour)
        min_y = min(p[1] for p in scaled_contour)
        max_x = max(p[0] for p in scaled_contour)
        max_y = max(p[1] for p in scaled_contour)

        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        centered = [(p[0] - cx, p[1] - cy) for p in scaled_contour]

        region['contour_mm'] = centered
        region['bounds_mm'] = (min_x - cx, min_y - cy, max_x - cx, max_y - cy)
        region['width_mm'] = max_x - min_x
        region['height_mm'] = max_y - min_y
        region['perimeter_mm'] = self._perimeter(centered)
        region['area_mm2'] = self._shoelace_area(centered)

        return region

    def vectorize_all(self, regions: List[Dict]) -> List[Dict]:
        """Vetoriza todas as regiões."""
        return [self.vectorize_region(r) for r in regions if r.get('contour')]

    def classify_narrow(self, region: Dict, max_satin_width: float = 12.0) -> bool:
        """Verifica se a região é estreita o suficiente para satin."""
        w = region.get('width_mm', 0)
        h = region.get('height_mm', 0)
        return min(w, h) < max_satin_width

    def _perimeter(self, contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 2:
            return 0.0
        total = 0.0
        for i in range(len(contour)):
            j = (i + 1) % len(contour)
            dx = contour[j][0] - contour[i][0]
            dy = contour[j][1] - contour[i][1]
            total += math.sqrt(dx * dx + dy * dy)
        return total

    def _shoelace_area(self, contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 3:
            return 0.0
        area = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            area += contour[i][0] * contour[j][1]
            area -= contour[j][0] * contour[i][1]
        return abs(area) / 2.0
