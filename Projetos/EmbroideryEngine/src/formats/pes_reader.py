"""
PES Reader - Brother PES Format Reader

Reads .pes files and extracts stitch data for validation and round-trip testing.
Supports PES v1.0 format with embedded PEC stitch data.
"""

import struct
from typing import List, Tuple, Optional
from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject, ThreadColor, ThreadPalette, MachineProfile, StitchType
from ..core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand


class PESReader:
    """Reads PES v1.0 files and reconstructs stitch data."""

    MAGIC_PES = b'#PES'
    MAGIC_PEC = b'#PEC'
    SCALE = 0.1  # 1 unit = 0.1mm

    def read(self, file_path: str) -> EmbroideryDesign:
        """Read PES file and return EmbroideryDesign."""
        with open(file_path, 'rb') as f:
            data = f.read()

        # Parse PES header
        design = self._parse_pes_header(data)

        # Find and parse PEC data
        pec_offset = self._find_pec_offset(data)
        if pec_offset >= 0:
            pec_data = data[pec_offset:]
            stitches = self._decode_pec(pec_data)
            self._apply_stitches_to_design(design, stitches)

        return design

    def _parse_pes_header(self, data: bytes) -> EmbroideryDesign:
        """Parse PES header to get metadata."""
        design = EmbroideryDesign(name="Imported")
        design.machine = MachineProfile("Brother", uses_01_units=True)

        if len(data) < 4 or data[:4] != self.MAGIC_PES:
            raise ValueError("Not a valid PES file")

        # PES header structure (simplified)
        # Offset 4: version (2 bytes)
        # Offset 6: version (2 bytes)
        # Offset 8-15: reserved (8 bytes)
        # Offset 16: hoop info (4 bytes)
        # Offset 20: hoop info (4 bytes)
        # Offset 24: reserved (4 bytes)
        # Offset 28: color count (4 bytes)
        # Offset 32+: color palette (3 bytes per color * 65)

        if len(data) >= 32:
            color_count = struct.unpack('<I', data[28:32])[0]
            palette = ThreadPalette()

            for i in range(min(color_count, 65)):
                offset = 32 + i * 3
                if offset + 3 <= len(data):
                    r, g, b = struct.unpack('BBB', data[offset:offset+3])
                    if r != 0xFF or g != 0x00 or b != 0x00:  # Skip placeholder
                        palette.threads.append(ThreadColor(f"Color{i}", r=r, g=g, b=b))

            design.palette = palette

        return design

    def _find_pec_offset(self, data: bytes) -> int:
        """Find PEC data offset in file."""
        # In PES v1, PEC offset is stored at offset 36-39
        if len(data) >= 40:
            offset = struct.unpack('<I', data[36:40])[0]
            if offset < len(data) and data[offset:offset+4] == self.MAGIC_PEC:
                return offset

        # Fallback: search for #PEC magic
        idx = data.find(self.MAGIC_PEC)
        return idx if idx >= 0 else -1

    def _decode_pec(self, pec_data: bytes) -> List[Tuple[str, int, int, int]]:
        """Decode PEC stitch data."""
        if len(pec_data) < 4 or pec_data[:4] != self.MAGIC_PEC:
            raise ValueError("Not a valid PEC data block")

        stitches = []
        pos = 512  # Skip PEC header (512 bytes)

        prev_x = 0
        prev_y = 0

        while pos < len(pec_data):
            if pos >= len(pec_data):
                break

            byte = pec_data[pos]

            if byte == 0xFF:  # End marker
                break

            if byte == 0xFE:  # Command (color change, trim)
                if pos + 2 < len(pec_data):
                    cmd = pec_data[pos + 1]
                    if cmd == 0xB0:  # Color change or trim
                        if pos + 3 < len(pec_data):
                            sub_cmd = pec_data[pos + 2]
                            if sub_cmd == 0x02:  # Trim
                                stitches.append(('TRIM', prev_x, prev_y, 0))
                            else:  # Color change
                                color = sub_cmd & 0x0F
                                stitches.append(('COLOR_CHANGE', prev_x, prev_y, color))
                        pos += 3
                    else:
                        pos += 2
                else:
                    pos += 1
            elif byte & 0xF0 == 0x10:  # Stitch/move command
                # Check if long format (3 bytes) or short (2 bytes)
                # Short: bits 4-7 contain high bits
                high_bits = (byte >> 4) & 0x07
                if high_bits != 0 or (byte & 0x0F) > 8:
                    # Long format (3 bytes)
                    if pos + 2 < len(pec_data):
                        dx = self._decode_delta_long(byte, pec_data[pos+1], pec_data[pos+2])
                        dy = pec_data[pos+2] if False else self._decode_delta_long(byte, pec_data[pos+1], pec_data[pos+2])
                        # Actually need proper decoding
                        dx = pec_data[pos+1]
                        dy = pec_data[pos+2]
                        if dx > 127: dx -= 256
                        if dy > 127: dy -= 256

                        prev_x += dx
                        prev_y += dy

                        # Determine if jump or stitch based on distance
                        dist = (dx*dx + dy*dy)**0.5
                        if dist > 100:  # Large delta = jump
                            stitches.append(('JUMP', prev_x, prev_y, 0))
                        else:
                            stitches.append(('STITCH', prev_x, prev_y, 0))
                        pos += 3
                    else:
                        pos += 1
                else:
                    # Short format (2 bytes)
                    if pos + 1 < len(pec_data):
                        byte1 = byte
                        byte2 = pec_data[pos + 1]

                        dx = ((byte1 & 0x0F) << 4) | (byte2 >> 4)
                        dy = byte2 & 0x0F

                        # Sign extend
                        if dx & 0x80: dx -= 256
                        if dy & 0x80: dy -= 256

                        prev_x += dx
                        prev_y += dy

                        dist = (dx*dx + dy*dy)**0.5
                        if dist > 100:
                            stitches.append(('JUMP', prev_x, prev_y, 0))
                        else:
                            stitches.append(('STITCH', prev_x, prev_y, 0))
                        pos += 2
                    else:
                        pos += 1
            else:
                pos += 1

        return stitches

    def _decode_delta_long(self, byte1: int, byte2: int, byte3: int) -> Tuple[int, int]:
        """Decode long format delta (3 bytes)."""
        dx = byte2
        dy = byte3
        if byte1 & 0x80: dx -= 256
        if byte1 & 0x40: dy -= 256
        return dx, dy

    def _apply_stitches_to_design(self, design: EmbroideryDesign, stitches: List[Tuple[str, int, int, int]]):
        """Apply decoded stitches to design objects."""
        # Group stitches by color
        color_groups = {}
        for stype, x, y, color in stitches:
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append((stype, x, y))

        # Create objects for each color
        for color_idx, stitch_list in color_groups.items():
            obj = EmbroideryObject(
                name=f"Color_{color_idx}",
                color_index=color_idx,
                stitch_type=StitchType.RUN
            )
            path = StitchPath()
            for stype, x, y in stitch_list:
                x_mm = x * self.SCALE
                y_mm = y * self.SCALE
                if stype == 'STITCH':
                    path.add_stitch_absolute(x_mm, y_mm, StitchCommand.STITCH)
                elif stype == 'JUMP':
                    path.add_stitch_absolute(x_mm, y_mm, StitchCommand.JUMP)
                elif stype == 'TRIM':
                    path.add_stitch_absolute(x_mm, y_mm, StitchCommand.TRIM)
                elif stype == 'COLOR_CHANGE':
                    path.add_stitch_absolute(x_mm, y_mm, StitchCommand.COLOR_CHANGE, color_index=color_idx)
            obj.generated_stitches = path
            design.objects.append(obj)


def read_pes(file_path: str) -> EmbroideryDesign:
    """Convenience function to read PES file."""
    reader = PESReader()
    return reader.read(file_path)


if __name__ == "__main__":
    # Test with a generated PES file
    import sys
    if len(sys.argv) > 1:
        design = read_pes(sys.argv[1])
        print(f"Design: {design.name}")
        print(f"Objects: {len(design.objects)}")
        print(f"Colors: {design.total_colors}")
        print(f"Stitches: {design.total_stitches}")
        for obj in design.objects:
            print(f"  {obj.name}: {obj.total_stitches} stitches")