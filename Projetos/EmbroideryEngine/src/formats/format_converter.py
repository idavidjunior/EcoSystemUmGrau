"""
FASE 17 - Format Converter via pyembroidery

Exporta EmbroideryDesign para DST, JEF, EXP, VP3 usando pyembroidery.
O pyembroidery lida com a codificação de baixo nível.
"""

import os
from typing import Optional

try:
    import pyembroidery
    HAS_PYEMBROIDERY = True
except ImportError:
    HAS_PYEMBROIDERY = False

from ..core.design.embroidery_design import EmbroideryDesign
from ..core.stitches.stitch_primitives import StitchCommand


SUPPORTED_FORMATS = {
    'dst': 'Tajima DST',
    'jef': 'Janome JEF',
    'exp': 'Melco EXP',
    'vp3': 'Pfaff VP3',
    'pes': 'Brother PES',
    'hus': 'Husqvarna HUS',
    'xxx': 'SWF XXX',
    'sew': 'Juki SEW',
    'shv': 'Husqvarna Viking SHV',
}


class FormatConverter:
    """Converte EmbroideryDesign para formatos de máquina via pyembroidery."""

    def __init__(self):
        if not HAS_PYEMBROIDERY:
            raise ImportError(
                "pyembroidery necessário para conversão. "
                "Instale com: pip install pyembroidery"
            )

    def convert(self, design: EmbroideryDesign, output_path: str,
                fmt: Optional[str] = None) -> str:
        """Converte e salva no formato especificado."""
        if fmt is None:
            ext = os.path.splitext(output_path)[1].lower().lstrip('.')
            fmt = ext

        pattern = self._design_to_pattern(design)
        pyembroidery.write(pattern, output_path)
        return output_path

    def _design_to_pattern(self, design: EmbroideryDesign):
        """Converte EmbroideryDesign para pyembroidery pattern."""
        pattern = pyembroidery.EmbPattern()

        for thread in design.palette.threads:
            pattern.add_thread({
                'name': thread.name,
                'color': (thread.r, thread.g, thread.b),
            })

        cx = design.width_mm / 2
        cy = design.height_mm / 2

        for obj in design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue

            for pt in obj.generated_stitches.points:
                x = pt.x + cx
                y = pt.y + cy

                if pt.command == StitchCommand.STITCH:
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
                elif pt.command == StitchCommand.JUMP:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                elif pt.command == StitchCommand.TRIM:
                    pattern.add_command(pyembroidery.TRIM)
                elif pt.command == StitchCommand.COLOR_CHANGE:
                    pattern.add_command(pyembroidery.COLOR_CHANGE)

        pattern.add_command(pyembroidery.END)
        return pattern

    @staticmethod
    def supported_formats():
        return list(SUPPORTED_FORMATS.keys())
