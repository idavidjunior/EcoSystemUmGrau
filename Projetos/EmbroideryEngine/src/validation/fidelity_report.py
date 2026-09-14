"""
Fidelity Report + Round-trip validation (missão LER).

Compara o bordado renderizado contra a imagem original e valida que um
design sobrevive à escrita/leitura de arquivo de máquina.

Funções públicas:
  - build_report(design, original_image_path, output_png_path=None,
                 output_json_path=None) -> dict
      Renderiza o design, alinha a imagem original (contain + centro) ao
      mesmo canvas do render, calcula SSIM global e DICE por cor,
      salva PNG composto (original | render | overlay) e JSON.

  - verify_roundtrip(design, pes_path=None, writer='pyembroidery') -> dict
      Escreve o design em PES (writer='pyembroidery' usa pyembroidery;
      writer='native' usa PESWriter do projeto) e lê de volta com
      pyembroidery (preferido), comparando contagem e posição dos
      stitches. Retorna erro máximo em mm.

Evidências em vez de opinião: toda métrica sai com número e caminho
dos artefatos gerados.
"""

import json
import os
import tempfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from ..core.design.embroidery_design import EmbroideryDesign
from ..core.stitches.stitch_primitives import StitchCommand
from ..simulation.embroidery_renderer import FABRIC_BG, render_design

try:
    import pyembroidery
    HAS_PYEMBROIDERY = True
except ImportError:  # pragma: no cover
    pyembroidery = None
    HAS_PYEMBROIDERY = False

try:
    from skimage.metrics import structural_similarity
    HAS_SKIMAGE = True
except ImportError:  # pragma: no cover
    structural_similarity = None
    HAS_SKIMAGE = False

# Tolerância de cor (distância euclidiana RGB) para máscara por cor.
# O render usa anti-aliasing (ss=2) e o original pode ter JPEG/noise,
# então 80 foi calibrado empiricamente para casar ÁREAS, não bordas.
COLOR_TOLERANCE = 80

# Lado máximo dos painéis do PNG composto (performance e leitura).
COMPOSITE_PANEL_HEIGHT = 480


# ------------------------------------------------------------
# Aritmética simples (testável isoladamente)
# ------------------------------------------------------------

def dice_coefficient(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """DICE = 2*|A∩B| / (|A|+|B|). 1.0 = idêntico, 0.0 = disjunto."""
    a = mask_a > 0
    b = mask_b > 0
    inter = int(np.count_nonzero(a & b))
    total = int(np.count_nonzero(a)) + int(np.count_nonzero(b))
    if total == 0:
        return 1.0  # ambos vazios: concordam perfeitamente
    return 2.0 * inter / total


def color_mask(img: Image.Image, rgb: tuple, tolerance: int = COLOR_TOLERANCE) -> np.ndarray:
    """Máscara booleana de pixels próximos da cor (distância euclidiana RGB)."""
    arr = np.asarray(img.convert("RGB"), dtype=np.int32)
    diff = np.abs(arr - np.array(rgb, dtype=np.int32))
    dist = np.sqrt((diff ** 2).sum(axis=2))
    return dist <= tolerance


def ssim_gray(img_a: Image.Image, img_b: Image.Image) -> float:
    """SSIM em escala de cinza (skimage; fallback numpy se ausente)."""
    a = np.asarray(img_a.convert("L"), dtype=np.float64)
    b = np.asarray(img_b.convert("L"), dtype=np.float64)
    if HAS_SKIMAGE:
        return float(structural_similarity(a, b, data_range=255.0))
    # Fallback: SSIM global (janela única) — aproximação honesta.
    mu_a, mu_b = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - mu_a) * (b - mu_b)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float((2 * mu_a * mu_b + c1) * (2 * cov + c2) /
                 ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2)))


def align_to_render(original: Image.Image, render: Image.Image) -> Image.Image:
    """Redimensiona `original` para caber no canvas do render (contain),
    com letterbox branco e centralizado. Preserva o aspect ratio."""
    render = render.convert("RGBA")
    w, h = render.size
    orig = original.convert("RGBA")
    ow, oh = orig.size
    if ow == 0 or oh == 0:
        raise ValueError("Imagem original vazia")

    scale = min(w / ow, h / oh)
    nw, nh = max(1, int(round(ow * scale))), max(1, int(round(oh * scale)))
    orig = orig.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    canvas.paste(orig, ((w - nw) // 2, (h - nh) // 2), orig)
    return canvas


def avg_stitch_length_mm(design: EmbroideryDesign) -> float:
    """Comprimento médio (mm) dos segmentos STITCH consecutivos."""
    lengths = []
    for obj in design.objects:
        pts = [p for p in obj.generated_stitches.points
               if p.command == StitchCommand.STITCH]
        for i in range(1, len(pts)):
            lengths.append(pts[i - 1].distance_to(pts[i]))
    if not lengths:
        return 0.0
    return sum(lengths) / len(lengths)


# ------------------------------------------------------------
# Escrita atômica (regra do ecossistema)
# ------------------------------------------------------------

def _write_atomic(path: str, data: bytes) -> str:
    path = os.path.abspath(path)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".fid_", suffix=".tmp", dir=d or ".")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def _write_atomic_text(path: str, text: str) -> str:
    return _write_atomic(path, text.encode("utf-8"))


# ------------------------------------------------------------
# build_report
# ------------------------------------------------------------

class _ThreadView:
    """Vista mínima de um fio (name, r, g, b) — aceita palette ou derivada."""

    __slots__ = ("name", "r", "g", "b")

    def __init__(self, name, r, g, b):
        self.name = name
        self.r = r
        self.g = g
        self.b = b


def _effective_threads(design) -> list:
    """Threads da paleta; se vazia, deriva das cores dos objetos visíveis.

    Designs criados manualmente (sem digitizer) podem não popular a palette;
    fallback garante DICE por cor e round-trip funcionando nesses casos.
    """
    if design.palette.threads:
        return list(design.palette.threads)
    seen = []
    for obj in design.objects:
        if not obj.visible:
            continue
        color = getattr(obj, "color", None)
        if color is None:
            continue
        rgb = (int(color.r), int(color.g), int(color.b))
        if rgb not in seen:
            seen.append(rgb)
    return [
        _ThreadView(f"cor_{i}", r, g, b)
        for i, (r, g, b) in enumerate(seen)
    ]


def build_report(
    design: EmbroideryDesign,
    original_image_path: str,
    output_png_path: str = None,
    output_json_path: str = None,
    max_side_px: int = 2400,
    ss: int = 2,
) -> dict:
    """Renderiza o design, compara com a imagem original e salva artefatos.

    Retorna dict com métricas:
      design (resumo), metrics.ssim, metrics.dice_by_color,
      metrics.avg_stitch_length_mm, warnings e caminhos dos artefatos.
    """
    if not os.path.isfile(original_image_path):
        raise FileNotFoundError(f"Imagem original não encontrada: {original_image_path}")

    render = render_design(design, max_side_px=max_side_px, ss=ss)
    original = Image.open(original_image_path)
    original_aligned = align_to_render(original, render)

    # --- SSIM global (em gray, mesma geometria) ---------------------
    ssim_val = ssim_gray(original_aligned, render.convert("RGBA"))

    # --- DICE por cor da paleta (ou cores derivadas dos objetos) -------
    threads = _effective_threads(design)
    dice_by_color = []
    for idx, thread in enumerate(threads):
        rgb = (thread.r, thread.g, thread.b)
        m_orig = color_mask(original_aligned, rgb)
        m_render = color_mask(render, rgb)
        dice_by_color.append({
            "color": [int(c) for c in rgb],
            "label": thread.name or f"cor_{idx}",
            "dice": float(round(dice_coefficient(m_orig, m_render), 4)),
            "area_original_px": int(np.count_nonzero(m_orig)),
            "area_render_px": int(np.count_nonzero(m_render)),
        })

    warnings = []
    if not HAS_SKIMAGE:
        warnings.append("skimage ausente; SSIM calculado por fallback numpy (aproximação)")

    report = {
        "design": {
            "name": design.name,
            "width_mm": float(design.width_mm),
            "height_mm": float(design.height_mm),
            "total_objects": int(len(design.objects)),
            "total_stitches": int(design.total_stitches),
            "total_colors": int(len(_effective_threads(design))),
        },
        "metrics": {
            "ssim": float(round(ssim_val, 4)),
            "dice_by_color": dice_by_color,
            "avg_stitch_length_mm": float(round(avg_stitch_length_mm(design), 3)),
        },
        "warnings": warnings,
        "artifacts": {},
    }

    # --- Artefatos ----------------------------------------------------
    png_path = output_png_path
    json_path = output_json_path
    if png_path is None and json_path is None:
        base = os.path.splitext(original_image_path)[0]
        png_path = base + "_fidelity.png"
        json_path = base + "_fidelity.json"

    if png_path:
        report["artifacts"]["composite_png"] = _composite_png(
            original_aligned, render, png_path)
    if json_path:
        report["artifacts"]["json"] = _write_atomic_text(
            json_path, json.dumps(report, indent=2, ensure_ascii=False))

    return report


def _composite_png(original, render, path: str) -> str:
    """Monta painel [original | render | overlay] e salva PNG."""
    render = render.convert("RGBA")
    overlay = Image.alpha_composite(original.convert("RGBA"), render)

    panels = [original.convert("RGBA"), render, overlay]
    h = min(COMPOSITE_PANEL_HEIGHT, max(p.size[1] for p in panels))
    scaled = []
    for p in panels:
        ratio = h / p.size[1]
        scaled.append(p.resize((max(1, int(p.size[0] * ratio)), h), Image.LANCZOS))

    total_w = sum(p.size[0] for p in scaled)
    strip = Image.new("RGBA", (total_w, h), (255, 255, 255, 255))
    x = 0
    for p in scaled:
        strip.paste(p, (x, 0))
        x += p.size[0]
        if x < total_w:
            draw = ImageDraw.Draw(strip)
            draw.line((x - 1, 0, x - 1, h), fill=(0, 0, 0, 80), width=2)

    _write_png_atomic(path, strip.convert("RGB"))
    return os.path.abspath(path)


def _write_png_atomic(path: str, img: Image.Image) -> str:
    """Salva imagem PNG com escrita atômica (tmp + os.replace)."""
    import io

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return _write_atomic(path, buf.getvalue())


# ------------------------------------------------------------
# verify_roundtrip
# ------------------------------------------------------------

def _design_to_pyembroidery_pattern(design: EmbroideryDesign):
    """Converte design para pyembroidery pattern em unidades 0.1mm.

    Usa a MESMA transformação do PESEncoder nativo (pt + centro) × 10,
    para que as unidades coincidam com o espaço do arquivo de máquina.
    """
    if not HAS_PYEMBROIDERY:
        raise ImportError("pyembroidery necessário para round-trip")
    pattern = pyembroidery.EmbPattern()
    for thread in _effective_threads(design):
        th = pyembroidery.EmbThread(description=thread.name)
        th.set_color(thread.r, thread.g, thread.b)
        pattern.add_thread(th)

    cx = design.width_mm / 2.0
    cy = design.height_mm / 2.0

    for obj in design.objects:
        if not obj.visible or not obj.generated_stitches:
            continue
        for pt in obj.generated_stitches.points:
            x = int(round((pt.x + cx) * 10.0))
            y = int(round((pt.y + cy) * 10.0))
            if pt.command == StitchCommand.STITCH:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            elif pt.command == StitchCommand.JUMP:
                pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
            elif pt.command == StitchCommand.TRIM:
                pattern.add_command(pyembroidery.TRIM)
            elif pt.command == StitchCommand.COLOR_CHANGE:
                pattern.add_stitch_absolute(pyembroidery.COLOR_CHANGE, x, y)
    pattern.add_command(pyembroidery.END)
    return pattern


def _read_stitches_from_pes(pes_path: str):
    """Lê PES e retorna lista de (x, y, command_int) em unidades 0.1mm."""
    pattern = pyembroidery.read_pes(pes_path)
    return list(pattern.stitches)


def _expected_stitches(design: EmbroideryDesign):
    """Lista esperada de (x, y, command) em 0.1mm (mesma transformação)."""
    cx = design.width_mm / 2.0
    cy = design.height_mm / 2.0
    rows = []
    for obj in design.objects:
        if not obj.visible or not obj.generated_stitches:
            continue
        for pt in obj.generated_stitches.points:
            x = int(round((pt.x + cx) * 10.0))
            y = int(round((pt.y + cy) * 10.0))
            if pt.command == StitchCommand.STITCH:
                rows.append((x, y, 0))
            elif pt.command == StitchCommand.JUMP:
                rows.append((x, y, 1))
            elif pt.command == StitchCommand.TRIM:
                rows.append((0, 0, 2))
            elif pt.command == StitchCommand.COLOR_CHANGE:
                rows.append((x, y, 3))
    return rows


def verify_roundtrip(
    design: EmbroideryDesign,
    pes_path: str = None,
    writer: str = "pyembroidery",
) -> dict:
    """Escreve PES e lê de volta, comparando stitches.

    writer:
      - 'pyembroidery' (padrão): usa pyembroidery para escrever — o
        circuit breaker de referência (gold standard).
      - 'native': usa PESWriter do projeto — documenta o desvio real
        do encoder nativo (hoje quebrado, ver warnings).

    Retorna dict com ok, contagens, erro máximo/médio (mm) e evidências.
    """
    if writer not in ("pyembroidery", "native"):
        raise ValueError(f"writer inválido: {writer!r}")

    if writer == "pyembroidery":
        if not HAS_PYEMBROIDERY:
            raise ImportError("pyembroidery necessário para round-trip gold standard")
        pattern = _design_to_pyembroidery_pattern(design)
        pes_path = pes_path or os.path.join("Temp", "roundtrip_gold.pes")
        pes_path = os.path.abspath(pes_path)
        d = os.path.dirname(pes_path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(suffix=".pes", dir=d or ".")
        os.close(fd)
        pyembroidery.write(pattern, tmp)
        os.replace(tmp, pes_path)
        wrote_size = os.path.getsize(pes_path)
    else:
        from ..formats.pes_encoder import PESWriter
        pes_path = pes_path or os.path.join("Temp", "roundtrip_native.pes")
        pes_path = os.path.abspath(pes_path)
        PESWriter.write(design, pes_path)
        wrote_size = os.path.getsize(pes_path)

    expected = _expected_stitches(design)
    warnings = []

    if not HAS_PYEMBROIDERY:
        warnings.append("pyembroidery ausente; leitura feita por PESReader nativo (não confiável)")

    try:
        if HAS_PYEMBROIDERY:
            read_rows = _read_stitches_from_pes(pes_path)
            reader = "pyembroidery"
        else:
            from ..formats.pes_reader import read_pes
            read_design = read_pes(pes_path)
            read_rows = [
                (int(round(p.x * 10)), int(round(p.y * 10)), int(p.command))
                for obj in read_design.objects for p in obj.generated_stitches.points
            ]
            reader = "pes_reader_nativo"
    except Exception as exc:  # noqa: BLE001 - relata falha controlada
        return {
            "ok": False,
            "writer": writer,
            "reader": "erro",
            "read_error": f"{type(exc).__name__}: {exc}",
            "stitches_expected": len(expected),
            "stitches_read": None,
            "max_error_mm": None,
            "mean_error_mm": None,
            "file_size": wrote_size,
            "pes_path": pes_path,
            "warnings": warnings,
        }

    # Comparação de fidelidade geométrica: apenas pontos de COSTURA
    # (comando STITCH=0). Jumps de entrada/saída são posicionamento normal
    # do PES e não representam o bordado.
    exp_stitches = [(x, y) for (x, y, cmd) in expected if cmd == 0]
    read_stitches = [(x, y) for (x, y, cmd) in read_rows if cmd == 0]

    errors_mm = []
    n = min(len(exp_stitches), len(read_stitches))
    exp_st = exp_stitches[:n]
    read_st = read_stitches[:n]
    for (ex, ey), (rx, ry) in zip(exp_st, read_st):
        errors_mm.append(((ex - rx) ** 2 + (ey - ry) ** 2) ** 0.5 / 10.0)

    max_err = max(errors_mm) if errors_mm else None
    mean_err = (sum(errors_mm) / len(errors_mm)) if errors_mm else None

    ok = (len(exp_stitches) == len(read_stitches) and max_err is not None
          and max_err <= 0.2)
    if len(exp_stitches) != len(read_stitches):
        warnings.append(
            f"contagem de stitches difere: esperado {len(exp_stitches)}, "
            f"lido {len(read_stitches)}"
        )
    if max_err is not None and max_err > 0.2:
        warnings.append(f"erro máximo {max_err:.2f}mm acima do limiar 0.2mm")

    return {
        "ok": ok,
        "writer": writer,
        "reader": reader,
        "stitches_expected": len(exp_stitches),
        "stitches_read": len(read_stitches),
        "max_error_mm": round(max_err, 3) if max_err is not None else None,
        "mean_error_mm": round(mean_err, 3) if mean_err is not None else None,
        "file_size": wrote_size,
        "pes_path": pes_path,
        "warnings": warnings,
    }