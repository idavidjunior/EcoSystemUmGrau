"""
Stitch Generator - Unified interface for all stitch types.

Provides a single entry point for generating embroidery stitches:
- Running stitch (run, triple_run, outline, center_run, edge_run)
- Satin stitch (satin, column)
- Fill stitch (tatami, fill, program_split, spiral, cross_stitch)
- Underlay generation
- Automatic stitch type selection based on geometry
"""

import math
from typing import List, Tuple, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

from ..core.design.embroidery_design import (
    EmbroideryObject, StitchType, UnderlayType, FabricType
)
from ..core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand
from .tatami.tatami_engine import TatamiEngine
from .satin.satin_engine import SatinEngine
from .run_engine.run_engine import RunEngine
from .underlay.underlay_engine import UnderlayEngine
from .compensation.compensation_engine import CompensationEngine
from ..image.path_cleaner import PathCleaner, PathCleanConfig


class StitchGeneratorMode(Enum):
    """Generation mode."""
    AUTO = "auto"          # Auto-select based on geometry
    RUN = "run"            # Force running stitch
    SATIN = "satin"        # Force satin stitch
    FILL = "fill"          # Force fill stitch (tatami)
    UNDERLAY_ONLY = "underlay_only"


@dataclass
class StitchParams:
    """Parameters for stitch generation."""
    stitch_type: StitchType = StitchType.FILL
    density: float = 0.4           # mm between stitches/rows
    stitch_length: float = 4.0     # Max stitch length (mm)
    min_stitch_length: float = 0.5 # Min stitch length (mm)
    max_stitch_length: float = 12.0 # Max stitch length (mm)
    angle: float = 0.0             # Fill angle (degrees)
    underlay_type: UnderlayType = UnderlayType.ZIGZAG
    underlay_density: float = 0.6  # Underlay density (mm)
    pull_compensation: float = 0.0 # Pull compensation (mm)
    push_compensation: float = 0.0 # Push compensation (mm)
    fabric: FabricType = FabricType.COTTON
    color_index: int = 0
    auto_underlay: bool = True
    auto_compensation: bool = True


class StitchGenerator:
    """
    Unified stitch generator - single interface for all stitch types.

    Usage:
        generator = StitchGenerator()
        path = generator.generate(object, params)

    Or for manual geometry:
        path = generator.generate_from_geometry(
            contour, holes, stitch_type, params
        )
    """

    def __init__(self):
        self.tatami = TatamiEngine()
        self.satin = SatinEngine()
        self.run = RunEngine()
        self.underlay = UnderlayEngine()
        self.compensation = CompensationEngine()
        self.path_cleaner = PathCleaner()

        # Default parameters by stitch type
        self._defaults = {
            StitchType.RUN: StitchParams(stitch_type=StitchType.RUN, density=2.0),
            StitchType.TRIPLE_RUN: StitchParams(stitch_type=StitchType.TRIPLE_RUN, density=2.0),
            StitchType.OUTLINE: StitchParams(stitch_type=StitchType.OUTLINE, density=2.0),
            StitchType.CENTER_RUN: StitchParams(stitch_type=StitchType.CENTER_RUN, density=2.0),
            StitchType.EDGE_RUN: StitchParams(stitch_type=StitchType.EDGE_RUN, density=2.0),
            StitchType.SATIN: StitchParams(stitch_type=StitchType.SATIN, density=0.4, angle=0.0),
            StitchType.COLUMN: StitchParams(stitch_type=StitchType.COLUMN, density=0.4, angle=0.0),
            StitchType.TATAMI: StitchParams(stitch_type=StitchType.TATAMI, density=0.4, angle=0.0),
            StitchType.FILL: StitchParams(stitch_type=StitchType.FILL, density=0.4, angle=0.0),
            StitchType.PROGRAM_SPLIT: StitchParams(stitch_type=StitchType.PROGRAM_SPLIT, density=0.4, angle=0.0),
            StitchType.SPIRAL: StitchParams(stitch_type=StitchType.SPIRAL, density=0.4),
            StitchType.CROSS_STITCH: StitchParams(stitch_type=StitchType.CROSS_STITCH, density=1.0),
            StitchType.CONTOUR: StitchParams(stitch_type=StitchType.CONTOUR, density=2.0),
        }

    def generate(self, obj: EmbroideryObject,
                 params: Optional[StitchParams] = None) -> StitchPath:
        """
        Generate stitches for an EmbroideryObject.

        Uses object's contour, holes, and properties.
        params overrides object properties if provided.
        """
        if not obj.contour:
            return StitchPath()

        # Run stitches only need 2 points (a line), others need 3+ (polygon)
        min_points = 2 if obj.stitch_type in (StitchType.RUN, StitchType.TRIPLE_RUN,
                                               StitchType.CENTER_RUN, StitchType.EDGE_RUN,
                                               StitchType.OUTLINE, StitchType.CONTOUR) else 3
        if len(obj.contour) < min_points:
            return StitchPath()

        # Merge params with object properties
        effective_params = self._merge_params(obj, params)

        # Clean contour and holes
        clean_contour, clean_holes = self.path_cleaner.clean(obj.contour, obj.holes)

        # Generate main stitches
        main_path = self._generate_by_type(
            clean_contour, clean_holes, effective_params
        )

        # Generate underlay if enabled
        if effective_params.auto_underlay and self._needs_underlay(effective_params.stitch_type):
            underlay_path = self._generate_underlay(
                clean_contour, clean_holes, effective_params
            )
            # Combine underlay + main
            combined = StitchPath()
            combined.points = underlay_path.points + main_path.points
            main_path = combined

        # Apply compensation if enabled
        if effective_params.auto_compensation:
            pull, push = self.compensation.compute_for_object(
                effective_params.stitch_type,
                effective_params.fabric,
                effective_params.density
            )
            main_path = self.compensation.apply(
                main_path, pull, push,
                effective_params.stitch_type,
                effective_params.fabric
            )

        return main_path

    def generate_from_geometry(self,
                               contour: List[Tuple[float, float]],
                               holes: Optional[List[List[Tuple[float, float]]]] = None,
                               stitch_type: StitchType = StitchType.FILL,
                               params: Optional[StitchParams] = None) -> StitchPath:
        """Generate stitches from raw geometry (without EmbroideryObject)."""
        if params is None:
            params = StitchParams(stitch_type=stitch_type)
        else:
            params.stitch_type = stitch_type

        # Clean geometry
        clean_contour, clean_holes = self.path_cleaner.clean(contour, holes)

        # Generate
        main_path = self._generate_by_type(clean_contour, clean_holes, params)

        # Underlay
        if params.auto_underlay and self._needs_underlay(stitch_type):
            underlay_path = self._generate_underlay(clean_contour, clean_holes, params)
            combined = StitchPath()
            combined.points = underlay_path.points + main_path.points
            main_path = combined

        # Compensation
        if params.auto_compensation:
            pull, push = self.compensation.compute_for_object(
                stitch_type, params.fabric, params.density
            )
            main_path = self.compensation.apply(
                main_path, pull, push, stitch_type, params.fabric
            )

        return main_path

    def generate_satin_column(self,
                              centerline: List[Tuple[float, float]],
                              width: float = 6.0,
                              params: Optional[StitchParams] = None) -> StitchPath:
        """Generate satin column along a centerline with fixed width."""
        if params is None:
            params = StitchParams(stitch_type=StitchType.SATIN, density=0.4)

        path = self.satin.generate_column(centerline, width, params.color_index)

        # Apply compensation
        if params.auto_compensation:
            pull, push = self.compensation.compute_for_object(
                StitchType.SATIN, params.fabric, params.density
            )
            path = self.compensation.apply(path, pull, push, StitchType.SATIN, params.fabric)

        return path

    def generate_running(self,
                         points: List[Tuple[float, float]],
                         stitch_type: StitchType = StitchType.RUN,
                         params: Optional[StitchParams] = None) -> StitchPath:
        """Generate running stitch along a polyline."""
        if params is None:
            params = self._defaults.get(stitch_type, StitchParams(stitch_type=stitch_type))

        # Create minimal object for run engine
        obj = EmbroideryObject(
            contour=points,
            stitch_type=stitch_type,
            density=params.density,
            color_index=params.color_index
        )

        return self.run.generate(obj=obj, stitch_type=stitch_type, color_index=params.color_index)

    def auto_select_stitch_type(self,
                                contour: List[Tuple[float, float]],
                                holes: Optional[List[List[Tuple[float, float]]]] = None,
                                width_mm: float = 0.0,
                                height_mm: float = 0.0,
                                area_mm2: float = 0.0) -> StitchType:
        """
        Automatically select stitch type based on geometry.

        Rules:
        - Narrow shapes (width < 3mm) -> SATIN
        - Long thin shapes (aspect > 4) -> SATIN
        - Large areas (area > 200mm²) -> TATAMI
        - Medium areas with skeleton -> SATIN
        - Lines/curves -> RUN
        """
        if not contour or len(contour) < 3:
            return StitchType.RUN

        if width_mm <= 0 or height_mm <= 0:
            # Calculate from contour
            xs = [p[0] for p in contour]
            ys = [p[1] for p in contour]
            width_mm = max(xs) - min(xs)
            height_mm = max(ys) - min(ys)

        if area_mm2 <= 0:
            # Shoelace formula
            area_mm2 = abs(self._shoelace(contour))

        aspect = max(width_mm, height_mm) / max(1.0, min(width_mm, height_mm))

        # Very narrow -> satin
        if min(width_mm, height_mm) < 3.0:
            return StitchType.SATIN

        # Long and thin -> satin
        if aspect > 4.0 and min(width_mm, height_mm) < 12.0:
            return StitchType.SATIN

        # Large area -> tatami
        if area_mm2 > 200.0:
            return StitchType.TATAMI

        # Medium area, could be either
        if area_mm2 > 50.0:
            return StitchType.TATAMI

        # Small area -> satin if elongated, else tatami
        if aspect > 2.0:
            return StitchType.SATIN

        return StitchType.TATAMI

    # ============================================================
    # Internal generation methods
    # ============================================================

    def _generate_by_type(self,
                          contour: List[Tuple[float, float]],
                          holes: Optional[List[List[Tuple[float, float]]]],
                          params: StitchParams) -> StitchPath:
        """Dispatch to appropriate engine based on stitch type."""

        if params.stitch_type in (StitchType.RUN, StitchType.TRIPLE_RUN,
                                   StitchType.OUTLINE, StitchType.CENTER_RUN,
                                   StitchType.EDGE_RUN, StitchType.CONTOUR):
            obj = EmbroideryObject(
                contour=contour,
                holes=holes or [],
                stitch_type=params.stitch_type,
                density=params.density,
                color_index=params.color_index
            )
            return self.run.generate(obj=obj, stitch_type=params.stitch_type,
                                     color_index=params.color_index)

        elif params.stitch_type in (StitchType.SATIN, StitchType.COLUMN):
            # For satin from contour, use generate_from_contour
            return self.satin.generate_from_contour(
                contour, width=min(12.0, max(3.0, params.density * 6)),
                angle=params.angle, color_index=params.color_index,
                density=params.density
            )

        elif params.stitch_type in (StitchType.TATAMI, StitchType.FILL,
                                     StitchType.PROGRAM_SPLIT, StitchType.SPIRAL,
                                     StitchType.CROSS_STITCH):
            return self.tatami.generate(
                contour, params.stitch_type, params.density,
                params.angle, params.color_index, holes
            )

        else:
            # Default to tatami
            return self.tatami.generate(
                contour, StitchType.TATAMI, params.density,
                params.angle, params.color_index, holes
            )

    def _generate_underlay(self,
                           contour: List[Tuple[float, float]],
                           holes: Optional[List[List[Tuple[float, float]]]],
                           params: StitchParams) -> StitchPath:
        """Generate underlay for the given stitch type."""
        if params.stitch_type in (StitchType.SATIN, StitchType.COLUMN):
            # For satin, we need rails - extract from contour
            # Simplified: use edge run as underlay
            return self.underlay.generate(
                contour, UnderlayType.EDGE_RUN, params.stitch_type,
                params.underlay_density, params.angle
            )
        else:
            # For fill, use selected underlay type
            return self.underlay.generate(
                contour, params.underlay_type, params.stitch_type,
                params.underlay_density, params.angle
            )

    def _needs_underlay(self, stitch_type: StitchType) -> bool:
        """Check if stitch type needs underlay."""
        return stitch_type not in (StitchType.RUN, StitchType.TRIPLE_RUN,
                                    StitchType.CENTER_RUN, StitchType.EDGE_RUN,
                                    StitchType.OUTLINE, StitchType.CONTOUR)

    def _merge_params(self, obj: EmbroideryObject,
                      params: Optional[StitchParams]) -> StitchParams:
        """Merge object properties with provided params."""
        if params is None:
            params = StitchParams(stitch_type=obj.stitch_type)

        # Use object values as fallback
        if params.density == 0.4 and obj.density > 0:
            params.density = obj.density
        if params.angle == 0.0 and obj.direction_angle != 0:
            params.angle = obj.direction_angle
        if params.color_index == 0:
            params.color_index = obj.color_index

        return params

    def _shoelace(self, contour: List[Tuple[float, float]]) -> float:
        """Polygon area via shoelace formula."""
        if len(contour) < 3:
            return 0.0
        area = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            area += contour[i][0] * contour[j][1] - contour[j][0] * contour[i][1]
        return area / 2.0

    def get_default_params(self, stitch_type: StitchType) -> StitchParams:
        """Get default parameters for a stitch type."""
        return self._defaults.get(stitch_type, StitchParams(stitch_type=stitch_type))

    def set_default_params(self, stitch_type: StitchType, params: StitchParams):
        """Set default parameters for a stitch type."""
        self._defaults[stitch_type] = params


# Convenience functions
def generate_stitches(obj: EmbroideryObject,
                      params: Optional[StitchParams] = None) -> StitchPath:
    """Quick stitch generation."""
    gen = StitchGenerator()
    return gen.generate(obj, params)


def generate_from_contour(contour: List[Tuple[float, float]],
                          stitch_type: StitchType = StitchType.FILL,
                          params: Optional[StitchParams] = None) -> StitchPath:
    """Quick generation from contour."""
    gen = StitchGenerator()
    return gen.generate_from_geometry(contour, None, stitch_type, params)


if __name__ == "__main__":
    # Quick test
    from ..core.design.embroidery_design import EmbroideryObject, ThreadColor

    # Test running
    gen = StitchGenerator()

    # Running stitch
    run_obj = EmbroideryObject(
        contour=[(0, 0), (10, 0), (10, 10), (0, 10)],
        stitch_type=StitchType.RUN,
        density=2.0
    )
    run_path = gen.generate(run_obj)
    print(f"Run: {run_path.total_stitches} stitches")

    # Satin
    satin_obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 4), (0, 4)],
        stitch_type=StitchType.SATIN,
        density=0.4
    )
    satin_path = gen.generate(satin_obj)
    print(f"Satin: {satin_path.total_stitches} stitches")

    # Fill
    fill_obj = EmbroideryObject(
        contour=[(0, 0), (20, 0), (20, 20), (0, 20)],
        stitch_type=StitchType.TATAMI,
        density=0.4
    )
    fill_path = gen.generate(fill_obj)
    print(f"Fill: {fill_path.total_stitches} stitches")