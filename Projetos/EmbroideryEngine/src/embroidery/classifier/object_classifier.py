"""
FASE 10 - Object Classifier

Classifica automaticamente o tipo de costura ideal para cada região:
- Narrow + elongada -> SATIN
- Grande area -> TATAMI
- Contorno fino -> RUN
- Detalhes pequenos -> TRIPLE_RUN
"""

import math
from typing import Dict
from ...core.design.embroidery_design import StitchType


class ObjectClassifier:
    """Classifica automaticamente o stitch type de cada região."""

    SATIN_MAX_WIDTH = 12.0
    LARGE_AREA_THRESHOLD = 200.0
    SMALL_AREA_THRESHOLD = 30.0
    HIGH_CIRCULARITY = 0.7

    def classify(self, region: Dict) -> StitchType:
        """Classifica o stitch type ideal para uma região."""
        w = region.get('width_mm', 0)
        h = region.get('height_mm', 0)
        area = region.get('area_mm2', 0)
        perimeter = region.get('perimeter_mm', 0)
        aspect = region.get('aspect_ratio', 1.0)
        circularity = region.get('circularity', 0)

        narrow = min(w, h) < self.SATIN_MAX_WIDTH
        large = area > self.LARGE_AREA_THRESHOLD
        small = area < self.SMALL_AREA_THRESHOLD
        elongated = aspect > 3.0
        roundish = circularity > self.HIGH_CIRCULARITY

        if narrow and elongated:
            return StitchType.SATIN
        elif narrow and not large:
            return StitchType.SATIN
        elif small:
            return StitchType.TRIPLE_RUN
        elif large and not narrow:
            if roundish:
                return StitchType.TATAMI
            else:
                return StitchType.FILL
        elif narrow:
            return StitchType.SATIN
        else:
            return StitchType.TATAMI

    def assign_all(self, regions: list) -> list:
        """Classifica stitch type para todas as regiões."""
        for region in regions:
            region['stitch_type'] = self.classify(region)
        return regions
