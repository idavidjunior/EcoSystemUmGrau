"""
FASE 13 - Quality Engine

Analisa e valida qualidade de um design de bordado:
- Pontos muito curtos ou muito longos
- Overlaps excessivos
- Saltos longos
- Densidade inadequada
- Bugs de geometria
- Número de pontos vs área
- Limites de máquina (máx. pontos, cores, dimensões, comprimento ponto/salto)
"""

import math
from typing import List, Dict, Tuple, Optional
from ..core.design.embroidery_design import EmbroideryDesign, StitchType
from ..core.stitches.stitch_primitives import StitchCommand
from ..config.config_loader import get_machine_profile


class QualityIssue:
    """Um problema de qualidade detectado."""

    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_ERROR = "error"
    SEVERITY_CRITICAL = "critical"

    def __init__(self, severity: str, category: str, message: str,
                 location: Optional[Tuple[float, float]] = None,
                 object_name: str = ""):
        self.severity = severity
        self.category = category
        self.message = message
        self.location = location
        self.object_name = object_name

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.category}: {self.message}"


class QualityEngine:
    """Motor de análise de qualidade de bordado."""

    def __init__(self, machine_profile: Optional[str] = None):
        """
        Initialize QualityEngine.

        Args:
            machine_profile: Machine profile key (e.g., 'generic', 'brother_pe800', 'janome_mb7')
                            If None, uses default machine from config.
        """
        machine = get_machine_profile(machine_profile) if machine_profile else get_machine_profile("generic")

        # Load limits from machine profile
        self.min_stitch_length = machine.get("min_stitch_length_mm", 0.3)
        self.max_stitch_length = machine.get("max_stitch_length_mm", 12.0)
        self.max_jump_distance = machine.get("max_jump_length_mm", 10.0)
        self.max_stitches = machine.get("max_stitches", 500000)
        self.max_colors = machine.get("max_colors", 65)
        self.max_width_mm = machine.get("hoop_width_mm", 200.0)
        self.max_height_mm = machine.get("hoop_height_mm", 200.0)

        # Quality thresholds
        self.max_issues_per_category = 10
        self.issues: List[QualityIssue] = []

        # Store machine info for reporting
        self.machine_name = machine.get("name", "Unknown")
        self.machine_format = machine.get("format", "unknown")

    def analyze(self, design: EmbroideryDesign) -> Dict:
        """Analisa o design e retorna relatório de qualidade."""
        self.issues = []

        # Structural checks
        self._check_empty_design(design)

        # Machine limit checks
        self._check_machine_limits(design)

        # Stitch quality checks
        self._check_stitch_lengths(design)
        self._check_long_jumps(design)
        self._check_stitch_density(design)

        # Geometry checks
        self._check_geometric_consistency(design)

        # Sequencing checks
        self._check_sequencing(design)

        score = self._calculate_score(design)

        return {
            "score": score,
            "machine": self.machine_name,
            "format": self.machine_format,
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_CRITICAL]),
            "errors": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_ERROR]),
            "warnings": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_WARNING]),
            "info": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_INFO]),
            "issues": self.issues
        }

    def _check_empty_design(self, design: EmbroideryDesign):
        if len(design.objects) == 0:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_CRITICAL,
                "structure",
                "Design não contém objetos"
            ))

        total_stitches = design.total_stitches
        if total_stitches == 0:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_CRITICAL,
                "stitches",
                "Design não contém pontos"
            ))

    def _check_machine_limits(self, design: EmbroideryDesign):
        """Check design against machine limits."""

        # Total stitches
        total_stitches = design.total_stitches
        if total_stitches > self.max_stitches:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_ERROR,
                "machine_limits",
                f"Total de pontos ({total_stitches}) excede limite da máquina ({self.max_stitches})"
            ))
        elif total_stitches > self.max_stitches * 0.8:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_WARNING,
                "machine_limits",
                f"Total de pontos ({total_stitches}) próximo ao limite da máquina ({self.max_stitches})"
            ))

        # Total colors
        total_colors = design.total_colors
        if total_colors > self.max_colors:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_ERROR,
                "machine_limits",
                f"Número de cores ({total_colors}) excede limite da máquina ({self.max_colors})"
            ))

        # Design dimensions
        bbox = design.bounding_box
        design_width = bbox[2] - bbox[0]
        design_height = bbox[3] - bbox[1]

        if design_width > self.max_width_mm:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_ERROR,
                "machine_limits",
                f"Largura do design ({design_width:.1f}mm) excede bastidor ({self.max_width_mm}mm)"
            ))

        if design_height > self.max_height_mm:
            self.issues.append(QualityIssue(
                QualityIssue.SEVERITY_ERROR,
                "machine_limits",
                f"Altura do design ({design_height:.1f}mm) excede bastidor ({self.max_height_mm}mm)"
            ))

        # Check individual objects
        for obj in design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue

            obj_bbox = obj.bounds
            obj_width = obj_bbox[2] - obj_bbox[0]
            obj_height = obj_bbox[3] - obj_bbox[1]

            if obj_width > self.max_width_mm or obj_height > self.max_height_mm:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_WARNING,
                    "machine_limits",
                    f"Objeto {obj.name} maior que bastidor ({obj_width:.1f}x{obj_height:.1f}mm)",
                    obj.center, obj.name
                ))

    def _check_stitch_lengths(self, design: EmbroideryDesign):
        for obj in design.objects:
            if not obj.generated_stitches:
                continue

            short_count = 0
            long_count = 0
            worst_short = 0.0
            worst_long = 0.0
            last_stitch = None

            for i, pt in enumerate(obj.generated_stitches.points):
                if pt.command == StitchCommand.STITCH:
                    if last_stitch is not None:
                        dist = math.sqrt((pt.x - last_stitch.x) ** 2 + (pt.y - last_stitch.y) ** 2)

                        if dist > 0 and dist < self.min_stitch_length:
                            short_count += 1
                            worst_short = max(worst_short, dist)

                        if dist > self.max_stitch_length:
                            long_count += 1
                            worst_long = max(worst_long, dist)

                    last_stitch = pt
                elif pt.command in (StitchCommand.TIE_OFF, StitchCommand.TIE_IN):
                    last_stitch = pt
                else:
                    last_stitch = None

            if short_count > 5:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_WARNING,
                    "stitch_length",
                    f"{short_count} stitches curtos (< {self.min_stitch_length}mm) em {obj.name} (pior: {worst_short:.2f}mm)",
                    obj.center, obj.name
                ))

            if long_count > 0:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_WARNING,
                    "stitch_length",
                    f"{long_count} stitches longos (> {self.max_stitch_length}mm) em {obj.name} (pior: {worst_long:.1f}mm)",
                    obj.center, obj.name
                ))

    def _check_long_jumps(self, design: EmbroideryDesign):
        for obj in design.objects:
            if not obj.generated_stitches:
                continue

            long_jumps = 0
            worst_jump = 0.0
            last_anchor = None
            for i, pt in enumerate(obj.generated_stitches.points):
                if pt.command in (StitchCommand.STITCH, StitchCommand.TIE_OFF, StitchCommand.TIE_IN):
                    last_anchor = pt
                elif pt.command == StitchCommand.JUMP and last_anchor is not None:
                    dist = math.sqrt((pt.x - last_anchor.x) ** 2 + (pt.y - last_anchor.y) ** 2)

                    if dist > self.max_jump_distance:
                        long_jumps += 1
                        worst_jump = max(worst_jump, dist)

            if long_jumps > 0:
                severity = QualityIssue.SEVERITY_WARNING if worst_jump > self.max_jump_distance * 2 else QualityIssue.SEVERITY_INFO
                self.issues.append(QualityIssue(
                    severity,
                    "jump",
                    f"{long_jumps} saltos longos em {obj.name} (pior: {worst_jump:.1f}mm, limite: {self.max_jump_distance}mm)",
                    obj.center, obj.name
                ))

    def _check_stitch_density(self, design: EmbroideryDesign):
        for obj in design.objects:
            if obj.stitch_type in (StitchType.RUN, StitchType.TRIPLE_RUN, StitchType.SATIN):
                continue

            total_stitch_length = 0
            stitch_points = 0
            if not obj.generated_stitches:
                continue

            for i, pt in enumerate(obj.generated_stitches.points):
                if pt.command == StitchCommand.STITCH and i > 0:
                    prev = obj.generated_stitches.points[i - 1]
                    if prev.command == StitchCommand.STITCH:
                        dist = math.sqrt((pt.x - prev.x) ** 2 + (pt.y - prev.y) ** 2)
                        total_stitch_length += dist
                        stitch_points += 1

            if stitch_points > 0 and obj.area > 0:
                density_ratio = total_stitch_length / obj.area
                if density_ratio < 0.1:
                    self.issues.append(QualityIssue(
                        QualityIssue.SEVERITY_WARNING,
                        "density",
                        f"Densidade muito baixa em {obj.name} ({density_ratio:.3f} mm/mm²)",
                        obj.center, obj.name
                    ))
                elif density_ratio > 5.0:
                    self.issues.append(QualityIssue(
                        QualityIssue.SEVERITY_WARNING,
                        "density",
                        f"Densidade muito alta em {obj.name} ({density_ratio:.3f} mm/mm²)",
                        obj.center, obj.name
                    ))

    def _check_geometric_consistency(self, design: EmbroideryDesign):
        for obj in design.objects:
            if not obj.contour or len(obj.contour) < 3:
                continue

            area = abs(self._shoelace(obj.contour))
            if area < 0.1:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_ERROR,
                    "geometry",
                    f"Objeto {obj.name} com área inválida ({area:.3f}mm²)",
                    obj.center, obj.name
                ))

            if len(obj.contour) < 3:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_ERROR,
                    "geometry",
                    f"Objeto {obj.name} com contorno inválido ({len(obj.contour)} pontos)",
                    obj.center, obj.name
                ))

            # Check for self-intersections (simplified)
            if self._has_self_intersection(obj.contour):
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_WARNING,
                    "geometry",
                    f"Objeto {obj.name} pode ter auto-interseção no contorno",
                    obj.center, obj.name
                ))

    def _has_self_intersection(self, points: List[Tuple[float, float]]) -> bool:
        """Simple self-intersection check."""
        n = len(points)
        if n < 4:
            return False

        for i in range(n):
            j = (i + 1) % n
            for k in range(i + 2, n):
                if k == (i - 1) % n:
                    continue
                l = (k + 1) % n
                if l == i or l == j:
                    continue

                if self._segments_intersect(points[i], points[j], points[k], points[l]):
                    return True
        return False

    def _segments_intersect(self, p1, p2, q1, q2) -> bool:
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

    def _check_sequencing(self, design: EmbroideryDesign):
        for i, obj in enumerate(design.objects):
            if i == 0:
                continue

            prev = design.objects[i - 1]
            if not obj.visible or not prev.visible:
                continue

            dist = math.sqrt(
                (obj.center[0] - prev.center[0]) ** 2 +
                (obj.center[1] - prev.center[1]) ** 2
            )

            if dist > 50.0 and obj.color_index != prev.color_index:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_INFO,
                    "sequencing",
                    f"Objetos de cores diferentes distantes: {dist:.1f}mm",
                    obj.center, obj.name
                ))

    def _shoelace(self, contour: list) -> float:
        """Área do polígono (Shoelace)."""
        area = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            area += contour[i][0] * contour[j][1]
            area -= contour[j][0] * contour[i][1]
        return area / 2.0

    def _calculate_score(self, design: EmbroideryDesign) -> float:
        """Calcula score de 0-100."""
        base_score = 100.0

        category_penalties = {}
        for issue in self.issues:
            cat = issue.category
            if cat not in category_penalties:
                category_penalties[cat] = 0

            if issue.severity == QualityIssue.SEVERITY_CRITICAL:
                category_penalties[cat] += 25
            elif issue.severity == QualityIssue.SEVERITY_ERROR:
                category_penalties[cat] += 15
            elif issue.severity == QualityIssue.SEVERITY_WARNING:
                category_penalties[cat] += 3
            else:
                category_penalties[cat] += 0.5

        penalty = sum(min(v, 30) for v in category_penalties.values())

        score = max(0, base_score - penalty)

        total_stitches = design.total_stitches
        if total_stitches > 0:
            if total_stitches < 100:
                score *= 0.5
            elif total_stitches < 500:
                score *= 0.7
            elif total_stitches > self.max_stitches * 0.8:
                score *= 0.9

        return round(score, 1)

    def summary(self, report: Dict) -> str:
        """Gera resumo legível do relatório."""
        lines = [
            f"Score de Qualidade: {report['score']}/100",
            f"Máquina: {report.get('machine', 'N/A')} ({report.get('format', 'N/A')})",
            f"Total de Issues: {report['total_issues']}",
            f"  Critical: {report['critical']}",
            f"  Error: {report['errors']}",
            f"  Warning: {report['warnings']}",
            f"  Info: {report.get('info', 0)}"
        ]

        if report['score'] >= 90:
            lines.append("Status: EXCELENTE - Pronto para produção")
        elif report['score'] >= 75:
            lines.append("Status: BOM - Aceitável com ressalvas")
        elif report['score'] >= 50:
            lines.append("Status: REGULAR - Requer ajustes")
        else:
            lines.append("Status: RUIM - Revisar antes de exportar")

        return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject, ThreadColor, StitchType
    from ..core.stitches.stitch_primitives import StitchPath, StitchPoint, StitchCommand

    design = EmbroideryDesign(name="Test", width_mm=200, height_mm=200)

    obj = EmbroideryObject(
        name="TestObj",
        contour=[(0, 0), (10, 0), (10, 10), (0, 10)],
        color=ThreadColor("Red", r=255, g=0, b=0),
        color_index=0,
        stitch_type=StitchType.TATAMI,
        density=0.4
    )
    path = StitchPath()
    for x in range(0, 11):
        for y in range(0, 11):
            path.add_stitch_absolute(x, y, StitchCommand.STITCH)
    obj.generated_stitches = path

    design.objects.append(obj)

    qe = QualityEngine("brother_pe800")
    report = qe.analyze(design)
    print(qe.summary(report))