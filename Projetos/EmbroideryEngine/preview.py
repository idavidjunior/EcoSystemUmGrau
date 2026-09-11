"""
Script de teste rápido para o Stitch Preview.
Gera um design sintético e abre o preview.

Uso:
    python preview.py                    # Design sintético padrão
    python preview.py caminho/para/img   # Imagem real (pipeline completo)
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog

sys.path.insert(0, os.path.dirname(__file__))


def create_synthetic_design():
    from src.core.design.embroidery_design import (
        EmbroideryDesign, EmbroideryObject, StitchType,
        UnderlayType, ThreadColor, ThreadPalette, MachineProfile
    )
    from src.core.stitches.stitch_primitives import StitchPath, StitchCommand
    import math

    design = EmbroideryDesign(name="Teste Sintético", width_mm=80, height_mm=80)
    design.machine = MachineProfile("Generic", hoop_width_mm=100, hoop_height_mm=100)

    palette_threads = [
        ThreadColor("Azul", r=30, g=80, b=200),
        ThreadColor("Vermelho", r=200, g=40, b=40),
        ThreadColor("Verde", r=40, g=160, b=60),
        ThreadColor("Amarelo", r=240, g=200, b=30),
    ]
    design.palette = ThreadPalette(name="Test", threads=palette_threads)

    cx, cy = 40, 40

    radius = 18
    pentagon = []
    for i in range(5):
        angle = math.radians(72 * i - 90)
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        pentagon.append((px, py))

    obj1 = EmbroideryObject(
        name="Pentágono",
        stitch_type=StitchType.TATAMI,
        color_index=0,
        color=palette_threads[0],
        contour=pentagon,
        bounds=(cx - radius, cy - radius, cx + radius, cy + radius),
        density=0.4,
        underlay_type=UnderlayType.DOUBLE_ZIGZAG,
    )
    obj1.generated_stitches = _gen_tatami(pentagon, 0.4, 0, 0)
    design.objects.append(obj1)

    tri_cx, tri_cy = 15, 65
    tri_r = 10
    triangle = []
    for i in range(3):
        angle = math.radians(120 * i - 90)
        px = tri_cx + tri_r * math.cos(angle)
        py = tri_cy + tri_r * math.sin(angle)
        triangle.append((px, py))

    obj2 = EmbroideryObject(
        name="Triângulo",
        stitch_type=StitchType.FILL,
        color_index=1,
        color=palette_threads[1],
        contour=triangle,
        bounds=(tri_cx - tri_r, tri_cy - tri_r, tri_cx + tri_r, tri_cy + tri_r),
        density=0.4,
        underlay_type=UnderlayType.ZIGZAG,
    )
    obj2.generated_stitches = _gen_tatami(triangle, 0.4, 45, 1)
    design.objects.append(obj2)

    star_cx, star_cy = 65, 65
    star_r = 12
    star = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        r = star_r if i % 2 == 0 else star_r * 0.4
        px = star_cx + r * math.cos(angle)
        py = star_cy + r * math.sin(angle)
        star.append((px, py))

    obj3 = EmbroideryObject(
        name="Estrela",
        stitch_type=StitchType.SATIN,
        color_index=2,
        color=palette_threads[2],
        contour=star,
        bounds=(star_cx - star_r, star_cy - star_r, star_cx + star_r, star_cy + star_r),
        density=0.4,
        underlay_type=UnderlayType.CENTER_RUN,
    )
    obj3.generated_stitches = _gen_satin(star, 0, 2)
    design.objects.append(obj3)

    rect_pts = [(10, 10), (25, 10), (25, 22), (10, 22)]
    obj4 = EmbroideryObject(
        name="Retângulo",
        stitch_type=StitchType.TATAMI,
        color_index=3,
        color=palette_threads[3],
        contour=rect_pts,
        bounds=(10, 10, 25, 22),
        density=0.4,
        underlay_type=UnderlayType.ZIGZAG,
    )
    obj4.generated_stitches = _gen_tatami(rect_pts, 0.4, 0, 3)
    design.objects.append(obj4)

    design.recalculate_metadata()
    return design


def _gen_tatami(contour, density, angle, color_index):
    from src.core.stitches.stitch_primitives import StitchPath, StitchCommand
    import math

    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    rotated = [(p[0] * cos_a - p[1] * sin_a,
                p[0] * sin_a + p[1] * cos_a) for p in contour]

    min_y = min(p[1] for p in rotated)
    max_y = max(p[1] for p in rotated)

    path = StitchPath()
    first = True
    direction = 1

    y = min_y + density / 2
    while y <= max_y:
        intersections = []
        n = len(rotated)
        for i in range(n):
            j = (i + 1) % n
            y1 = rotated[i][1]
            y2 = rotated[j][1]
            if (y1 <= y < y2) or (y2 <= y < y1):
                if y1 != y2:
                    x = rotated[i][0] + (y - y1) / (y2 - y1) * (rotated[j][0] - rotated[i][0])
                    intersections.append(x)

        if len(intersections) >= 2:
            intersections.sort()
            i = 0
            while i < len(intersections) - 1:
                x1 = intersections[i]
                x2 = intersections[i + 1]

                if direction == 1:
                    pts = [(x1, y), (x2, y)]
                else:
                    pts = [(x2, y), (x1, y)]

                for px, py in pts:
                    orig_x = px * cos_a + py * sin_a
                    orig_y = -px * sin_a + py * cos_a
                    if first:
                        path.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)
                        first = False
                    else:
                        last = path.points[-1]
                        dist = math.sqrt((orig_x - last.x) ** 2 + (orig_y - last.y) ** 2)
                        if dist > 12.0:
                            path.add_stitch_absolute(orig_x, orig_y, StitchCommand.JUMP)
                        path.add_stitch_absolute(orig_x, orig_y, StitchCommand.STITCH)

                i += 2

        direction *= -1
        y += density

    return path


def _gen_satin(contour, angle, color_index):
    from src.core.stitches.stitch_primitives import StitchPath, StitchCommand
    import math

    if len(contour) < 3:
        return StitchPath()

    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    projections = []
    for p in contour:
        proj = p[0] * cos_a + p[1] * sin_a
        projections.append((proj, p))
    projections.sort(key=lambda x: x[0])

    mid = len(projections) // 2
    rail_a = [p[1] for p in projections[:mid]]
    rail_b = [p[1] for p in projections[mid:]]

    n = max(len(rail_a), len(rail_b))
    if len(rail_a) < n:
        rail_a = [rail_a[min(i, len(rail_a) - 1)] for i in range(n)]
    if len(rail_b) < n:
        rail_b = [rail_b[min(i, len(rail_b) - 1)] for i in range(n)]

    path = StitchPath()
    path.add_stitch_absolute(rail_a[0][0], rail_a[0][1], StitchCommand.STITCH)
    path.add_stitch_absolute(rail_b[0][0], rail_b[0][1], StitchCommand.STITCH)

    for i in range(1, n):
        rx, ry = rail_b[i]
        path.add_stitch_absolute(rx, ry, StitchCommand.STITCH)
        if i + 1 < n:
            lx, ly = rail_a[i + 1]
            path.add_stitch_absolute(lx, ly, StitchCommand.STITCH)

    return path


def create_from_image(image_path):
    from src.pipeline.digitizer_pipeline import DigitizerPipeline

    pipeline = DigitizerPipeline(density=0.4, max_colors=6, scale_mm=0.2)
    design, report = pipeline.digitize_and_validate(image_path)

    print(f"Pipeline concluído:")
    print(f"  Objetos: {report['total_issues']}")
    print(f"  Score: {report['score']}")
    print(f"  Total issues: {report['total_issues']}")

    return design


def main():
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            print(f"Processando imagem: {image_path}")
            design = create_from_image(image_path)
        else:
            print(f"Arquivo não encontrado: {image_path}")
            print("Usando design sintético...")
            design = create_synthetic_design()
    else:
        print("Usando design sintético de teste...")
        design = create_synthetic_design()

    print(f"\nDesign: {design.name}")
    print(f"  Dimensões: {design.width_mm:.1f} x {design.height_mm:.1f} mm")
    summary = design.stitch_summary
    print(f"  Objetos: {summary['objects']}")
    print(f"  Cores: {summary['colors']}")
    print(f"  Pontos: {summary['stitches']}")
    print(f"  Jumps: {summary['jumps']}")
    print(f"  Trims: {summary['trims']}")
    print(f"  Tempo est.: {summary['estimated_time_seconds']:.0f}s")

    print("\nAbrindo preview...")
    from src.simulation.stitch_preview import StitchPreview
    preview = StitchPreview(design)
    preview.show()


if __name__ == "__main__":
    main()
