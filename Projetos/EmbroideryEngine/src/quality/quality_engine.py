"""
FASE 13 - Quality Engine

Analisa e valida qualidade de um design de bordado:
- Pontos muito curtos ou muito longos
- Overlaps excessivos
- Saltos longos
- Densidade inadequada
- Bugs de geometria
- Número de pontos vs área
"""

import math
from typing import List, Dict, Tuple, Optional
from ..core.design.embroidery_design import EmbroideryDesign, StitchType
from ..core.stitches.stitch_primitives import StitchCommand


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

    def __init__(self):
        self.min_stitch_length = 0.3
        self.max_stitch_length = 12.0
        self.max_jump_distance = 10.0
        self.max_issues_per_category = 10
        self.issues: List[QualityIssue] = []

    def analyze(self, design: EmbroideryDesign) -> Dict:
        """Analisa o design e retorna relatório de qualidade."""
        self.issues = []

        self._check_empty_design(design)
        self._check_stitch_lengths(design)
        self._check_long_jumps(design)
        self._check_stitch_density(design)
        self._check_geometric_consistency(design)
        self._check_sequencing(design)

        score = self._calculate_score(design)

        return {
            "score": score,
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_CRITICAL]),
            "errors": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_ERROR]),
            "warnings": len([i for i in self.issues if i.severity == QualityIssue.SEVERITY_WARNING]),
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
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_INFO,
                    "jump",
                    f"{long_jumps} saltos longos em {obj.name} (pior: {worst_jump:.1f}mm)",
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
                        f"Densidade muito baixa em {obj.name}",
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
                    f"Objeto {obj.name} com área inválida",
                    obj.center, obj.name
                ))

            if len(obj.contour) < 3:
                self.issues.append(QualityIssue(
                    QualityIssue.SEVERITY_ERROR,
                    "geometry",
                    f"Objeto {obj.name} com contorno inválido",
                    obj.center, obj.name
                ))

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
            elif total_stitches > 500000:
                score *= 0.9

        return round(score, 1)

    def summary(self, report: Dict) -> str:
        """Gera resumo legível do relatório."""
        lines = [
            f"Score de Qualidade: {report['score']}/100",
            f"Total de Issues: {report['total_issues']}",
            f"  Critical: {report['critical']}",
            f"  Error: {report['errors']}",
            f"  Warning: {report['warnings']}"
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
