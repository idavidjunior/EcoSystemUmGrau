"""
FASE 18 - Digitizer Pipeline (Pipeline Completo de Digitalização)

Pipeline completo: imagem → segmentação → vetORIZAÇÃO → classificação
→ planejamento → sequenciamento → qualidade → exportação.
"""

from typing import Optional, List

from ..core.design.embroidery_design import (
    EmbroideryDesign, FabricType, MachineProfile
)

from ..image.segmentation.segmentation_engine import (
    SegmentationEngine, ColorReductionEngine
)
from ..image.vectorization.vectorization_engine import VectorizationEngine
from ..embroidery.classifier.object_classifier import ObjectClassifier
from ..embroidery.planning.stitch_planner import StitchPlanner
from ..embroidery.sequencing.sequence_optimizer import SequenceOptimizer
from ..quality.quality_engine import QualityEngine


class DigitizerPipeline:
    """Pipeline completo: imagem → design de bordado otimizado."""

    def __init__(self, density: float = 0.4,
                 fabric: FabricType = FabricType.COTTON,
                 max_colors: int = 15, scale_mm: float = 0.2,
                 machine: Optional[MachineProfile] = None):
        self.density = density
        self.fabric = fabric
        self.max_colors = max_colors
        self.scale_mm = scale_mm
        self.machine = machine or MachineProfile(name="Generic")

    def digitize(self, image_path: str,
                 canvas_width_mm: float = 200.0,
                 canvas_height_mm: float = 200.0) -> EmbroideryDesign:
        """Pipeline completo: imagem → design de bordado."""

        from PIL import Image
        pil_image = Image.open(image_path)

        color_engine = ColorReductionEngine(max_colors=self.max_colors)
        reduced_image, palette = color_engine.reduce(pil_image)

        seg_engine = SegmentationEngine(min_region_area=50)
        regions = seg_engine.segment(reduced_image, palette)

        vec_engine = VectorizationEngine(scale_mm=self.scale_mm)
        regions_mm = vec_engine.vectorize_all(regions)

        classifier = ObjectClassifier()
        regions_classified = classifier.assign_all(regions_mm)

        planner = StitchPlanner(density=self.density, fabric=self.fabric)
        design = planner.plan(
            regions_classified, self.scale_mm,
            canvas_width_mm, canvas_height_mm
        )

        optimizer = SequenceOptimizer()
        design = optimizer.optimize(design)

        return design

    def digitize_and_validate(self, image_path: str,
                              canvas_width_mm: float = 200.0,
                              canvas_height_mm: float = 200.0):
        """Pipeline com validação de qualidade."""
        design = self.digitize(image_path, canvas_width_mm, canvas_height_mm)

        qe = QualityEngine()
        report = qe.analyze(design)

        return design, report

    def digitize_and_export(self, image_path: str, output_path: str,
                            fmt: str = 'pes',
                            canvas_width_mm: float = 200.0,
                            canvas_height_mm: float = 200.0) -> str:
        """Pipeline completo: imagem → arquivo de bordado."""
        design = self.digitize(image_path, canvas_width_mm, canvas_height_mm)

        if fmt == 'pes':
            from ..formats.pes_encoder import PESWriter
            PESWriter.write(design, output_path)
        else:
            from ..formats.format_converter import FormatConverter
            converter = FormatConverter()
            converter.convert(design, output_path, fmt)

        return output_path
