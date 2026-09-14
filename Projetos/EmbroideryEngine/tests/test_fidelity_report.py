"""
Unit tests for Fidelity Report & Round-trip (src/validation/fidelity_report.py).

Cobre o DoD do módulo:
- Aritmética: DICE (idêntico/disjunto/vazios), máscara por cor, SSIM gray
- Alinhamento original -> render (contain + centralizado, aspect ratio)
- avg_stitch_length_mm
- Round-trip gold standard (pyembroidery escreve -> lê) com erro <= 0.2mm
- Round-trip native (PESWriter) DETECTA o desvio do encoder nativo (ok=False)
- build_report gera PNG composto + JSON com métricas
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pytest
from PIL import Image

from src.core.design.embroidery_design import (
    EmbroideryDesign, EmbroideryObject, ThreadColor, StitchType, UnderlayType
)
from src.core.stitches.stitch_primitives import StitchPath
from src.validation.fidelity_report import (
    build_report,
    verify_roundtrip,
    dice_coefficient,
    color_mask,
    ssim_gray,
    align_to_render,
    avg_stitch_length_mm,
)


# ------------------------------------------------------------
# Fixtures / helpers (mesmas convenções do test_embroidery_renderer)
# ------------------------------------------------------------

def _make_design(objects, width_mm=80.0, height_mm=80.0):
    design = EmbroideryDesign(name="test", width_mm=width_mm,
                              height_mm=height_mm)
    for obj in objects:
        design.add_object(obj)
    design.recalculate_metadata()
    return design


def _obj_horizontal_line(color=(200, 40, 40), length_mm=20.0, y=0.0):
    """Objeto RUN com um único segmento horizontal de (0,y) a (length_mm,y)."""
    obj = EmbroideryObject(
        name="linha", stitch_type=StitchType.RUN,
        color_index=0,
        color=ThreadColor("teste", r=color[0], g=color[1], b=color[2]),
        contour=[(0, y), (length_mm, y)],
        bounds=(0, y - 5, length_mm, y + 5),
        density=0.4, underlay_type=UnderlayType.NONE,
    )
    path = StitchPath()
    path.add_stitch_absolute(0, y)
    path.add_stitch_absolute(length_mm, y)
    obj.generated_stitches = path
    return obj


# ------------------------------------------------------------
# Aritmética
# ------------------------------------------------------------

def test_dice_identical():
    a = np.ones((5, 5), dtype=bool)
    assert dice_coefficient(a, a) == 1.0


def test_dice_disjoint():
    a = np.zeros((5, 5), dtype=bool)
    b = np.ones((5, 5), dtype=bool)
    assert dice_coefficient(a, b) == 0.0


def test_dice_both_empty_is_agreement():
    a = np.zeros((5, 5), dtype=bool)
    b = np.zeros((5, 5), dtype=bool)
    assert dice_coefficient(a, b) == 1.0


def test_dice_partial():
    a = np.zeros((6, 6), dtype=bool)
    b = np.zeros((6, 6), dtype=bool)
    a[0:2, 0:2] = True
    b[1:3, 1:3] = True
    # A: 4 px (0,0..1,1); B: 4 px (1,1..2,2); inter={1,1} => 2*1/(4+4)=0.25
    assert dice_coefficient(a, b) == pytest.approx(0.25)


def test_color_mask_exact_and_far():
    img = Image.new("RGB", (40, 30), (29, 80, 199))
    m = color_mask(img, (29, 80, 199))
    assert m.shape == (30, 40)
    assert bool(m.all())
    m2 = color_mask(img, (255, 0, 0))
    assert not bool(m2.any())


def test_ssim_gray_identical_and_different():
    a = Image.new("RGB", (40, 40), (100, 100, 100))
    b = Image.new("RGB", (40, 40), (100, 100, 100))
    assert ssim_gray(a, b) == pytest.approx(1.0, abs=1e-3)
    c = Image.new("RGB", (40, 40), (200, 200, 200))
    assert ssim_gray(a, c) < 1.0


def test_align_to_render_preserves_aspect():
    orig = Image.new("RGB", (200, 100), (255, 0, 0))
    render = Image.new("RGBA", (100, 100), (245, 240, 232, 255))
    out = align_to_render(orig, render)
    assert out.size == (100, 100)
    # contain 200x100 num canvas 100x100: largura 100, altura 50, letterbox.
    alpha = np.asarray(out)
    # linhas centralizadas: as 25 linhas do topo = branco do fundo.
    assert (alpha[0] == np.array([255, 255, 255, 255])).all()
    # centro deve ser vermelho (região pintada 100x50 começa na linha 25)
    assert (alpha[25] == np.array([255, 0, 0, 255])).all()


def test_avg_stitch_length_mm():
    design = _make_design([_obj_horizontal_line(length_mm=20.0)])
    assert avg_stitch_length_mm(design) == pytest.approx(20.0)


# ------------------------------------------------------------
# Round-trip
# ------------------------------------------------------------

def test_roundtrip_gold_standard_exact(tmp_path):
    design = _make_design([_obj_horizontal_line(length_mm=20.0)])
    pes = str(tmp_path / "gold.pes")
    rt = verify_roundtrip(design, pes_path=pes, writer="pyembroidery")
    assert rt["ok"] is True
    assert rt["stitches_expected"] == rt["stitches_read"] == 2
    assert rt["max_error_mm"] <= 0.2
    assert os.path.isfile(pes)


def test_roundtrip_native_detects_encoder_bug(tmp_path):
    """O encoder nativo hoje escreve PES ilegível (offset/header quebrados).
    O verifier DEVE detectar e reportar ok=False com evidência numérica.
    Se este teste começar a falhar, provavelmente o encoder foi corrigido:
    atualize o expectation, não degrade o gate."""
    design = _make_design([_obj_horizontal_line(length_mm=20.0)])
    pes = str(tmp_path / "native.pes")
    rt = verify_roundtrip(design, pes_path=pes, writer="native")
    assert rt["ok"] is False
    assert rt["max_error_mm"] is None or rt["max_error_mm"] > 0.2
    assert os.path.isfile(pes)


# ------------------------------------------------------------
# build_report
# ------------------------------------------------------------

def test_build_report_generates_artifacts(tmp_path):
    design = _make_design([_obj_horizontal_line(length_mm=20.0)])
    # imagem original na cor do fio, para o DICE ter casamento real
    img = Image.new("RGB", (80, 80), (200, 40, 40))
    original = str(tmp_path / "orig.png")
    img.save(original)
    png = str(tmp_path / "out.png")
    jsn = str(tmp_path / "out.json")

    report = build_report(design, original_image_path=original,
                          output_png_path=png, output_json_path=jsn)

    assert os.path.isfile(png)
    assert os.path.isfile(jsn)
    assert 0.0 <= report["metrics"]["ssim"] <= 1.0
    assert report["metrics"]["dice_by_color"]
    assert report["design"]["total_stitches"] == 2
    assert report["metrics"]["avg_stitch_length_mm"] == pytest.approx(20.0)

    first = report["metrics"]["dice_by_color"][0]
    assert first["dice"] > 0.0  # cor do fio está na imagem original e no render
    assert first["area_original_px"] > 0
    assert first["area_render_px"] > 0


def test_build_report_missing_original_raises(tmp_path):
    design = _make_design([_obj_horizontal_line()])
    with pytest.raises(FileNotFoundError):
        build_report(design, original_image_path=str(tmp_path / "nao_existe.png"))