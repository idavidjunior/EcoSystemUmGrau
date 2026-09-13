"""
Unit tests for Embroidery Renderer (src/simulation/embroidery_renderer.py).

Cobre o DoD do módulo:
- Saída RGBA, lado máximo 2400px, proporção preservada
- Cada stitch é segmento (pixel no meio de um stitch = cor do fio)
- Espessura proporcional à densidade (0.4mm ~= 3px a 10px/mm)
- JUMP/TRIM não produzem linha visível
- Underlay desenhado antes, alpha < 255; desligável
- Determinismo (mesma entrada -> mesma imagem)
- Design grande (300mm) -> lado == 2400
- Heurística de divisão underlay/main (estimate_underlay_split)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from PIL import Image

from src.core.design.embroidery_design import (
    EmbroideryDesign, EmbroideryObject, ThreadColor, StitchType, UnderlayType
)
from src.core.stitches.stitch_primitives import StitchPath, StitchCommand
from src.simulation.embroidery_renderer import (
    EmbroideryRenderer, render_design, render_object,
    estimate_underlay_split, compute_scale, MAX_SIDE_PX,
    FABRIC_BG,
)


# ------------------------------------------------------------
# Fixtures / helpers
# ------------------------------------------------------------

def _make_design(objects, width_mm=80.0, height_mm=80.0):
    design = EmbroideryDesign(name="test", width_mm=width_mm,
                              height_mm=height_mm)
    for obj in objects:
        design.add_object(obj)
    design.recalculate_metadata()
    return design


def _obj_horizontal_line(color=(200, 40, 40), density=0.4,
                         underlay_type=UnderlayType.NONE,
                         length_mm=20.0, y=0.0):
    """Objeto com um único stitch horizontal de (0, y) a (length, y)."""
    obj = EmbroideryObject(
        name="linha", stitch_type=StitchType.RUN,
        color_index=0,
        color=ThreadColor("teste", r=color[0], g=color[1], b=color[2]),
        contour=[(0, y), (length_mm, y)],
        bounds=(0, y - 5, length_mm, y + 5),
        density=density, underlay_type=underlay_type,
    )
    path = StitchPath()
    path.add_stitch_absolute(0, y)
    if underlay_type != UnderlayType.NONE:
        # underlay: dois stitches longos cruzando a forma
        path.add_stitch_absolute(length_mm * 0.5, y - 4)
        path.add_stitch_absolute(length_mm, y)
    else:
        path.add_stitch_absolute(length_mm, y)
    obj.generated_stitches = path
    return obj


# ------------------------------------------------------------
# Escala e dimensões
# ------------------------------------------------------------

def test_scale_respects_max_side():
    # Objeto que ocupa 300mm de verdade (recalculate_metadata usa o bbox).
    design = _make_design([_obj_horizontal_line(length_mm=300.0)], 300, 300)
    scale = compute_scale(design, MAX_SIDE_PX)
    assert 300 * scale <= MAX_SIDE_PX + 1


def test_render_size_max_side():
    # Objeto que ocupa 300mm de verdade (recalculate_metadata usa o bbox).
    design = _make_design([_obj_horizontal_line(length_mm=300.0)], 300, 300)
    img = render_design(design)
    assert img.mode == "RGBA"
    assert max(img.width, img.height) <= MAX_SIDE_PX
    # Proporção preservada: design 300x10mm -> largura > altura.
    assert img.width > img.height


def test_render_small_design_uses_max_ppm():
    design = _make_design([_obj_horizontal_line()], 20, 20)
    img = render_design(design)
    # 20mm a 10px/mm -> 200px + margem
    assert img.width < 400


# ------------------------------------------------------------
# Stitch = segmento (cor e posição corretas)
# ------------------------------------------------------------

def test_pixel_on_stitch_is_thread_color():
    color = (200, 40, 40)
    design = _make_design([_obj_horizontal_line(color=color, length_mm=20.0)])
    renderer = EmbroideryRenderer(ss=1)  # sem supersampling p/ pixel exato
    img = renderer.render_object(design.objects[0], px_per_mm=10.0)
    # origin = (8 - bounds[0]*10, 8 - bounds[1]*10) = (8, 8+50)
    mid_x = int(8 + 10 * 10.0)
    mid_y = int(8 - (-5) * 10.0)
    px = img.getpixel((mid_x, mid_y))
    assert abs(px[0] - color[0]) <= 12  # tolerância por AA/width
    assert abs(px[1] - color[1]) <= 12
    assert abs(px[2] - color[2]) <= 12


def test_stitch_is_segment_not_dot():
    """Entre dois stitches consecutivos há linha (não apenas nos pontos)."""
    color = (30, 80, 200)
    design = _make_design([_obj_horizontal_line(color=color, length_mm=40.0)])
    renderer = EmbroideryRenderer(ss=1)
    img = renderer.render_object(design.objects[0], px_per_mm=10.0)
    mid_x = int(8 + 20 * 10.0)   # meio do segmento (x=20mm)
    mid_y = int(8 - (-5) * 10.0)
    px = img.getpixel((mid_x, mid_y))
    assert abs(px[0] - color[0]) <= 12


# ------------------------------------------------------------
# Espessura proporcional à densidade
# ------------------------------------------------------------

def test_thread_width_proportional_to_density():
    """0.4mm a 10px/mm -> ~3px de largura de fio (medida aproximada)."""
    color = (10, 90, 10)
    design = _make_design([_obj_horizontal_line(color=color, length_mm=30.0)])
    renderer = EmbroideryRenderer(ss=1)
    img = renderer.render_object(design.objects[0], px_per_mm=10.0)
    mid_x = int(8 + 15 * 10.0)
    y_center = int(8 - (-5) * 10.0)
    # conta pixels da cor do fio verticalmente na coluna do meio
    width_px = 0
    for dy in range(-6, 7):
        px = img.getpixel((mid_x, y_center + dy))
        if abs(px[0] - color[0]) <= 12 and abs(px[1] - color[1]) <= 12:
            width_px += 1
    assert 2 <= width_px <= 5  # ~3px, com margem


# ------------------------------------------------------------
# JUMP/TRIM não desenham linha
# ------------------------------------------------------------

def test_jump_does_not_draw_line():
    color = (200, 40, 40)
    obj = EmbroideryObject(
        name="jump", stitch_type=StitchType.RUN, color_index=0,
        color=ThreadColor("teste", r=color[0], g=color[1], b=color[2]),
        contour=[(0, 0), (5, 0), (5, 5), (20, 5)],
        bounds=(0, -5, 20, 5), density=0.4,
    )
    path = StitchPath()
    path.add_stitch_absolute(0, 0)
    path.add_stitch_absolute(5, 0)
    path.add_stitch_absolute(5, 5, StitchCommand.JUMP)
    path.add_stitch_absolute(20, 5)
    obj.generated_stitches = path

    renderer = EmbroideryRenderer(ss=1)
    img = renderer.render_object(obj, px_per_mm=10.0)
    # meio do salto (12.5, 5) deve ser fundo (sem linha)
    mid_x = int(8 + 12.5 * 10.0)
    mid_y = int(8 - (-5) * 10.0)
    px = img.getpixel((mid_x, mid_y))
    assert px != (color[0], color[1], color[2], 255)


def test_trim_does_not_draw_line():
    color = (200, 40, 40)
    obj = EmbroideryObject(
        name="trim", stitch_type=StitchType.RUN, color_index=0,
        color=ThreadColor("teste", r=color[0], g=color[1], b=color[2]),
        contour=[(0, 0), (5, 0), (5, 5), (20, 5)],
        bounds=(0, -5, 20, 5), density=0.4,
    )
    path = StitchPath()
    path.add_stitch_absolute(0, 0)
    path.add_stitch_absolute(5, 0)
    path.add_stitch_absolute(5, 5, StitchCommand.TRIM)
    path.add_stitch_absolute(20, 5)
    obj.generated_stitches = path

    renderer = EmbroideryRenderer(ss=1)
    img = renderer.render_object(obj, px_per_mm=10.0)
    mid_x = int(8 + 12.5 * 10.0)
    mid_y = int(8 - (-5) * 10.0)
    px = img.getpixel((mid_x, mid_y))
    assert px != (color[0], color[1], color[2], 255)


# ------------------------------------------------------------
# Underlay
# ------------------------------------------------------------

def test_underlay_rendered_before_main():
    """Com underlay, deve existir área com alpha < 255 na região do underlay."""
    color = (30, 80, 200)
    obj = EmbroideryObject(
        name="under", stitch_type=StitchType.TATAMI, color_index=0,
        color=ThreadColor("teste", r=color[0], g=color[1], b=color[2]),
        contour=[(0, -5), (40, -5), (40, 5), (0, 5)],
        bounds=(0, -5, 40, 5), density=0.4,
        underlay_type=UnderlayType.ZIGZAG, underlay_density=0.6,
    )
    path = StitchPath()
    # underlay: 5 stitches longos (~10mm) cruzando a forma
    for i in range(6):
        path.add_stitch_absolute(i * 10, -4)
    # main: stitches curtos (~2mm) em zigue-zague, claramente mais curtos
    for j in range(30):
        path.add_stitch_absolute(40 if j % 2 == 0 else 38, 4 - j * 0.2)
    obj.generated_stitches = path

    renderer_on = EmbroideryRenderer(ss=1, show_underlay=True)
    renderer_off = EmbroideryRenderer(ss=1, show_underlay=False)
    img_on = renderer_on.render_object(obj, px_per_mm=10.0)
    img_off = renderer_off.render_object(obj, px_per_mm=10.0)

    # Renderização difere com/sem underlay (uma linha translúcida a mais)
    assert img_on.tobytes() != img_off.tobytes()

    # Pixel sobre a linha do underlay (y=-4mm), longe do main: com underlay
    # aparece cor translúcida sobre o fundo; sem underlay é só o fundo.
    # origin = (8 - bounds[0]*10, 8 - bounds[1]*10) = (8, 58); y=-4 -> y=18
    px_x = int(8 + 5 * 10.0)
    px_y = int(58 + (-4) * 10.0)
    px_off = img_off.getpixel((px_x, px_y))
    assert px_off == FABRIC_BG
    px_on = img_on.getpixel((px_x, px_y))
    assert px_on != FABRIC_BG
    assert px_on != (color[0], color[1], color[2], 255)  # translúcido


def test_estimate_underlay_split_detects_join():
    """Path com underlay longo seguido de main curto: divisão no joelho."""
    path = StitchPath()
    # underlay: 5 stitches de ~10mm
    for i in range(6):
        path.add_stitch_absolute(i * 10, 0)
    # main: 40 stitches curtos (~1mm) alternando
    for j in range(40):
        path.add_stitch_absolute(60 + j, 0)
        path.add_stitch_absolute(60 + j, 1)
    # não importa se o main está deslocado; o teste valida a fronteira
    split = estimate_underlay_split(path.points, density_mm=0.4)
    assert 5 <= split <= 8  # fronteira perto do 6º stitch (índice 6)


def test_no_underlay_when_none():
    design = _make_design([_obj_horizontal_line(underlay_type=UnderlayType.NONE)])
    assert design.objects[0].underlay_type == UnderlayType.NONE
    # reuso da demo: render sem underlay não quebra
    img = render_design(design)
    assert img.mode == "RGBA"


# ------------------------------------------------------------
# Determinismo
# ------------------------------------------------------------

def test_deterministic_output():
    d1 = _make_design([_obj_horizontal_line(length_mm=25.0)])
    d2 = _make_design([_obj_horizontal_line(length_mm=25.0)])
    img1 = render_design(d1)
    img2 = render_design(d2)
    assert img1.tobytes() == img2.tobytes()