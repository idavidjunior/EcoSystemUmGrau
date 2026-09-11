"""
FASE 15 - PES Encoder

Codifica EmbroideryDesign em formato PES v1.0 (Brother).
Formato nativo Brother - suporta até 65 cores.

Estrutura PES:
  Header PES (#PES0001) →指点 ao PEC
  PEC Header (#PEC) → dados de pontos
  Pontos PEC: formato delta com 1-3 bytes
"""

import struct
import math
from typing import List
from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject, StitchType
from ..core.stitches.stitch_primitives import StitchCommand


class PESEncoder:
    """Codificador PES v1.0."""

    MAGIC_PES = b'#PES'
    MAGIC_PEC = b'#PEC'
    PES_VERSION = 1
    PEC_SCALE = 0.1  # 1 unidade PEC = 0.1mm

    def encode(self, design: EmbroideryDesign, output_path: str):
        """Codifica design em arquivo PES."""
        all_stitches = self._collect_stitches(design)

        pes_header = self._build_pes_header(design)
        pec_data = self._encode_pec(all_stitches, design.width_mm, design.height_mm)

        with open(output_path, 'wb') as f:
            f.write(pes_header)
            pec_offset = len(pes_header) + 8
            f.write(struct.pack('<I', pec_offset))
            f.write(struct.pack('<I', len(pec_data)))
            for _ in range(4):
                f.write(struct.pack('<I', 0))
            f.write(pec_data)

    def _collect_stitches(self, design: EmbroideryDesign) -> List[tuple]:
        """Coleta todos os pontos em ordem de costura."""
        stitches = []
        cx = design.width_mm / 2
        cy = design.height_mm / 2

        for obj in design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue

            for pt in obj.generated_stitches.points:
                x_mm = pt.x + cx
                y_mm = pt.y + cy
                x_pec = int(x_mm / self.PEC_SCALE)
                y_pec = int(y_mm / self.PEC_SCALE)

                if pt.command == StitchCommand.STITCH:
                    stitches.append(('STITCH', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.JUMP:
                    stitches.append(('JUMP', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.TRIM:
                    stitches.append(('TRIM', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.COLOR_CHANGE:
                    stitches.append(('COLOR_CHANGE', x_pec, y_pec, obj.color_index))
                elif pt.command in (StitchCommand.TIE_IN, StitchCommand.TIE_OFF):
                    stitches.append(('STITCH', x_pec, y_pec, obj.color_index))

        return stitches

    def _build_pes_header(self, design: EmbroideryDesign) -> bytes:
        """Escreve cabeçalho PES."""
        buf = bytearray()
        buf.extend(self.MAGIC_PES)
        buf.extend(struct.pack('<H', 1))
        buf.extend(struct.pack('<H', 1))
        buf.extend(b'\x00' * 8)
        buf.extend(struct.pack('<I', 0))
        buf.extend(struct.pack('<I', 0))
        buf.extend(struct.pack('<I', 0))
        buf.extend(struct.pack('<I', len(design.palette.threads)))
        for thread in design.palette.threads[:65]:
            buf.extend(struct.pack('BBB', thread.r, thread.g, thread.b))
        for _ in range(max(0, 65 - len(design.palette.threads))):
            buf.extend(b'\xff\x00\x00')
        return bytes(buf)

    def _encode_pec(self, stitches, width_mm, height_mm) -> bytes:
        """Codifica pontos no formato PEC."""
        buf = bytearray()
        buf.extend(self.MAGIC_PEC)
        buf.extend(b'\x20' * 12)
        buf.extend(b'LA:Embroidery\r')
        buf.extend(struct.pack('BB', 0xFF, 0xFF))
        buf.extend(struct.pack('<HH', 0, 0))
        buf.extend(struct.pack('<HH', 1, 1))
        buf.extend(struct.pack('<HH', int(width_mm * 10), int(height_mm * 10)))
        buf.extend(b'\x20' * 480)

        prev_x = 0
        prev_y = 0

        for stitch_type, x, y, color in stitches:
            dx = x - prev_x
            dy = y - prev_y

            if stitch_type == 'COLOR_CHANGE':
                buf.extend(struct.pack('BB', 0xFE, 0xB0))
                buf.extend(struct.pack('B', color & 0x0F))
            elif stitch_type == 'JUMP':
                buf.extend(self._encode_move(dx, dy))
            elif stitch_type == 'STITCH':
                buf.extend(self._encode_move(dx, dy))
            elif stitch_type == 'TRIM':
                buf.extend(struct.pack('BB', 0xFE, 0xB0))
                buf.extend(struct.pack('B', 0x02))

            prev_x = x
            prev_y = y

        buf.extend(b'\xff')
        while len(buf) % 32 != 0:
            buf.extend(b'\x00')
        return bytes(buf)

    def _encode_move(self, dx, dy) -> bytes:
        """Codifica movimento PEC (delta encoding)."""
        buf = bytearray()
        adx = abs(dx)
        ady = abs(dy)

        if adx <= 40 and ady <= 40:
            byte1 = 0x10 | ((dx >> 4) & 0x0F)
            byte2 = (dx & 0x0F) << 4 | (dy & 0x0F)
            buf.extend(struct.pack('BB', byte1, byte2))
        else:
            byte1 = 0x10 | ((dy >> 8) & 0x07) << 4 | ((dx >> 8) & 0x07)
            buf.extend(struct.pack('BBB', byte1, dx & 0xFF, dy & 0xFF))

        return bytes(buf)


class PESWriter:
    """Convenience wrapper."""

    @staticmethod
    def write(design: EmbroideryDesign, path: str):
        encoder = PESEncoder()
        encoder.encode(design, path)
        return path
