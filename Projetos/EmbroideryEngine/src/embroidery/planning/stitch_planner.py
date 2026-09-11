"""
FASE 11 - Stitch Planner

Pipeline completo: regiões → underlay → costura principal → compensação.
"""

import math
from typing import List, Dict, Optional

from ...core.design.embroidery_design import (
    EmbroideryDesign, EmbroideryObject, StitchType,
    UnderlayType, FabricType, ThreadColor, ThreadPalette,
    MachineProfile
)
from ...core.stitches.stitch_primitives import StitchPoint, StitchPath, StitchCommand

from ..run_engine.run_engine import RunEngine
from ..satin.satin_engine import SatinEngine
from ..tatami.tatami_engine import TatamiEngine
from ..underlay.underlay_engine import UnderlayEngine
from ..compensation.compensation_engine import CompensationEngine


class StitchPlanner:
    """Planejador completo de costura - orquestra todos os motores."""

    def __init__(self, density: float = 0.4, fabric: FabricType = FabricType.COTTON):
        self.density = density
        self.fabric = fabric
        self.run_engine = RunEngine()
        self.satin_engine = SatinEngine()
        self.tatami_engine = TatamiEngine()
        self.underlay_engine = UnderlayEngine()
        self.compensation_engine = CompensationEngine()

    def plan(self, regions: List[Dict],
             scale_mm: float = 0.2,
             canvas_width_mm: float = 200.0,
             canvas_height_mm: float = 200.0) -> EmbroideryDesign:
        """Pipeline: regiões → design de bordado com pontos gerados."""
        design = EmbroideryDesign(
            width_mm=canvas_width_mm,
            height_mm=canvas_height_mm
        )

        palette_threads = []
        for region in regions:
            rgb = region.get('color_rgb', (0, 0, 0))
            thread = ThreadColor(
                name=f"Color_{len(palette_threads)}",
                r=rgb[0], g=rgb[1], b=rgb[2]
            )
            palette_threads.append(thread)

        design.palette = ThreadPalette(name="Auto", threads=palette_threads)

        color_map = {}
        for region in regions:
            rgb = region.get('color_rgb', (0, 0, 0))
            if rgb not in color_map:
                color_map[rgb] = len(color_map)
            region['color_index'] = color_map[rgb]

        for region in regions:
            obj = self._region_to_object(region, scale_mm)
            if obj:
                obj = self._generate_stitches(obj)
                design.objects.append(obj)

        design.recalculate_metadata()
        return design

    def _region_to_object(self, region: Dict, scale_mm: float) -> Optional[EmbroideryObject]:
        """Converte região classificada em EmbroideryObject."""
        contour_mm = region.get('contour_mm', [])
        if len(contour_mm) < 3:
            return None

        stitch_type = region.get('stitch_type', StitchType.FILL)
        color_idx = region.get('color_index', 0)
        rgb = region.get('color_rgb', (0, 0, 0))

        obj = EmbroideryObject(
            name=f"Region_{color_idx}",
            stitch_type=stitch_type,
            color_index=color_idx,
            color=ThreadColor(name="", r=rgb[0], g=rgb[1], b=rgb[2]),
            contour=contour_mm,
            bounds=region.get('bounds_mm', (0, 0, 0, 0)),
            density=self.density,
        )

        obj = self._assign_parameters(obj, region)
        return obj

    def _assign_parameters(self, obj: EmbroideryObject, region: Dict) -> EmbroideryObject:
        """Atribui parâmetros baseado no tipo de costura."""
        if obj.stitch_type == StitchType.SATIN:
            obj.density = self.density * 0.9
            obj.stitch_length = min(12.0, obj.width * 0.8)
            obj.pull_compensation = 0.3
            obj.push_compensation = 0.2
            obj.underlay_type = UnderlayType.ZIGZAG
        elif obj.stitch_type in (StitchType.TATAMI, StitchType.FILL):
            obj.density = self.density
            obj.stitch_length = 12.0
            obj.pull_compensation = 0.2
            obj.push_compensation = 0.15
            obj.underlay_type = UnderlayType.DOUBLE_ZIGZAG
        elif obj.stitch_type == StitchType.TRIPLE_RUN:
            obj.density = 4.0
            obj.stitch_length = 4.0
            obj.pull_compensation = 0.15
            obj.underlay_type = UnderlayType.NONE
        else:
            obj.density = 4.0
            obj.stitch_length = 4.0
            obj.pull_compensation = 0.1
            obj.underlay_type = UnderlayType.NONE

        pull, push = self.compensation_engine.get_compensation(self.fabric, obj.stitch_length)
        obj.pull_compensation = pull
        obj.push_compensation = push
        return obj

    def _generate_stitches(self, obj: EmbroideryObject) -> EmbroideryObject:
        """Gera pontos de costura para um objeto."""
        path = StitchPath()

        if obj.underlay_type != UnderlayType.NONE:
            underlay = self.underlay_engine.generate(
                obj.contour, obj.underlay_type,
                obj.stitch_type, obj.underlay_density
            )
            path.append_path(underlay)

        if obj.stitch_type == StitchType.SATIN:
            main_path = self.satin_engine.generate_from_contour(
                obj.contour, obj.width, obj.direction_angle,
                obj.color_index, obj.density
            )
        elif obj.stitch_type in (StitchType.TATAMI, StitchType.FILL):
            main_path = self.tatami_engine.generate(
                obj.contour, obj.stitch_type, obj.density,
                obj.direction_angle, obj.color_index, obj.holes
            )
        elif obj.stitch_type == StitchType.TRIPLE_RUN:
            main_path = self.run_engine.generate(
                contour=obj.contour, stitch_type=StitchType.TRIPLE_RUN,
                color_index=obj.color_index
            )
        else:
            main_path = self.run_engine.generate(
                contour=obj.contour, stitch_type=StitchType.RUN,
                color_index=obj.color_index
            )

        path.append_path(main_path)

        path = self.compensation_engine.apply(
            path, obj.pull_compensation, obj.push_compensation,
            obj.stitch_type, self.fabric
        )

        obj.generated_stitches = path
        return obj


class DigitizerPipeline:
    """Pipeline completo de digitalização: imagem → design de bordado."""

    def __init__(self, density: float = 0.4, fabric: FabricType = FabricType.COTTON,
                 max_colors: int = 15, scale_mm: float = 0.2):
        self.density = density
        self.fabric = fabric
        self.max_colors = max_colors
        self.scale_mm = scale_mm
        self.planner = StitchPlanner(density=density, fabric=fabric)

    def digitize(self, image_path: str,
                 canvas_width_mm: float = 200.0,
                 canvas_height_mm: float = 200.0) -> EmbroideryDesign:
        """Pipeline completo: imagem → design de bordado."""
        from ...image.segmentation.segmentation_engine import (
            SegmentationEngine, ColorReductionEngine
        )
        from ...image.vectorization.vectorization_engine import VectorizationEngine
        from ..classifier.object_classifier import ObjectClassifier

        pil_image = None
        try:
            from PIL import Image
            pil_image = Image.open(image_path)
        except ImportError:
            raise ImportError("Pillow necessário para carregar imagens")

        color_engine = ColorReductionEngine(max_colors=self.max_colors)
        reduced_image, palette = color_engine.reduce(pil_image)

        seg_engine = SegmentationEngine(min_region_area=50)
        regions = seg_engine.segment(reduced_image, palette)

        vec_engine = VectorizationEngine(scale_mm=self.scale_mm)
        regions_mm = vec_engine.vectorize_all(regions)

        classifier = ObjectClassifier()
        regions_classified = classifier.assign_all(regions_mm)

        design = self.planner.plan(
            regions_classified, self.scale_mm,
            canvas_width_mm, canvas_height_mm
        )

        return design
