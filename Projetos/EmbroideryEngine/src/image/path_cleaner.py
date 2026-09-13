"""
Path Cleaner - Dedicated path cleaning for embroidery vectorization.

Cleans vector paths from segmentation/vectorization:
- Close open paths
- Remove self-intersections
- Remove redundant/duplicate nodes
- Smooth while preserving corners
- Fix winding order (CCW for exterior, CW for holes)
- Simplify with Douglas-Peucker preserving features
"""

import math
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class PathCleanConfig:
    """Configuration for path cleaning."""
    close_tolerance: float = 1.0          # Distance to consider path closed
    simplify_tolerance: float = 0.5       # Douglas-Peucker epsilon
    corner_threshold: float = 0.7         # cos(angle) for corner detection
    min_segment_length: float = 0.1       # Remove segments shorter than this
    max_iterations: int = 3               # Max smoothing iterations
    fix_winding: bool = True              # Ensure CCW exterior, CW holes
    remove_duplicates: bool = True        # Remove duplicate consecutive points
    remove_collinear: bool = True         # Remove collinear intermediate points


class PathCleaner:
    """Cleans and repairs vector paths for embroidery."""

    def __init__(self, config: Optional[PathCleanConfig] = None):
        self.config = config or PathCleanConfig()

    def clean(self, contour: List[Tuple[float, float]],
              holes: Optional[List[List[Tuple[float, float]]]] = None) -> Tuple[List[Tuple[float, float]], List[List[Tuple[float, float]]]]:
        """
        Full cleaning pipeline for a contour with optional holes.

        Returns: (cleaned_contour, cleaned_holes)
        """
        if not contour or len(contour) < 3:
            return contour, holes or []

        # 1. Remove duplicate consecutive points
        if self.config.remove_duplicates:
            contour = self._remove_duplicates(contour)
            if holes:
                holes = [self._remove_duplicates(h) for h in holes]

        # 2. Close the path if open
        contour = self._close_path(contour)
        if holes:
            holes = [self._close_path(h) for h in holes]

        # 3. Remove self-intersections
        contour = self._remove_self_intersections(contour)
        if holes:
            holes = [self._remove_self_intersections(h) for h in holes]

        # 4. Remove collinear points
        if self.config.remove_collinear:
            contour = self._remove_collinear(contour)
            if holes:
                holes = [self._remove_collinear(h) for h in holes]

        # 5. Simplify with Douglas-Peucker preserving corners
        contour = self._simplify_preserve_corners(contour)
        if holes:
            holes = [self._simplify_preserve_corners(h) for h in holes]

        # 6. Remove tiny segments
        contour = self._remove_tiny_segments(contour)
        if holes:
            holes = [self._remove_tiny_segments(h) for h in holes]

        # 7. Fix winding order
        if self.config.fix_winding:
            contour, holes = self._fix_winding(contour, holes or [])

        # 8. Final smoothing (optional, light)
        contour = self._light_smooth(contour)
        if holes:
            holes = [self._light_smooth(h) for h in holes]

        return contour, holes

    def clean_multi(self, contours: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
        """Clean multiple contours (e.g., from multi-region segmentation)."""
        return [self.clean(c)[0] for c in contours if len(c) >= 3]

    # ============================================================
    # Individual cleaning operations
    # ============================================================

    def _remove_duplicates(self, points: List[Tuple[float, float]],
                           tolerance: float = 1e-6) -> List[Tuple[float, float]]:
        """Remove consecutive duplicate points."""
        if len(points) < 2:
            return points[:]

        result = [points[0]]
        for p in points[1:]:
            dx = p[0] - result[-1][0]
            dy = p[1] - result[-1][1]
            if dx * dx + dy * dy > tolerance * tolerance:
                result.append(p)

        # Check if first and last are duplicates (closed path)
        if len(result) > 2:
            dx = result[0][0] - result[-1][0]
            dy = result[0][1] - result[-1][1]
            if dx * dx + dy * dy <= tolerance * tolerance:
                result.pop()

        return result

    def _close_path(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Close an open path by connecting end to start if close enough."""
        if len(points) < 3:
            return points[:]

        first = points[0]
        last = points[-1]

        dx = first[0] - last[0]
        dy = first[1] - last[1]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= self.config.close_tolerance:
            # Close by ensuring last point equals first
            result = points[:-1] + [first]
            return result

        return points[:]

    def _remove_self_intersections(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove self-intersections by splitting at intersections and keeping outer loop."""
        if len(points) < 4:
            return points[:]

        # Find all intersections
        intersections = []
        n = len(points)

        for i in range(n):
            j = (i + 1) % n
            p1, p2 = points[i], points[j]

            for k in range(i + 2, n):
                # Skip adjacent edges
                if k == (i - 1) % n or k == i or k == j:
                    continue
                l = (k + 1) % n
                if l == i or l == j:
                    continue

                q1, q2 = points[k], points[l]

                intersect = self._segment_intersection(p1, p2, q1, q2)
                if intersect:
                    intersections.append((i, j, k, l, intersect))

        if not intersections:
            return points[:]

        # For simplicity, return the convex hull if intersections found
        # A full implementation would split and reorder loops
        return self._convex_hull(points)

    def _segment_intersection(self, p1: Tuple[float, float], p2: Tuple[float, float],
                              q1: Tuple[float, float], q2: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Check if two segments intersect, return intersection point."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = q1
        x4, y4 = q2

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None  # Parallel

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 < t < 1 and 0 < u < 1:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return (ix, iy)

        return None

    def _convex_hull(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Compute convex hull (fallback for self-intersecting paths)."""
        if len(points) < 3:
            return points[:]

        # Graham scan
        pts = sorted(set(points))

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

    def _remove_collinear(self, points: List[Tuple[float, float]],
                          angle_tolerance: float = 1e-3) -> List[Tuple[float, float]]:
        """Remove intermediate collinear points."""
        if len(points) < 3:
            return points[:]

        result = [points[0]]
        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]

            # Vectors
            v1 = (p1[0] - p0[0], p1[1] - p0[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])

            # Cross product for collinearity
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            len1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
            len2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])

            if len1 > 1e-10 and len2 > 1e-10:
                sin_angle = cross / (len1 * len2)
                if abs(sin_angle) > angle_tolerance:
                    result.append(p1)
            else:
                result.append(p1)

        result.append(points[-1])
        return result

    def _simplify_preserve_corners(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Douglas-Peucker simplification preserving detected corners."""
        if len(points) < 4:
            return points[:]

        # Detect corners
        corners = self._detect_corners(points)
        corner_indices = set()

        for cx, cy in corners:
            idx = min(range(len(points)),
                      key=lambda i: (points[i][0] - cx) ** 2 + (points[i][1] - cy) ** 2)
            corner_indices.add(idx)

        # Recursive DP with corner preservation
        def dp_recursive(start: int, end: int) -> List[Tuple[float, float]]:
            if end <= start + 1:
                return [points[start]]

            # Find furthest point from line start-end
            dmax = 0.0
            index = start + 1

            for i in range(start + 1, end):
                if i in corner_indices:
                    continue
                d = self._point_line_distance(points[i], points[start], points[end])
                if d > dmax:
                    dmax = d
                    index = i

            if dmax > self.config.simplify_tolerance:
                left = dp_recursive(start, index)
                right = dp_recursive(index, end)
                return left + right
            else:
                return [points[start], points[end]]

        # Apply between consecutive corners
        sorted_corners = sorted(corner_indices)
        if not sorted_corners:
            return self._douglas_peucker(points, self.config.simplify_tolerance)

        result = []
        n = len(points)

        for i in range(len(sorted_corners)):
            start = sorted_corners[i]
            end = sorted_corners[(i + 1) % len(sorted_corners)]

            if end > start:
                segment = dp_recursive(start, end)
            else:
                segment = dp_recursive(start, n) + dp_recursive(0, end)

            result.extend(segment[:-1])  # Avoid duplicating corner

        return result

    def _douglas_peucker(self, points: List[Tuple[float, float]],
                         epsilon: float) -> List[Tuple[float, float]]:
        """Standard Douglas-Peucker simplification."""
        if len(points) <= 2:
            return points[:]

        def dp_recursive(start: int, end: int):
            if end <= start + 1:
                return [points[start]]

            dmax = 0.0
            index = start + 1

            for i in range(start + 1, end):
                d = self._point_line_distance(points[i], points[start], points[end])
                if d > dmax:
                    dmax = d
                    index = i

            if dmax > epsilon:
                left = dp_recursive(start, index)
                right = dp_recursive(index, end)
                return left + right
            else:
                return [points[start], points[end]]

        result = dp_recursive(0, len(points) - 1)
        result.append(points[-1])
        return result

    def _remove_tiny_segments(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove segments shorter than min_segment_length."""
        if len(points) < 3:
            return points[:]

        result = [points[0]]
        min_len_sq = self.config.min_segment_length ** 2

        for i in range(1, len(points)):
            dx = points[i][0] - result[-1][0]
            dy = points[i][1] - result[-1][1]
            if dx * dx + dy * dy >= min_len_sq:
                result.append(points[i])

        # Ensure closed path stays closed
        if len(result) >= 3:
            dx = result[0][0] - result[-1][0]
            dy = result[0][1] - result[-1][1]
            if dx * dx + dy * dy <= min_len_sq:
                result[-1] = result[0]

        return result

    def _fix_winding(self, exterior: List[Tuple[float, float]],
                     holes: List[List[Tuple[float, float]]]) -> Tuple[List[Tuple[float, float]], List[List[Tuple[float, float]]]]:
        """Ensure exterior is CCW and holes are CW."""
        if self._signed_area(exterior) < 0:
            exterior = exterior[::-1]

        fixed_holes = []
        for hole in holes:
            if self._signed_area(hole) > 0:
                fixed_holes.append(hole[::-1])
            else:
                fixed_holes.append(hole)

        return exterior, fixed_holes

    def _signed_area(self, points: List[Tuple[float, float]]) -> float:
        """Signed area (positive = CCW)."""
        if len(points) < 3:
            return 0.0

        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1] - points[j][0] * points[i][1]

        return area / 2.0

    def _light_smooth(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Light smoothing preserving corners."""
        if len(points) < 5:
            return points[:]

        corners = self._detect_corners(points)
        corner_indices = set()
        for cx, cy in corners:
            idx = min(range(len(points)),
                      key=lambda i: (points[i][0] - cx) ** 2 + (points[i][1] - cy) ** 2)
            corner_indices.add(idx)

        pts = [list(p) for p in points]
        for _ in range(self.config.max_iterations):
            new_pts = [pts[0]]
            for i in range(1, len(pts) - 1):
                if i in corner_indices:
                    new_pts.append(pts[i])
                else:
                    # Laplacian smoothing
                    x = 0.5 * pts[i][0] + 0.25 * pts[i-1][0] + 0.25 * pts[(i+1) % len(pts)][0]
                    y = 0.5 * pts[i][1] + 0.25 * pts[i-1][1] + 0.25 * pts[(i+1) % len(pts)][1]
                    new_pts.append([x, y])
            new_pts.append(pts[-1])
            pts = new_pts

        return [(p[0], p[1]) for p in pts]

    def _detect_corners(self, points: List[Tuple[float, float]],
                        window: int = 5) -> List[Tuple[float, float]]:
        """Detect corners using k-curvature."""
        if len(points) < window * 2 + 1:
            return []

        corners = []
        n = len(points)

        for i in range(n):
            prev_idx = (i - window) % n
            next_idx = (i + window) % n

            v1 = (points[i][0] - points[prev_idx][0], points[i][1] - points[prev_idx][1])
            v2 = (points[next_idx][0] - points[i][0], points[next_idx][1] - points[i][1])

            norm1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
            norm2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])

            if norm1 > 1e-6 and norm2 > 1e-6:
                cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (norm1 * norm2)
                cos_angle = max(-1.0, min(1.0, cos_angle))

                if cos_angle < self.config.corner_threshold:
                    corners.append(points[i])

        # Filter nearby corners
        return self._filter_nearby_corners(corners)

    def _filter_nearby_corners(self, corners: List[Tuple[float, float]],
                                min_dist: float = 3.0) -> List[Tuple[float, float]]:
        """Filter corners that are too close together."""
        if not corners:
            return []

        filtered = [corners[0]]
        min_dist_sq = min_dist * min_dist

        for c in corners[1:]:
            dx = c[0] - filtered[-1][0]
            dy = c[1] - filtered[-1][1]
            if dx * dx + dy * dy >= min_dist_sq:
                filtered.append(c)

        return filtered

    def _point_line_distance(self, point: Tuple[float, float],
                             line_start: Tuple[float, float],
                             line_end: Tuple[float, float]) -> float:
        """Perpendicular distance from point to line segment."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        return math.sqrt((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2)


# Convenience function
def clean_path(contour: List[Tuple[float, float]],
               holes: Optional[List[List[Tuple[float, float]]]] = None,
               config: Optional[PathCleanConfig] = None) -> Tuple[List[Tuple[float, float]], List[List[Tuple[float, float]]]]:
    """Quick path cleaning with default or custom config."""
    cleaner = PathCleaner(config)
    return cleaner.clean(contour, holes)


if __name__ == "__main__":
    # Quick test
    # Open square with gap
    open_square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    cleaner = PathCleaner()
    closed, _ = cleaner.clean(open_square)
    print(f"Open: {open_square}")
    print(f"Closed: {closed}")
    print(f"Closed? {closed[0] == closed[-1]}")

    # Self-intersecting figure-8
    figure8 = [(0, 0), (10, 10), (0, 10), (10, 0)]
    cleaned, _ = cleaner.clean(figure8)
    print(f"Figure-8: {figure8}")
    print(f"Cleaned: {cleaned}")

    # Path with redundant points
    redundant = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 3), (2, 3), (1, 3), (0, 3)]
    cleaned, _ = cleaner.clean(redundant)
    print(f"Redundant: {redundant}")
    print(f"Cleaned: {cleaned}")