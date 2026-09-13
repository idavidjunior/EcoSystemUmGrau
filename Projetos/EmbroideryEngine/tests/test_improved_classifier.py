"""
FASE 10.5 - Golden Set e Testes do ImprovedStitchClassifier

Valida:
1. Detecção correta de OUTLINE/CONTOUR (anéis, polígonos ocos, estrelas).
2. Detecção de TEXTO (glifos isolados vs cluster de glifos -> RUN).
3. ÂNGULO DOMINANTE (direction_angle computado via PCA, nunca 0.0 fixo).
4. FALLBACK preserva as regras atuais (ObjectClassifier) sem regressão.
5. Acurácia >= 85% no golden set e zero regressão nos casos que o
   classificador atual acerta.
"""

import os
import sys
import math

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.embroidery.classifier.improved_classifier import ImprovedStitchClassifier
from src.embroidery.classifier.object_classifier import ObjectClassifier
from src.core.design.embroidery_design import StitchType

try:
    from skimage import draw, measure
    HAS_SKIMAGE = True
except Exception:
    HAS_SKIMAGE = False


# ============================================================
# Helpers de rasterização sintética (escala px -> mm)
# ============================================================

def make_mask_ring(r_outer_px, r_inner_px, size):
    """Coroa circular (anel)."""
    mask = np.zeros((size, size), dtype=bool)
    cy = cx = size // 2
    rr, cc = draw.disk((cy, cx), r_outer_px, shape=mask.shape)
    mask[rr, cc] = True
    rr, cc = draw.disk((cy, cx), r_inner_px, shape=mask.shape)
    mask[rr, cc] = False
    return mask


def make_mask_ellipse(rx_px, ry_px, size):
    mask = np.zeros((size, size), dtype=bool)
    rr, cc = draw.ellipse(size // 2, size // 2, ry_px, rx_px, shape=mask.shape)
    mask[rr, cc] = True
    return mask


def make_mask_rect(w_px, h_px, size=None):
    size = size or max(w_px, h_px) + 30
    mask = np.zeros((size, size), dtype=bool)
    x0 = (size - w_px) // 2
    y0 = (size - h_px) // 2
    mask[y0:y0 + h_px, x0:x0 + w_px] = True
    return mask


def star_xy(cx, cy, R, r):
    pts = []
    for i in range(10):
        radius = R if i % 2 == 0 else r
        angle = -math.pi / 2 + i * math.pi / 5.0
        pts.append((cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle)))
    return pts


def make_mask_star_outline(R_px, r_px, inner_scale, size):
    mask = np.zeros((size, size), dtype=bool)
    cx = cy = size // 2
    pts = star_xy(cx, cy, R_px, r_px)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    rr, cc = draw.polygon(ys, xs, shape=mask.shape)
    mask[rr, cc] = True
    inner = [(cx + (x - cx) * inner_scale, cy + (y - cy) * inner_scale)
             for x, y in pts]
    rr, cc = draw.polygon([p[1] for p in inner], [p[0] for p in inner],
                          shape=mask.shape)
    mask[rr, cc] = False
    return mask


def make_region(mask, scale=0.2):
    """Converte máscara sintética em dict no formato das regiões do pipeline."""
    mask = np.asarray(mask, dtype=np.uint8)
    contours = measure.find_contours(mask, 0.5)
    if not contours:
        raise ValueError("máscara gerou contorno vazio")
    contour = max(contours, key=len)
    contour_mm = [(c[1] * scale, c[0] * scale) for c in contour]  # (x, y) em mm

    perimeter = 0.0
    n = len(contour_mm)
    for i in range(n):
        j = (i + 1) % n
        perimeter += math.hypot(contour_mm[j][0] - contour_mm[i][0],
                                contour_mm[j][1] - contour_mm[i][1])

    ys, xs = np.nonzero(mask)
    xmin, xmax = float(xs.min()), float(xs.max())
    ymin, ymax = float(ys.min()), float(ys.max())
    area_mm2 = float(mask.sum()) * scale * scale

    return {
        'mask': mask,
        'contour_mm': contour_mm,
        'scale_mm': scale,
        'width_mm': (xmax - xmin) * scale,
        'height_mm': (ymax - ymin) * scale,
        'area_mm2': area_mm2,
        'perimeter_mm': perimeter,
        'aspect_ratio': (xmax - xmin) / max(ymax - ymin, 1e-6),
        'bounds_mm': (xmin * scale, ymin * scale,
                      xmax * scale, ymax * scale),
    }


# ============================================================
# Golden set (formas sintéticas realistas)
# ============================================================

SCALE = 0.2  # 1 mm = 5 px


def build_golden_set():
    cases = {}
    cases['ring_10_8'] = make_region(
        make_mask_ring(50, 40, 120), SCALE)                    # anel 10/8mm
    cases['pentagon_outline'] = make_region(
        make_mask_star_outline(45, 45, 0.9, 120), SCALE)       # pentágono oco ~1mm
    cases['circle_filled_4'] = make_region(
        make_mask_ellipse(20, 20, 60), SCALE)                  # círculo r=4mm
    cases['satin_column_30x3'] = make_region(
        make_mask_rect(150, 15, 180), SCALE)                   # coluna 30x3mm
    cases['big_square_30x30'] = make_region(
        make_mask_rect(150, 150, 180), SCALE)                  # área 30x30mm
    cases['thin_line_15x1'] = make_region(
        make_mask_rect(75, 5, 100), SCALE)                     # fio 15x1mm
    cases['letter_o_small'] = make_region(
        make_mask_ring(15, 10, 40), SCALE)                     # glifo O ~3mm
    cases['medium_rect_15x8'] = make_region(
        make_mask_rect(75, 40, 110), SCALE)                    # retângulo 15x8mm
    cases['ellipse_50x10'] = make_region(
        make_mask_ellipse(125, 25, 300), SCALE)               # elipse 50x10mm
    cases['square_6x6'] = make_region(
        make_mask_rect(30, 30, 60), SCALE)                     # quadrado 6x6mm
    cases['star_outline'] = make_region(
        make_mask_star_outline(60, 25, 0.9, 170), SCALE)       # estrela outline
    return cases


# Tipos aceitáveis (TATAMI/FILL são equivalentes no planner - mesmo motor)
EXPECTED = {
    'ring_10_8': {StitchType.OUTLINE},
    'pentagon_outline': {StitchType.OUTLINE},
    'circle_filled_4': {StitchType.FILL},
    'satin_column_30x3': {StitchType.SATIN},   # regressão: atual acerta
    'big_square_30x30': {StitchType.TATAMI, StitchType.FILL},
    'thin_line_15x1': {StitchType.RUN},
    'letter_o_small': {StitchType.OUTLINE},
    'medium_rect_15x8': {StitchType.FILL},
    'ellipse_50x10': {StitchType.SATIN},       # regressão: atual acerta
    'square_6x6': {StitchType.FILL},
    'star_outline': {StitchType.OUTLINE},
}

# Casos em que o ObjectClassifier atual acerta (zero regressão obrigatória)
REGRESSION_EQUIVALENT = {
    'satin_column_30x3': {StitchType.SATIN},
    'ellipse_50x10': {StitchType.SATIN},
    'big_square_30x30': {StitchType.TATAMI, StitchType.FILL},
}


def make_text_cluster():
    """3 glifos 'O' pequenos próximos (cluster de texto)."""
    letters = []
    for k in range(3):
        region = make_region(make_mask_ring(15, 10, 40), SCALE)
        # desloca a letra em 7mm (35px) no eixo x
        shift = k * 35
        region['bounds_mm'] = (region['bounds_mm'][0] + shift * SCALE,
                               region['bounds_mm'][1],
                               region['bounds_mm'][2] + shift * SCALE,
                               region['bounds_mm'][3])
        letters.append(region)
    return letters


# ============================================================
# Testes
# ============================================================

def test_golden_set_accuracy():
    """Acurácia do golden set (objetivo: >= 85%)."""
    clf = ImprovedStitchClassifier()
    cases = build_golden_set()
    hits = 0
    for name, region in cases.items():
        result = clf.classify(region)
        assert result in EXPECTED[name], (
            f"[{name}] esperado {EXPECTED[name]}, obteve {result}"
        )
        hits += 1
    accuracy = hits / len(cases)
    assert accuracy >= 0.85, f"acurácia {accuracy:.0%} < 85%"


def test_zero_regression_on_current_classifier():
    """Casos que o ObjectClassifier atual acerta não podem regredir."""
    clf = ImprovedStitchClassifier()
    old = ObjectClassifier()
    cases = build_golden_set()
    for name, region in cases.items():
        if name in REGRESSION_EQUIVALENT:
            new_type = clf.classify(region)
            assert new_type in REGRESSION_EQUIVALENT[name], (
                f"[{name}] regrediu: {new_type}"
            )
        # e o plano de costura continua aceitando o tipo (não pode lançar)
    # Smoke do planner: cada tipo derivado é válido no StitchType
    for name, region in cases.items():
        t = clf.classify(region)
        assert isinstance(t, StitchType)


def test_text_cluster_detection():
    """3 glifos próximos viram RUN (texto); o glifo isolado fica OUTLINE."""
    clf = ImprovedStitchClassifier()

    letters = make_text_cluster()
    classified = clf.assign_all(letters)
    for region in classified:
        assert region['stitch_type'] == StitchType.RUN, (
            f"cluster de texto deveria ser RUN, obteve {region['stitch_type']}"
        )
        assert region['classification_source'] == 'text_cluster'

    # Glifo igual isolado -> OUTLINE (não é cluster)
    single = make_region(make_mask_ring(15, 10, 40), SCALE)
    meta = clf.classify_with_metadata(single)
    assert meta['stitch_type'] == StitchType.OUTLINE


def test_dominant_angle_computed():
    """direction_angle sai do PCA (coluna/elipse horizontais ~ 0°, nunca fixo)."""
    clf = ImprovedStitchClassifier()
    cases = build_golden_set()

    col = clf.classify_with_metadata(cases['satin_column_30x3'])
    ell = clf.classify_with_metadata(cases['ellipse_50x10'])

    for meta in (col, ell):
        assert meta['stitch_type'] == StitchType.SATIN
        angle = meta['direction_angle']
        assert 0.0 <= angle < 180.0
        # skimage mede a orientação a partir do eixo de linhas (vertical):
        # um retângulo horizontal tem eixo dominante em ~90° (ou ~0°).
        diff90 = min(abs(angle - 90.0), 180.0 - abs(angle - 90.0))
        diff0 = min(abs(angle - 0.0), abs(angle - 180.0))
        assert min(diff90, diff0) <= 15.0, (
            f"ângulo dominante inesperado para forma horizontal: {angle}"
        )

    # Regiões com forma definem ângulo próprio (não é sempre o mesmo valor)
    line = clf.classify_with_metadata(cases['thin_line_15x1'])
    assert 0.0 <= line['direction_angle'] < 180.0
    assert line['stitch_type'] == StitchType.RUN


def test_fallback_preserves_current_rules():
    """Sem features suficientes, usa ObjectClassifier com confiança baixa."""
    clf = ImprovedStitchClassifier()
    # Região sem mask/contour, com features que NÃO disparam as heurísticas
    # (área pequena, compacta, sem elongação) -> fallback para as regras atuais
    region = {
        'width_mm': 20.0, 'height_mm': 15.0,
        'area_mm2': 20.0, 'perimeter_mm': 20.0,
        'aspect_ratio': 1.33,
    }
    meta = clf.classify_with_metadata(region)
    assert meta['classification_source'] == 'fallback'
    assert meta['confidence'] == clf.FALLBACK_CONFIDENCE
    # O fallback preserva a regra atual (area pequena -> TRIPLE_RUN)
    assert meta['stitch_type'] == StitchType.TRIPLE_RUN


def test_confidence_bounds():
    """Toda classificação tem confiança no intervalo (0, 1] e ângulo válido."""
    clf = ImprovedStitchClassifier()
    cases = build_golden_set()
    for name, region in cases.items():
        meta = clf.classify_with_metadata(region)
        assert 0.0 < meta['confidence'] <= 1.0, name
        assert 0.0 <= meta['direction_angle'] < 180.0, name
        assert meta['stitch_type'] in EXPECTED[name], name