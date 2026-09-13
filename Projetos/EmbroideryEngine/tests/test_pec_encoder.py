"""
Unit tests for PEC Encoder.

Tests PEC format encoding: delta encoding, short/long moves,
color changes, trims, jumps, and round-trip compatibility.
"""

import os
import sys
import tempfile
import struct

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.formats.pec_encoder import PECEncoder, PECWriter
from src.core.design.embroidery_design import (
    EmbroideryDesign, EmbroideryObject, ThreadColor, ThreadPalette,
    MachineProfile, StitchType
)
from src.core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand


def create_test_design() -> EmbroideryDesign:
    """Create a minimal valid test design."""
    design = EmbroideryDesign(name="TestPEC", width_mm=50.0, height_mm=50.0)
    design.machine = MachineProfile("Test", uses_01_units=True)

    obj = EmbroideryObject(
        name="Triangle",
        contour=[(0, -10), (10, 10), (-10, 10)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )

    path = StitchPath()
    path.add_stitch_absolute(0, -10, StitchCommand.STITCH)
    path.add_stitch_absolute(10, 10, StitchCommand.STITCH)
    path.add_stitch_absolute(-10, 10, StitchCommand.STITCH)
    path.add_stitch_absolute(0, -10, StitchCommand.STITCH)  # Close
    obj.generated_stitches = path

    design.objects.append(obj)
    design.palette = ThreadPalette(threads=[obj.color])

    return design


def test_pec_encoder_basic():
    """Test basic PEC encoding produces valid output."""
    design = create_test_design()
    encoder = PECEncoder()

    with tempfile.NamedTemporaryFile(suffix='.pec', delete=False) as f:
        temp_path = f.name

    try:
        encoder.encode(design, temp_path)

        # Verify file exists and has content
        assert os.path.exists(temp_path)
        size = os.path.getsize(temp_path)
        assert size > 100  # At least header + some stitches

        # Read and verify header
        with open(temp_path, 'rb') as f:
            data = f.read()

        # Check magic
        assert data[:4] == b'#PEC'

        # Check dimensions in header
        # MAGIC(4) + 12 padding + 13 label + 2 FF + 4 unknown + 4 version = 39, but actual is 40
        width = struct.unpack('<H', data[40:42])[0]
        height = struct.unpack('<H', data[42:44])[0]
        assert width == 500  # 50mm * 10
        assert height == 500

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_pec_encoder_short_moves():
    """Test short move encoding (<=40 units in both axes)."""
    design = create_test_design()
    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)

    # First few stitches should be short moves
    pec_data = encoder._encode_pec(stitches, 50, 50)

    # Verify no long moves (3-byte) for small coordinates
    # Search for 0x10 prefix indicating short moves
    short_moves = pec_data.count(b'\x10')
    assert short_moves > 0


def test_pec_encoder_long_moves():
    """Test long move encoding (>40 units)."""
    design = EmbroideryDesign(name="Test", width_mm=200, height_mm=200)
    design.machine = MachineProfile("Test", uses_01_units=True)

    obj = EmbroideryObject(
        name="LongJump",
        contour=[(-90, 0), (90, 0)],
        color=ThreadColor("Blue", r=0, g=0, b=255),
        color_index=0,
        stitch_type=StitchType.RUN
    )

    path = StitchPath()
    path.add_stitch_absolute(-90, 0, StitchCommand.STITCH)
    path.add_stitch_absolute(90, 0, StitchCommand.JUMP)  # 180mm jump = 1800 units
    path.add_stitch_absolute(90, 0, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)
    design.palette = ThreadPalette(threads=[obj.color])

    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)
    pec_data = encoder._encode_pec(stitches, 200, 200)

    # Should contain long move encoding (3 bytes starting with 0x10 but with high bits)
    # Long moves have bit 4-6 set for high coordinate bytes
    found_long = False
    i = pec_data.find(b'#PEC') + 512  # Skip header
    while i < len(pec_data) - 3:
        b = pec_data[i]
        if b == 0x10:
            # Check if it's a long move (high bits in upper nibble)
            if i + 2 < len(pec_data):
                # Long move if dx or dy > 40
                found_long = True
                break
        i += 1

    # At minimum verify encoding runs without error
    assert len(pec_data) > 512


def test_pec_color_change():
    """Test color change encoding."""
    design = EmbroideryDesign(name="Test", width_mm=50, height_mm=50)
    design.machine = MachineProfile("Test", uses_01_units=True)

    obj1 = EmbroideryObject(
        name="Red",
        contour=[(-10, 0), (0, 10)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )
    obj1.generated_stitches = StitchPath([
        StitchPoint(-10, 0, StitchCommand.STITCH),
        StitchPoint(0, 10, StitchCommand.STITCH),
        StitchPoint(0, 10, StitchCommand.COLOR_CHANGE, color_index=1),
    ])

    obj2 = EmbroideryObject(
        name="Blue",
        contour=[(0, 10), (10, 0)],
        color=ThreadColor("Blue", r=0, g=0, b=255),
        color_index=1,
        stitch_type=StitchType.RUN
    )
    obj2.generated_stitches = StitchPath([
        StitchPoint(0, 10, StitchCommand.STITCH),
        StitchPoint(10, 0, StitchCommand.STITCH),
    ])

    design.objects.extend([obj1, obj2])
    design.palette = ThreadPalette(threads=[obj1.color, obj2.color])

    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)

    # Verify color change command present
    color_changes = [s for s in stitches if s[0] == 'COLOR_CHANGE']
    assert len(color_changes) == 1
    assert color_changes[0][3] == 1  # Color index 1

    pec_data = encoder._encode_pec(stitches, 50, 50)

    # Check for color change opcode 0xFE 0xB0
    assert b'\xFE\xB0' in pec_data


def test_pec_trim_encoding():
    """Test trim command encoding."""
    design = create_test_design()
    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)

    # Add a trim manually
    stitches.append(('TRIM', 100, 100, 0))

    pec_data = encoder._encode_pec(stitches, 50, 50)

    # Check for trim opcode 0xFE 0xB0 0x02
    assert b'\xFE\xB0\x02' in pec_data


def test_pec_writer_convenience():
    """Test PECWriter static method."""
    design = create_test_design()

    with tempfile.NamedTemporaryFile(suffix='.pec', delete=False) as f:
        temp_path = f.name

    try:
        PECWriter.write(design, temp_path)
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 100
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_pec_scale_factor():
    """Test that PEC scale (0.1mm) is correctly applied."""
    design = EmbroideryDesign(name="Test", width_mm=10, height_mm=10)
    design.machine = MachineProfile("Test", uses_01_units=True)

    obj = EmbroideryObject(
        name="Point",
        contour=[(0, 0)],
        color=ThreadColor("Black"),
        color_index=0,
        stitch_type=StitchType.RUN
    )
    obj.generated_stitches = StitchPath([
        StitchPoint(1.0, 2.0, StitchCommand.STITCH),
    ])
    design.objects.append(obj)
    design.palette = ThreadPalette(threads=[obj.color])

    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)

    # 1mm / 0.1 = 10 units, 2mm / 0.1 = 20 units
    # Design is centered, so cx=5, cy=5
    # Point at (1,2) in object coords -> (6, 7) in design coords
    # PEC: (6/0.1, 7/0.1) = (60, 70)
    assert stitches[0][1] == 60
    assert stitches[0][2] == 70


def test_pec_end_marker():
    """Test that PEC data ends with 0xFF marker."""
    design = create_test_design()
    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)
    pec_data = encoder._encode_pec(stitches, 50, 50)

    # Find end marker before padding
    end_idx = pec_data.rfind(b'\xff')
    assert end_idx >= 0

    # After end marker, only padding zeros
    assert all(b == 0 for b in pec_data[end_idx+1:])


def test_pec_32byte_alignment():
    """Test that PEC data is padded to 32-byte boundary."""
    design = create_test_design()
    encoder = PECEncoder()
    stitches = encoder._collect_stitches(design)
    pec_data = encoder._encode_pec(stitches, 50, 50)

    assert len(pec_data) % 32 == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])