"""
FASE 10 - Object Classifier

Classifica automaticamente o tipo de costura para cada objeto de bordado.
Baseado em: largura, área, proporção, posição, contexto.
"""

import math
from typing import List, Dict, Tuple
from ...core.design.embroidery_design import (
    StitchType, UnderlayType, EmbroideryObject
)


class StitchTypeClassifier:
    """Classificador automático de tipo de costura."""

    SATIN_MAX_WIDTH = 12.0
    TATAMI_MIN_AREA = 200.0
    RUN_MAX_WIDTH = 2.0

    def classify(self, region: Dict) -> StitchType:
        """Classifica o tipo de costura ideal para uma região."""
        w = region.get('width_mm', 0)
        h = region.get('height_mm', 0)
        area = region.get('area_mm2', 0)
        aspect = region.get('aspect_ratio', 1.0)

        min_dim = min(w, h)
        max_dim = max(w, h)

        if min_dim < self.RUN_MAX_WIDTH:
            return StitchType.RUN

        if min_dim < self.SATIN_MAX_WIDTH:
            if aspect > 3.0:
                return StitchType.SATIN
            elif aspect > 1.5:
                return StitchType.SATIN
            else:
                return StitchType.SATIN

        if area > self.TATAMI_MIN_AREA:
            if aspect > 2.0:
                return StitchType.TATAMI
            return StitchType.TATAMI

        return StitchType.FILL

    def assign_parameters(self, obj: EmbroideryObject,
                          region: Dict,
                          density: float = 0.4,
                          fabric: str = "cotton") -> EmbroideryObject:
        """Atribui parâmetros de costura baseado no tipo classificado."""
        stitch_type = obj.stitch_type

        if stitch_type == StitchType.SATIN:
            obj.density = density * 0.9
            obj.stitch_length = min(12.0, obj.width * 0.8)
            obj.pull_compensation = 0.3
            obj.push_compensation = 0.2
            obj.underlay_type = UnderlayType.ZIGZAG
            obj.underlay_density = density * 1.5
        elif stitch_type in (StitchType.TATAMI, StitchType.FILL):
            obj.density = density
            obj.stitch_length = 12.0
            obj.pull_compensation = 0.2
            obj.push_compensation = 0.15
            obj.underlay_type = UnderlayType.DOUBLE_ZIGZAG
            obj.underlay_density = density * 1.2
        elif stitch_type == StitchType.RUN:
            obj.density = 0.0
            obj.stitch_length = 4.0
            obj.pull_compensation = 0.1
            obj.push_compensation = 0.0
            obj.underlay_type = UnderlayType.NONE
        elif stitch_type == StitchType.TRIPLE_RUN:
            obj.density = 0.0
            obj.stitch_length = 4.0
            obj.pull_compensation = 0.15
            obj.push_compensation = 0.0
            obj.underlay_type = UnderlayType.NONE

        obj.min_stitch_length = 0.5
        obj.max_stitch_length = 12.0

        return obj

    def classify_all(self, regions: List[Dict]) -> List[Dict]:
        """Classifica todas as regiões e adiciona stitch_type."""
        for region in regions:
            region['stitch_type'] = self.classify(region)
        return regions
