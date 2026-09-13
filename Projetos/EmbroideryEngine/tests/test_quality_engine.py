"""
Unit tests for Quality Engine with Machine Limits integration.

Tests:
- Machine limits validation (max stitches, colors, dimensions)
- Stitch length checks (min/max from machine config)
- Jump distance checks (from machine config)
- Design dimension validation against hoop size
- Score calculation with machine limits
"""

import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.quality.quality_engine import QualityEngine, QualityIssue
from src.core.design.embroidery_design import (
    EmbroideryDesign, EmbroideryObject, ThreadColor, StitchType, FabricType
)
from src.core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand


def create_test_design() -> EmbroideryDesign:
    """Create a basic valid test design."""
    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)

    obj = EmbroideryObject(
        name="Square",
        contour=[(0, 0), (50, 0), (50, 50), (0, 50)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI,
        density=0.4
    )

    # Generate some stitches
    path = StitchPath()
    for x in range(0, 51, 5):
        for y in range(0, 51, 5):
            path.add_stitch_absolute(x, y, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)
    return design


def test_quality_engine_default_machine():
    """Test QualityEngine with default machine (generic)."""
    qe = QualityEngine()  # Uses default "generic"
    design = create_test_design()

    report = qe.analyze(design)

    assert report["machine"] == "Generic Machine"
    assert report["format"] == "pes"
    assert report["total_issues"] >= 0
    assert 0 <= report["score"] <= 100


def test_quality_engine_specific_machine():
    """Test QualityEngine with specific machine profile."""
    qe = QualityEngine("brother_pe800")
    design = create_test_design()

    report = qe.analyze(design)

    assert report["machine"] == "Brother PE800 / Innov-is"
    assert report["format"] == "pes"
    # Brother PE800 has hoop 130x180, max_stitches 500000


def test_max_stitches_limit():
    """Test max stitches validation."""
    qe = QualityEngine("brother_pe800")  # 500k limit

    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)

    # Create object with many stitches
    obj = EmbroideryObject(
        name="ManyStitches",
        contour=[(0, 0), (50, 0), (50, 50), (0, 50)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI,
        density=0.4
    )

    # Create path with > 500k stitches
    path = StitchPath()
    for i in range(600000):
        path.add_stitch_absolute(i * 0.001, 0, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe.analyze(design)

    # Should have ERROR for exceeding max stitches
    machine_errors = [i for i in report["issues"] if i.category == "machine_limits" and i.severity == "error"]
    assert len(machine_errors) > 0
    assert any("excede limite" in str(e) for e in machine_errors)


def test_max_colors_limit():
    """Test max colors validation."""
    qe = QualityEngine("brother_pe800")  # 65 colors max

    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)

    # Add 70 objects with different colors
    for i in range(70):
        obj = EmbroideryObject(
            name=f"Obj{i}",
            contour=[(i * 1.0, 0), (i * 1.0 + 0.5, 0), (i * 1.0 + 0.5, 0.5), (i * 1.0, 0.5)],
            color=ThreadColor(f"Color{i}", r=i % 256, g=(i * 2) % 256, b=(i * 3) % 256),
            color_index=i,
            stitch_type=StitchType.RUN
        )
        path = StitchPath()
        path.add_stitch_absolute(i * 1.0, 0, StitchCommand.STITCH)
        path.add_stitch_absolute(i * 1.0 + 0.5, 0, StitchCommand.STITCH)
        obj.generated_stitches = path
        design.objects.append(obj)

    report = qe.analyze(design)

    # Should have ERROR for exceeding max colors
    machine_errors = [i for i in report["issues"] if i.category == "machine_limits" and i.severity == "error"]
    assert len(machine_errors) > 0
    assert any("cores" in str(e) for e in machine_errors)


def test_design_dimensions_exceed_hoop():
    """Test design dimensions vs hoop size."""
    qe = QualityEngine("brother_pe800")  # Hoop 130x180

    design = EmbroideryDesign(name="Test", width_mm=200, height_mm=200)

    obj = EmbroideryObject(
        name="LargeDesign",
        contour=[(-100, -100), (100, -100), (100, 100), (-100, 100)],  # 200x200
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI
    )
    path = StitchPath()
    path.add_stitch_absolute(0, 0, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe.analyze(design)

    # Should have ERROR for exceeding hoop dimensions
    machine_errors = [i for i in report["issues"] if i.category == "machine_limits" and i.severity == "error"]
    assert len(machine_errors) >= 2  # Width and height
    assert any("Largura" in str(e) for e in machine_errors)
    assert any("Altura" in str(e) for e in machine_errors)


def test_stitch_length_limits_from_machine():
    """Test stitch length validation uses machine config."""
    # Generic: max 12.0, min 0.3
    qe_generic = QualityEngine("generic")

    design = EmbroideryDesign(name="Test", width_mm=50, height_mm=50)

    obj = EmbroideryObject(
        name="LongStitch",
        contour=[(0, 0), (10, 0)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )
    # Stitch longer than 12mm
    path = StitchPath()
    path.add_stitch_absolute(0, 0, StitchCommand.STITCH)
    path.add_stitch_absolute(15, 0, StitchCommand.STITCH)  # 15mm > 12mm max
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe_generic.analyze(design)

    # Should detect long stitch
    length_warnings = [i for i in report["issues"] if i.category == "stitch_length" and "longos" in str(i)]
    assert len(length_warnings) > 0


def test_jump_distance_from_machine():
    """Test jump distance validation uses machine config."""
    qe = QualityEngine("brother_pe800")  # max_jump 12.7mm

    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)

    obj = EmbroideryObject(
        name="LongJump",
        contour=[(0, 0), (10, 0)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )
    # Jump of 20mm > 12.7mm limit
    path = StitchPath()
    path.add_stitch_absolute(0, 0, StitchCommand.STITCH)
    path.add_stitch_absolute(20, 0, StitchCommand.JUMP)  # 20mm jump
    path.add_stitch_absolute(20, 0, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe.analyze(design)

    # Should detect long jump
    jump_issues = [i for i in report["issues"] if i.category == "jump"]
    assert len(jump_issues) > 0
    assert any("20" in str(i) or "longos" in str(i) for i in jump_issues)


def test_short_stitch_detection():
    """Test detection of stitches shorter than minimum."""
    qe = QualityEngine("generic")  # min 0.3mm

    design = EmbroideryDesign(name="Test", width_mm=50, height_mm=50)

    obj = EmbroideryObject(
        name="ShortStitches",
        contour=[(0, 0), (10, 0)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.RUN
    )
    # Many very short stitches
    path = StitchPath()
    x = 0.0
    for i in range(20):
        path.add_stitch_absolute(x, 0, StitchCommand.STITCH)
        x += 0.1  # 0.1mm < 0.3mm min
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe.analyze(design)

    # Should detect short stitches
    short_warnings = [i for i in report["issues"] if i.category == "stitch_length" and "curtos" in str(i)]
    assert len(short_warnings) > 0


def test_density_warnings():
    """Test density warnings (too low or too high)."""
    qe = QualityEngine("generic")

    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)

    # Low density fill
    obj_low = EmbroideryObject(
        name="LowDensity",
        contour=[(0, 0), (50, 0), (50, 50), (0, 50)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI
    )
    path = StitchPath()
    # Very sparse stitches
    for x in range(0, 51, 20):
        for y in range(0, 51, 20):
            path.add_stitch_absolute(x, y, StitchCommand.STITCH)
    obj_low.generated_stitches = path

    design.objects.append(obj_low)

    report = qe.analyze(design)

    density_warnings = [i for i in report["issues"] if i.category == "density" and "baixa" in str(i)]
    assert len(density_warnings) > 0


def test_geometry_self_intersection():
    """Test self-intersection detection."""
    qe = QualityEngine("generic")

    design = EmbroideryDesign(name="Test", width_mm=50, height_mm=50)

    # Figure-8 (self-intersecting)
    obj = EmbroideryObject(
        name="Figure8",
        contour=[(0, 0), (10, 10), (0, 10), (10, 0)],  # Self-intersects
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI
    )
    path = StitchPath()
    path.add_stitch_absolute(0, 0, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)

    report = qe.analyze(design)

    # Should detect self-intersection
    geom_warnings = [i for i in report["issues"] if i.category == "geometry" and "auto-interseção" in str(i)]
    assert len(geom_warnings) > 0


def test_empty_design_critical():
    """Test empty design gets CRITICAL issues."""
    qe = QualityEngine("generic")

    design = EmbroideryDesign(name="Empty")
    report = qe.analyze(design)

    critical = [i for i in report["issues"] if i.severity == "critical"]
    assert len(critical) >= 2  # No objects + no stitches


def test_score_calculation():
    """Test score calculation with various issues."""
    qe = QualityEngine("generic")

    # Good design
    design_good = create_test_design()
    report_good = qe.analyze(design_good)
    assert report_good["score"] > 50  # Should be decent

    # Bad design (no stitches - critical issue)
    design_bad = EmbroideryDesign(name="Bad", width_mm=100, height_mm=100)
    obj = EmbroideryObject(
        name="BadObj",
        contour=[(0, 0), (50, 0), (50, 50), (0, 50)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI
    )
    # No stitches
    obj.generated_stitches = StitchPath()
    design_bad.objects.append(obj)

    report_bad = qe.analyze(design_bad)
    # With 1 critical issue, score = 100 - 25 = 75
    assert report_bad["score"] == 75
    assert report_bad["critical"] > 0


def test_machine_limits_warning_threshold():
    """Test warning at 80% of max stitches."""
    qe = QualityEngine("brother_pe800")  # 500k max

    design = EmbroideryDesign(name="Test", width_mm=100, height_mm=100)
    obj = EmbroideryObject(
        name="NearLimit",
        contour=[(0, 0), (50, 0), (50, 50), (0, 50)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI
    )
    # 450k stitches = 90% of 500k
    path = StitchPath()
    for i in range(450000):
        path.add_stitch_absolute(i * 0.001, 0, StitchCommand.STITCH)
    obj.generated_stitches = path
    design.objects.append(obj)

    report = qe.analyze(design)

    # Should have WARNING for approaching limit
    warnings = [i for i in report["issues"] if i.category == "machine_limits" and i.severity == "warning"]
    assert len(warnings) > 0
    assert any("próximo" in str(w) for w in warnings)


def test_summary_includes_machine_info():
    """Test summary includes machine name and format."""
    qe = QualityEngine("janome_mb7")
    design = create_test_design()
    report = qe.analyze(design)

    summary = qe.summary(report)
    assert "Janome MB-7" in summary
    assert "jef" in summary


def test_different_machine_profiles():
    """Test different machine profiles have different limits."""
    machines_to_test = [
        ("generic", 1000000, 65, 200, 200),
        ("brother_pe800", 500000, 65, 130, 180),
        ("janome_mb7", 500000, 99, 200, 200),
        ("tajima_tme", 2000000, 15, 450, 550),
    ]

    for machine_key, expected_stitches, expected_colors, expected_w, expected_h in machines_to_test:
        qe = QualityEngine(machine_key)
        assert qe.max_stitches == expected_stitches
        assert qe.max_colors == expected_colors
        assert qe.max_width_mm == expected_w
        assert qe.max_height_mm == expected_h


if __name__ == "__main__":
    pytest.main([__file__, "-v"])