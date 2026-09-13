"""
PEC Encoder - Brother PEC Stitch Data Format

PEC is the actual stitch data format embedded in PES files.
This encoder writes standalone .pec files (stitch data only, no PES header).
Used by older Brother machines and for testing PEC encoding in isolation.

Format: Delta-encoded coordinates with command bytes.
Scale: 1 unit = 0.1mm (same as PEC in PES).
"""

import struct
from typing import List, Tuple
from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject, StitchType
from ..core.stitches.stitch_primitives import StitchCommand


class PECEncoder:
    """Encodes EmbroideryDesign to standalone PEC format (stitch data only)."""

    MAGIC = b'#PEC'
    SCALE = 0.1  # 1 unit = 0.1mm

    def encode(self, design: EmbroideryDesign, output_path: str):
        """Encode design to .pec file."""
        all_stitches = self._collect_stitches(design)
        pec_data = self._encode_pec(all_stitches, design.width_mm, design.height_mm)

        with open(output_path, 'wb') as f:
            f.write(pec_data)

    def _collect_stitches(self, design: EmbroideryDesign) -> List[tuple]:
        """Collect all stitches in sewing order."""
        stitches = []
        cx = design.width_mm / 2
        cy = design.height_mm / 2

        for obj in design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue

            for pt in obj.generated_stitches.points:
                x_mm = pt.x + cx
                y_mm = pt.y + cy
                x_pec = int(round(x_mm / self.SCALE))
                y_pec = int(round(y_mm / self.SCALE))

                # Use point's color_index if available (for COLOR_CHANGE), else object's
                pt_color = getattr(pt, 'color_index', obj.color_index)

                if pt.command == StitchCommand.STITCH:
                    stitches.append(('STITCH', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.JUMP:
                    stitches.append(('JUMP', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.TRIM:
                    stitches.append(('TRIM', x_pec, y_pec, obj.color_index))
                elif pt.command == StitchCommand.COLOR_CHANGE:
                    stitches.append(('COLOR_CHANGE', x_pec, y_pec, pt_color))
                elif pt.command in (StitchCommand.TIE_IN, StitchCommand.TIE_OFF):
                    stitches.append(('STITCH', x_pec, y_pec, obj.color_index))

        return stitches

    def _encode_pec(self, stitches: List[tuple], width_mm: float, height_mm: float) -> bytes:
        """Encode stitches to PEC binary format."""
        buf = bytearray()
        buf.extend(self.MAGIC)
        buf.extend(b'\x20' * 12)  # Padding
        buf.extend(b'LA:Embroidery\r')  # Label
        buf.extend(struct.pack('BB', 0xFF, 0xFF))  # End of header marker
        buf.extend(struct.pack('<HH', 0, 0))  # Unknown
        buf.extend(struct.pack('<HH', 1, 1))  # Version
        buf.extend(struct.pack('<HH', int(width_mm * 10), int(height_mm * 10)))  # Dimensions in 0.1mm
        buf.extend(b'\x20' * 480)  # Padding to 512 bytes

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

        # End marker
        buf.extend(b'\xff')

        # Pad to 32-byte boundary
        while len(buf) % 32 != 0:
            buf.extend(b'\x00')

        return bytes(buf)

    def _encode_move(self, dx: int, dy: int) -> bytes:
        """Encode PEC move (delta encoding: 2 bytes short, 3 bytes long)."""
        buf = bytearray()
        adx = abs(dx)
        ady = abs(dy)

        if adx <= 40 and ady <= 40:
            # Short move: 2 bytes
            # byte1: 0x10 | ((dx >> 4) & 0x0F)
            # byte2: (dx & 0x0F) << 4 | (dy & 0x0F)
            byte1 = 0x10 | ((dx >> 4) & 0x0F)
            byte2 = ((dx & 0x0F) << 4) | (dy & 0x0F)
            buf.extend(struct.pack('BB', byte1, byte2))
        else:
            # Long move: 3 bytes
            # byte1: 0x10 | ((dy >> 8) & 0x07) << 4 | ((dx >> 8) & 0x07)
            # byte2: dx & 0xFF
            # byte3: dy & 0xFF
            byte1 = 0x10 | (((dy >> 8) & 0x07) << 4) | ((dx >> 8) & 0x07)
            buf.extend(struct.pack('BBB', byte1, dx & 0xFF, dy & 0xFF))

        return bytes(buf)


class PECWriter:
    """Convenience wrapper for PEC encoding."""

    @staticmethod
    def write(design: EmbroideryDesign, path: str):
        encoder = PECEncoder()
        encoder.encode(design, path)
        return path


# Standalone test
if __name__ == "__main__":
    # Quick self-test
    from ..core.design.embroidery_design import (
        EmbroideryDesign, EmbroideryObject, ThreadColor, ThreadPalette,
        MachineProfile, StitchType, FabricType
    )
    from ..core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand

    # Create minimal test design
    design = EmbroideryDesign(name="Test", width_mm=50, height_mm=50)
    design.machine = MachineProfile("Test", uses_01_units=True)

    # Simple square contour
    obj = EmbroideryObject(
        name="Square",
        contour=[(-10, -10), (10, -10), (10, 10), (-10, 10)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )

    # Generate simple run stitches
    path = StitchPath()
    for x, y in obj.contour:
        path.add_stitch_absolute(x, y, StitchCommand.STITCH)
    path.add_stitch_absolute(-10, -10, StitchCommand.STITCH)  # Close
    obj.generated_stitches = path

    design.objects.append(obj)
    design.palette = ThreadPalette(threads=[obj.color])

    # Test encoding
    PECWriter.write(design, "test_output.pec")
    print("PEC test written to test_output.pec")