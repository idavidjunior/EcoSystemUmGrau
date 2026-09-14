"""
FASE 18 - Digitizer Pipeline (Pipeline Completo de Digitalização)

Pipeline completo: imagem → segmentação → vetORIZAÇÃO → classificação
→ planejamento → sequenciamento → qualidade → exportação.
"""

from typing import Optional, List

from PIL import Image

from ..core.design.embroidery_design import (
    EmbroideryDesign, FabricType, MachineProfile
)

from ..image.segmentation.segmentation_engine import (
    SegmentationEngine, ColorReductionEngine
)
from ..image.vectorization.vectorization_engine import VectorizationEngine
from ..embroidery.classifier.improved_classifier import ImprovedStitchClassifier
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

        pil_image = self._prepare_image(Image.open(image_path))

        color_engine = ColorReductionEngine(max_colors=self.max_colors)
        reduced_image, palette = color_engine.reduce(pil_image)

        seg_engine = SegmentationEngine(min_region_area=50)
        regions = seg_engine.segment(reduced_image, palette)

        vec_engine = VectorizationEngine(scale_mm=self.scale_mm)
        regions_mm = vec_engine.vectorize_all(regions)

        classifier = ImprovedStitchClassifier()
        regions_classified = classifier.assign_all(regions_mm)

        planner = StitchPlanner(density=self.density, fabric=self.fabric)
        design = planner.plan(
            regions_classified, self.scale_mm,
            canvas_width_mm, canvas_height_mm
        )

        optimizer = SequenceOptimizer()
        design = optimizer.optimize(design)

        design = self._filter_noise_objects(design)

        return design

    @staticmethod
    def _prepare_image(image: 'Image.Image') -> 'Image.Image':
        """Normaliza a imagem de entrada para RGB.

        PNGs com canal alfa têm a transparência convertida para fundo branco
        (tecido), padrão dos digitalizadores profissionais.
        """
        has_alpha = image.mode in ('RGBA', 'LA') or (
            image.mode == 'P' and 'transparency' in image.info
        )
        if has_alpha:
            image = image.convert('RGBA')
            background = Image.new('RGBA', image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, image)
        return image.convert('RGB')

    @staticmethod
    def _count_stitches(obj) -> int:
        """Conta comandos STITCH realmente gerados no caminho do objeto."""
        path = getattr(obj, 'generated_stitches', None)
        points = getattr(path, 'points', None)
        if not points:
            return 0
        total = 0
        for pt in points:
            cmd = getattr(pt, 'command', None)
            name = getattr(cmd, 'name', str(cmd)).upper()
            if name == 'STITCH':
                total += 1
        return total

    @staticmethod
    def _filter_noise_objects(design: EmbroideryDesign) -> EmbroideryDesign:
        """Remove objetos-ruído (speckles de antialiasing/recorte ruidoso).

        Mantém objetos com pontos reais acima de um piso absoluto e de uma
        fração do maior objeto — descarta os pontinhos de 1 a 5 pontos que
        deixam a prévia 'embolada', sem prejudicar detalhes legítimos.
        """
        if not design.objects:
            return design

        counts = [DigitizerPipeline._count_stitches(o) for o in design.objects]
        max_count = max(counts)
        if max_count <= 0:
            return design

        # Piso relativo ao maior objeto (0,8%) + piso absoluto (5 pontos)
        min_keep = max(5, int(0.008 * max_count))
        design.objects = [o for o, c in zip(design.objects, counts) if c >= min_keep]
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
