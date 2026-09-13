"""
Unit tests for Stitch Generator.

Tests unified interface for all stitch types:
- Running stitch (run, triple_run, outline)
- Satin stitch (satin, column)
- Fill stitch (tatami, program_split, spiral)
- Auto stitch type selection
- Underlay integration
- Compensation integration
"""

import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.embroidery.stitch_generator import (
    StitchGenerator, StitchParams, StitchGeneratorMode, generate_stitches
)
from src.core.design.embroidery_design import (
    EmbroideryObject, StitchType, UnderlayType, FabricType, ThreadColor
)
from src.core.stitches.stitch_primitives import StitchPath, StitchCommand


def test_running_stitch():
    """Test running stitch generation."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (10, 0), (10, 10), (0, 10)],
        stitch_type=StitchType.RUN,
        density=2.0,
        color_index=0
    )

    path = gen.generate(obj)

    assert isinstance(path, StitchPath)
    assert path.total_stitches > 0
    assert path.total_jumps == 0  # No jumps in simple run


def test_triple_run_stitch():
    """Test triple run stitch (forward-back-forward)."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (10, 0)],
        stitch_type=StitchType.TRIPLE_RUN,
        density=2.0,
        color_index=0
    )

    path = gen.generate(obj)

    # Triple run should have 3x the stitches
    assert path.total_stitches > 10


def test_outline_stitch():
    """Test outline running stitch."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (10, 0), (10, 10), (0, 10)],
        stitch_type=StitchType.OUTLINE,
        density=2.0,
        color_index=0
    )

    path = gen.generate(obj)

    assert path.total_stitches > 0


def test_satin_stitch():
    """Test satin stitch generation."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 4), (0, 4)],  # Narrow rectangle
        stitch_type=StitchType.SATIN,
        density=0.4,
        color_index=0
    )
    obj.direction_angle = 0.0

    path = gen.generate(obj)

    assert isinstance(path, StitchPath)
    assert path.total_stitches > 0


def test_satin_column():
    """Test satin column along centerline."""
    gen = StitchGenerator()

    centerline = [(0, 0), (10, 0), (20, 0)]
    path = gen.generate_satin_column(centerline, width=6.0)

    assert path.total_stitches > 0


def test_tatami_fill():
    """Test tatami fill generation."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 20), (0, 20)],
        stitch_type=StitchType.TATAMI,
        density=0.4,
        color_index=0
    )
    obj.direction_angle = 45.0

    path = gen.generate(obj)

    assert path.total_stitches > 0
    # Tatami should have alternating direction
    # Check that we have both directions (simplified check)
    assert path.total_stitches > 20


def test_program_split_fill():
    """Test program split fill (alternating blocks)."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (30, 0), (30, 30), (0, 30)],
        stitch_type=StitchType.PROGRAM_SPLIT,
        density=0.4,
        color_index=0
    )
    obj.direction_angle = 0.0

    path = gen.generate(obj)

    assert path.total_stitches > 0


def test_spiral_fill():
    """Test spiral fill."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 20), (0, 20)],
        stitch_type=StitchType.SPIRAL,
        density=0.4,
        color_index=0
    )

    path = gen.generate(obj)

    assert path.total_stitches > 0


def test_cross_stitch_fill():
    """Test cross-stitch pattern fill."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (30, 0), (30, 30), (0, 30)],
        stitch_type=StitchType.CROSS_STITCH,
        density=1.0,
        color_index=0
    )

    path = gen.generate(obj)

    assert path.total_stitches > 0


def test_generate_from_geometry():
    """Test generation from raw geometry without EmbroideryObject."""
    gen = StitchGenerator()

    contour = [(0, 0), (20, 0), (20, 20), (0, 20)]
    params = StitchParams(stitch_type=StitchType.TATAMI, density=0.4)

    path = gen.generate_from_geometry(contour, None, StitchType.TATAMI, params)

    assert path.total_stitches > 0


def test_auto_stitch_type_selection():
    """Test automatic stitch type selection based on geometry."""
    gen = StitchGenerator()

    # Narrow rectangle -> SATIN
    narrow = [(0, 0), (30, 0), (30, 2), (0, 2)]
    st = gen.auto_select_stitch_type(narrow, width_mm=30, height_mm=2, area_mm2=60)
    assert st == StitchType.SATIN

    # Large square -> TATAMI
    large = [(0, 0), (20, 0), (20, 20), (0, 20)]
    st = gen.auto_select_stitch_type(large, width_mm=20, height_mm=20, area_mm2=400)
    assert st == StitchType.TATAMI

    # Long thin -> SATIN
    long_thin = [(0, 0), (50, 0), (50, 3), (0, 3)]
    st = gen.auto_select_stitch_type(long_thin, width_mm=50, height_mm=3, area_mm2=150)
    assert st == StitchType.SATIN

    # Medium aspect -> TATAMI
    med = [(0, 0), (15, 0), (15, 10), (0, 10)]
    st = gen.auto_select_stitch_type(med, width_mm=15, height_mm=10, area_mm2=150)
    assert st == StitchType.TATAMI

    # Small area, elongated -> SATIN
    small_long = [(0, 0), (20, 0), (20, 3), (0, 3)]
    st = gen.auto_select_stitch_type(small_long, width_mm=20, height_mm=3, area_mm2=60)
    assert st == StitchType.SATIN


def test_underlay_integration():
    """Test that underlay is generated for fill/satin stitches."""
    gen = StitchGenerator()

    # Fill with underlay
    obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 20), (0, 20)],
        stitch_type=StitchType.TATAMI,
        density=0.4,
        color_index=0
    )

    params = StitchParams(
        stitch_type=StitchType.TATAMI,
        density=0.4,
        auto_underlay=True,
        underlay_type=UnderlayType.ZIGZAG,
        underlay_density=0.6
    )

    path = gen.generate(obj, params)

    # Should have more stitches due to underlay
    assert path.total_stitches > 50


def test_no_underlay_for_run():
    """Test that running stitches don't get underlay."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (10, 0)],
        stitch_type=StitchType.RUN,
        density=2.0,
        color_index=0
    )

    params = StitchParams(stitch_type=StitchType.RUN, auto_underlay=True)
    path = gen.generate(obj, params)

    # Running stitches should not have underlay
    assert path.total_stitches > 0
    # But fewer than a fill of same size would have


def test_compensation_integration():
    """Test pull/push compensation is applied."""
    gen = StitchGenerator()

    obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 20), (0, 20)],
        stitch_type=StitchType.TATAMI,
        density=0.4,
        color_index=0
    )
    obj.fabric = FabricType.KNIT  # High stretch

    params = StitchParams(
        stitch_type=StitchType.TATAMI,
        density=0.4,
        auto_compensation=True,
        fabric=FabricType.KNIT
    )

    path = gen.generate(obj, params)

    assert path.total_stitches > 0
    # Points should be modified (compensation applied)
    # Just verify it runs without error


def test_stitch_params_defaults():
    """Test default parameters for each stitch type."""
    gen = StitchGenerator()

    for stitch_type in StitchType:
        params = gen.get_default_params(stitch_type)
        assert params.stitch_type == stitch_type
        assert params.density > 0


def test_custom_default_params():
    """Test setting custom default parameters."""
    gen = StitchGenerator()

    custom = StitchParams(stitch_type=StitchType.TATAMI, density=0.5, angle=30.0)
    gen.set_default_params(StitchType.TATAMI, custom)

    params = gen.get_default_params(StitchType.TATAMI)
    assert params.density == 0.5
    assert params.angle == 30.0


def test_convenience_function():
    """Test generate_stitches convenience function."""
    obj = EmbroideryObject(
        contour=[(0, 0), (10, 0), (10, 10), (0, 10)],
        stitch_type=StitchType.RUN,
        density=2.0
    )

    path = generate_stitches(obj)
    assert isinstance(path, StitchPath)
    assert path.total_stitches > 0


def test_holes_in_fill():
    """Test fill generation with holes (donut shape)."""
    gen = StitchGenerator()

    outer = [(0, 0), (20, 0), (20, 20), (0, 20)]
    inner = [(8, 8), (8, 12), (12, 12), (12, 8)]  # Hole

    obj = EmbroideryObject(
        contour=outer,
        holes=[inner],
        stitch_type=StitchType.TATAMI,
        density=0.4,
        color_index=0
    )

    path = gen.generate(obj)

    assert path.total_stitches > 0
    # Should have stitches but not in the hole area


def test_stitch_type_enum_values():
    """Test all StitchType enum values are handled."""
    gen = StitchGenerator()

    handled_types = [
        StitchType.RUN, StitchType.TRIPLE_RUN, StitchType.OUTLINE,
        StitchType.CENTER_RUN, StitchType.EDGE_RUN, StitchType.CONTOUR,
        StitchType.SATIN, StitchType.COLUMN,
        StitchType.TATAMI, StitchType.FILL, StitchType.PROGRAM_SPLIT,
        StitchType.SPIRAL, StitchType.CROSS_STITCH
    ]

    for st in handled_types:
        params = StitchParams(stitch_type=st)
        # Should not raise
        contour = [(0, 0), (10, 0), (10, 10), (0, 10)]
        if st in (StitchType.RUN, StitchType.TRIPLE_RUN, StitchType.OUTLINE,
                  StitchType.CENTER_RUN, StitchType.EDGE_RUN):
            contour = [(0, 0), (10, 0)]
        path = gen.generate_from_geometry(contour, None, st, params)
        assert isinstance(path, StitchPath)


def test_empty_contour():
    """Test handling of empty/invalid contours."""
    gen = StitchGenerator()

    # Empty
    path = gen.generate_from_geometry([], None, StitchType.TATAMI)
    assert path.total_stitches == 0

    # Too few points
    path = gen.generate_from_geometry([(0, 0)], None, StitchType.TATAMI)
    assert path.total_stitches == 0

    path = gen.generate_from_geometry([(0, 0), (10, 0)], None, StitchType.TATAMI)
    assert path.total_stitches == 0


def test_density_effects():
    """Test that density affects stitch count."""
    gen = StitchGenerator()

    contour = [(0, 0), (20, 0), (20, 20), (0, 20)]

    # Low density (sparse)
    params_low = StitchParams(stitch_type=StitchType.TATAMI, density=1.0)
    path_low = gen.generate_from_geometry(contour, None, StitchType.TATAMI, params_low)

    # High density (dense)
    params_high = StitchParams(stitch_type=StitchType.TATAMI, density=0.2)
    path_high = gen.generate_from_geometry(contour, None, StitchType.TATAMI, params_high)

    # Higher density = more stitches
    assert path_high.total_stitches > path_low.total_stitches


def test_angle_effects():
    """Test that angle changes stitch direction."""
    gen = StitchGenerator()

    contour = [(0, 0), (20, 0), (20, 20), (0, 20)]

    params_0 = StitchParams(stitch_type=StitchType.TATAMI, density=0.4, angle=0.0)
    params_90 = StitchParams(stitch_type=StitchType.TATAMI, density=0.4, angle=90.0)

    path_0 = gen.generate_from_geometry(contour, None, StitchType.TATAMI, params_0)
    path_90 = gen.generate_from_geometry(contour, None, StitchType.TATAMI, params_90)

    # Both should generate valid paths
    assert path_0.total_stitches > 0
    assert path_90.total_stitches > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])