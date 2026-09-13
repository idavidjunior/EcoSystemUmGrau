"""
Unit tests for Path Cleaner.

Tests path cleaning operations: close paths, remove self-intersections,
remove redundant nodes, smooth while preserving corners, fix winding.
"""

import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.image.path_cleaner import PathCleaner, PathCleanConfig, clean_path


def test_close_open_path():
    """Test closing an open path within tolerance."""
    # Square with small 0.5 gap between last and first point
    open_square = [(0, 0), (10, 0), (10, 10), (0, 0.3)]  # Gap of 0.3

    cleaner = PathCleaner(PathCleanConfig(close_tolerance=1.0))
    closed, _ = cleaner.clean(open_square)

    # Should close by making last point == first point (but not duplicate)
    assert len(closed) == 4  # First and last are now same point
    assert closed[0] == closed[-1]  # First equals last (closed)


def test_close_open_path_outside_tolerance():
    """Test path NOT closed when gap exceeds tolerance."""
    open_square = [(0, 0), (10, 0), (10, 10), (0, 10)]  # Gap = 10*sqrt(2) ≈ 14.14

    cleaner = PathCleaner(PathCleanConfig(close_tolerance=1.0))
    closed, _ = cleaner.clean(open_square)

    # Should not close (gap too large)
    assert len(closed) == 4
    assert closed[0] != closed[-1]


def test_remove_duplicate_points():
    """Test removal of consecutive duplicate points."""
    with_dupes = [(0, 0), (0, 0), (10, 0), (10, 0), (10, 10), (10, 10), (0, 10)]

    cleaner = PathCleaner()
    cleaned, _ = cleaner.clean(with_dupes)

    # Should have 4 unique points (no closing duplicate)
    assert len(cleaned) == 4
    # Check no consecutive duplicates
    for i in range(len(cleaned) - 1):
        assert cleaned[i] != cleaned[i + 1]


def test_remove_collinear_points():
    """Test removal of intermediate collinear points."""
    # Straight line with intermediate points - not closed (no duplicate first/last)
    collinear = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 3), (2, 3), (1, 3), (0, 3)]

    cleaner = PathCleaner(PathCleanConfig(remove_collinear=True))
    cleaned, _ = cleaner.clean(collinear)

    # Should reduce to corners only: (0,0), (3,0), (3,3), (0,3)
    assert len(cleaned) == 4
    assert cleaned[0] == (0, 0)
    assert cleaned[1] == (3, 0)
    assert cleaned[2] == (3, 3)
    assert cleaned[3] == (0, 3)


def test_douglas_peucker_simplification():
    """Test Douglas-Peucker simplification."""
    # Zigzag line that can be simplified
    zigzag = [(0, 0), (1, 0.1), (2, 0), (3, -0.1), (4, 0), (5, 0.1), (6, 0)]

    config = PathCleanConfig(simplify_tolerance=0.5)
    cleaner = PathCleaner(config)
    cleaned, _ = cleaner.clean(zigzag)

    # Should significantly reduce points
    assert len(cleaned) < len(zigzag)
    # First and last should be preserved
    assert cleaned[0] == (0, 0)
    assert cleaned[-1] == (6, 0)


def test_corner_preservation():
    """Test that sharp corners are preserved during simplification."""
    # Rectangle with sharp corners - not closed
    rect = [(0, 0), (10, 0), (10, 5), (0, 5)]
    # Add some noise on edges
    noisy = []
    for i, (x, y) in enumerate(rect):
        noisy.append((x, y))
        # Add midpoints with small perturbations
        if i < 3:
            nx, ny = rect[(i + 1) % 4]
            noisy.append((x + 0.1, y))  # Slightly off line

    config = PathCleanConfig(simplify_tolerance=0.5, corner_threshold=0.7)
    cleaner = PathCleaner(config)
    cleaned, _ = cleaner.clean(noisy)

    # Should preserve 4 corners (no duplicate closing)
    assert len(cleaned) == 4


def test_remove_tiny_segments():
    """Test removal of very short segments."""
    tiny_segs = [(0, 0), (0.01, 0), (0.02, 0), (10, 0), (10, 10), (0, 10)]

    config = PathCleanConfig(min_segment_length=0.1)
    cleaner = PathCleaner(config)
    cleaned, _ = cleaner.clean(tiny_segs)

    # Tiny segments at start should be merged
    assert len(cleaned) <= 5  # (0,0), (10,0), (10,10), (0,10), (0,0)


def test_self_intersection_removal():
    """Test handling of self-intersecting paths (figure-8)."""
    figure8 = [(0, 0), (10, 10), (0, 10), (10, 0)]

    cleaner = PathCleaner()
    cleaned, _ = cleaner.clean(figure8)

    # Should return convex hull (fallback for self-intersection)
    assert len(cleaned) >= 3
    # Result should be a simple polygon (no self-intersections)
    assert not has_self_intersection(cleaned)


def has_self_intersection(points):
    """Helper to check for self-intersections."""
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        for k in range(i + 2, n):
            if k == (i - 1) % n:
                continue
            l = (k + 1) % n
            if l == i or l == j:
                continue
            if segments_intersect(points[i], points[j], points[k], points[l]):
                return True
    return False


def segments_intersect(p1, p2, q1, q2):
    """Check if two segments intersect."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = q1
    x4, y4 = q2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return False

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    return 0 < t < 1 and 0 < u < 1


def test_fix_winding_exterior():
    """Test exterior winding correction (should be CCW)."""
    # CW square (negative area)
    cw_square = [(0, 0), (0, 10), (10, 10), (10, 0)]

    config = PathCleanConfig(fix_winding=True)
    cleaner = PathCleaner(config)
    cleaned, _ = cleaner.clean(cw_square)

    # Should be CCW (positive area)
    area = signed_area(cleaned)
    assert area > 0


def test_fix_winding_holes():
    """Test hole winding correction (should be CW)."""
    # CCW exterior
    exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
    # CCW hole (should become CW)
    hole = [(3, 3), (5, 3), (5, 5), (3, 5)]

    config = PathCleanConfig(fix_winding=True)
    cleaner = PathCleaner(config)
    cleaned_ext, cleaned_holes = cleaner.clean(exterior, [hole])

    # Hole should be CW (negative area)
    hole_area = signed_area(cleaned_holes[0])
    assert hole_area < 0


def test_hole_preservation():
    """Test that holes are preserved and cleaned."""
    exterior = [(0, 0), (20, 0), (20, 20), (0, 20)]
    hole = [(8, 8), (8, 12), (12, 12), (12, 8)]
    # Add noise to hole
    noisy_hole = [(8, 8), (8.1, 8), (9, 8.1), (12, 12), (12, 8.1), (12, 8)]

    cleaner = PathCleaner()
    cleaned_ext, cleaned_holes = cleaner.clean(exterior, [noisy_hole])

    assert len(cleaned_holes) == 1
    assert len(cleaned_holes[0]) >= 4
    # Hole should not have duplicate closing point
    assert cleaned_holes[0][0] != cleaned_holes[0][-1] or len(cleaned_holes[0]) == 1


def test_smooth_preserves_corners():
    """Test that smoothing preserves sharp corners."""
    # Simple rectangle with a few points on each edge - not closed
    points = [
        (0, 0), (5, 0), (10, 0),  # Bottom edge
        (10, 5), (10, 10),        # Right edge
        (5, 10), (0, 10),         # Top edge
        (0, 5)                     # Left edge (no closing)
    ]

    # Use light smoothing
    cleaner = PathCleaner(PathCleanConfig(max_iterations=1))
    cleaned, _ = cleaner.clean(points)

    # Should preserve roughly rectangular shape
    assert len(cleaned) >= 4
    # Check that we have points near the corners
    xs = [p[0] for p in cleaned]
    ys = [p[1] for p in cleaned]
    assert max(xs) - min(xs) > 5  # Width preserved
    assert max(ys) - min(ys) > 5  # Height preserved


def test_multi_contour_cleaning():
    """Test cleaning multiple contours at once."""
    contours = [
        [(0, 0), (10, 0), (10, 10), (0, 10)],  # Square (not closed)
        [(20, 20), (30, 20), (30, 30)],  # Triangle (not closed)
        [(0, 0), (0, 0), (5, 0), (5, 5), (0, 5)],  # With duplicates
    ]

    cleaner = PathCleaner()
    cleaned = cleaner.clean_multi(contours)

    assert len(cleaned) == 3
    # All should have unique points (no duplicate closing)
    for c in cleaned:
        if len(c) > 1:
            assert c[0] != c[-1] or len(c) == 1


def test_empty_path():
    """Test handling of empty or invalid paths."""
    cleaner = PathCleaner()

    # Empty
    assert cleaner.clean([]) == ([], [])
    # Single point
    assert cleaner.clean([(0, 0)]) == ([(0, 0)], [])
    # Two points
    assert len(cleaner.clean([(0, 0), (10, 0)])[0]) == 2


def test_convenience_function():
    """Test the clean_path convenience function."""
    result = clean_path([(0, 0), (10, 0), (10, 10), (0, 10)])
    contour, holes = result
    # Should not have duplicate closing point
    assert contour[0] != contour[-1] or len(contour) == 1


def test_config_customization():
    """Test custom configuration."""
    config = PathCleanConfig(
        close_tolerance=5.0,
        simplify_tolerance=2.0,
        corner_threshold=0.5,
        min_segment_length=1.0,
        fix_winding=False,
        remove_duplicates=False
    )
    cleaner = PathCleaner(config)

    assert cleaner.config.close_tolerance == 5.0
    assert cleaner.config.simplify_tolerance == 2.0
    assert cleaner.config.corner_threshold == 0.5


def signed_area(points):
    """Calculate signed area of polygon."""
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1] - points[j][0] * points[i][1]
    return area / 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])