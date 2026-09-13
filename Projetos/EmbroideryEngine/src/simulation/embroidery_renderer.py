"""
FASE 19 - Embroidery Renderer (Simulador Visual de Bordado Realista)

Renderiza um EmbroideryDesign como imagem (PIL) de bordado costurado.

Diferenças principais em relação ao stitch_preview.py (FASE 14):
- Saída é imagem (PIL), não janela tkinter → funciona headless e exportável.
- Cada stitch é um segmento de reta (do ponto anterior ao atual), nunca um ponto.
- Espessura do fio proporcional à densidade do objeto (0.4mm ~= 3px a 10px/mm).
- Sobreposição real: pontos desenhados em ordem sequencial (posteriores por cima).
- Underlay desenhado primeiro, com largura e opacidade reduzidas.
- JUMP/TRIM/COLOR_CHANGE/TIE cortam o fio: nenhuma linha visível (agulha sobe).
- Anti-aliasing por supersampling (2x) + downscale LANCZOS.

Contrato de entrada (modelo real do projeto):
    EmbroideryDesign
        .objects: List[EmbroideryObject]
    EmbroideryObject
        .color: ThreadColor (r, g, b)
        .color_index: int
        .density: float        # espaçamento em mm (0.4 típico p/ fill)
        .stitch_length: float  # mm
        .stitch_type: StitchType
        .underlay_type: UnderlayType
        .underlay_density: float
        .visible: bool
        .generated_stitches: Optional[StitchPath]
    StitchPath
        .points: List[StitchPoint]  # x, y em mm; command: StitchCommand
    StitchCommand
        STITCH=0, JUMP=1, TRIM=2, COLOR_CHANGE=3, SEQUIN=4,
        START=5, END=6, NEEDLE_UP=7, NEEDLE_DOWN=8, TIE_IN=9, TIE_OFF=10

Observações honestas do modelo:
- Não existe classe StitchRegion; a entrada real é EmbroideryDesign/EmbroideryObject.
- NÃO existe ângulo por ponto (apenas direction_angle por objeto).
  O ângulo de cada stitch é derivado por atan2 entre pontos consecutivos.
- O underlay NÃO é marcado nos pontos: o planner concatena
  path(underlay) + path(main), tudo como STITCH. Este módulo separa por
  heurística de "joelho" (mudança estatística no comprimento do stitch
  na primeira metade do path). Documentado em _estimate_underlay_split.
"""

from __future__ import annotations

import math
import statistics
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject
from ..core.stitches.stitch_primitives import StitchCommand

# ============================================================
# Constantes de renderização
# ============================================================

MAX_SIDE_PX = 2400          # lado máximo da imagem de saída
MAX_PX_PER_MM = 10.0        # resolução máxima (0.4mm -> ~3px de fio)
MIN_THREAD_WIDTH_PX = 1.0   # largura mínima do fio
MAX_THREAD_WIDTH_PX = 6.0   # largura máxima do fio
THREAD_WIDTH_FACTOR = 0.75  # fio = densidade_mm * px_per_mm * 0.75

UNDERLAY_ALPHA = 100        # opacidade do underlay (0-255)
UNDERLAY_WIDTH_RATIO = 0.55 # largura do underlay em relação ao fio principal

FABRIC_BG = (245, 240, 232, 255)  # tecido claro (mesma base do stitch_preview)

_CUT_COMMANDS = frozenset({
    StitchCommand.JUMP,
    StitchCommand.TRIM,
    StitchCommand.COLOR_CHANGE,
    StitchCommand.SEQUIN,
    StitchCommand.START,
    StitchCommand.END,
    StitchCommand.NEEDLE_UP,
    StitchCommand.NEEDLE_DOWN,
    StitchCommand.TIE_OFF,
})
"""Comandos que quebram a linha visível (a agulha levanta / o fio corta)."""

_DRAW_COMMANDS = frozenset({StitchCommand.STITCH, StitchCommand.TIE_IN})
"""Comandos que produzem fio visível."""


# ============================================================
# Heurísticas auxiliares
# ============================================================

def stitch_lengths(points: Sequence[object]) -> List[float]:
    """Comprimento de cada stitch costurado (consecutivos STITCH/TIE_IN)."""
    lengths: List[float] = []
    prev = None
    for pt in points:
        if pt.command in _DRAW_COMMANDS:
            if prev is not None:
                dx = pt.x - prev.x
                dy = pt.y - prev.y
                lengths.append(math.hypot(dx, dy))
            prev = pt
    return lengths


def _moving_average(values: Sequence[float], window: int) -> List[Optional[float]]:
    """Média móvel simples; bordas recebem None."""
    if window <= 1 or not values:
        return list(values) if window <= 1 else [None] * len(values)
    out: List[Optional[float]] = [None] * len(values)
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= window:
            acc -= values[i - window]
        if i >= window - 1:
            out[i] = acc / window
    return out


def estimate_underlay_split(
    points: Sequence[object],
    density_mm: float = 0.4,
    min_stitches: int = 8,
) -> int:
    """
    Estima quantos pontos iniciais do StitchPath são underlay.

    O StitchPlanner concatena underlay + main no mesmo path (sem marcação).
    O underlay (zigzag/double_zigzag/fill) cruza a forma de um lado ao outro,
    gerando stitches longos; o preenchimento principal (tatami/fill denso)
    gera stitches mais curtos e mais regulares. A fronteira é o "joelho" de
    maior queda na média móvel do comprimento na primeira metade do path.

    Retorna o índice (em `points`) do primeiro ponto do main. 0 = sem underlay.
    """
    n = len(points)
    if n < min_stitches:
        return 0

    lengths = stitch_lengths(points)
    if len(lengths) < min_stitches:
        return 0

    # Compatibilidade com near-zero density (evita divisão por zero abaixo).
    density_mm = density_mm if density_mm and density_mm > 0 else 0.4

    # Janela de estimativa do "comprimento típico do underlay": ~1mm de
    # costura em pontos, mínimo 5, máximo 25.
    window = max(5, min(25, int(round(1.0 / density_mm))))

    # Trabalhamos apenas na primeira metade dos stitches: o underlay, por
    # construção do planner, vem antes do main.
    half = max(min_stitches, len(lengths) // 2)

    # Baseline = comprimento mediano do começo do path (amostra do underlay).
    # O primeiro stitch do main é significativamente mais curto que o
    # unterlay (passadas largas) — a fronteira é o primeiro stitch curto.
    baseline = statistics.median(lengths[:window])
    baseline = baseline if baseline and baseline > 0 else 0.4

    best_idx = 0
    for i in range(window, half):
        # Salto proporcional: main costuma ter < 60% do comprimento do
        # underlay. Tolerância evita disparo por ruído pequeno.
        if lengths[i] < baseline * 0.55:
            best_idx = i
            break

    # Mapeia índice de stitch de volta para índice de ponto.
    stitch_ordinal = 0
    for pi, pt in enumerate(points):
        if pt.command in _DRAW_COMMANDS:
            if stitch_ordinal == best_idx:
                return max(0, pi)
            stitch_ordinal += 1
    return 0


def compute_scale(design: EmbroideryDesign, max_side_px: int = MAX_SIDE_PX,
                  max_px_per_mm: float = MAX_PX_PER_MM) -> float:
    """Resolução em px/mm: nunca estoura max_side_px nem max_px_per_mm."""
    w = max(design.width_mm, 1.0)
    h = max(design.height_mm, 1.0)
    scale = max_side_px / max(w, h)
    return min(max_px_per_mm, scale)


# ============================================================
# Renderer principal
# ============================================================

class EmbroideryRenderer:
    """
    Renderiza designs de bordado como imagem costurada (PIL).

    Parâmetros:
        max_side_px: lado máximo da imagem (padrão 2400).
        max_px_per_mm: resolução máxima (padrão 10).
        background: tupla RGBA do fundo; None = transparente.
        show_underlay: desenha o underlay com opacidade/espessura reduzidas.
        show_jumps: desenha jumps como linha tracejada (diagnóstico).
        ss: fator de supersampling (2 = anti-aliasing forte).
    """

    def __init__(self, max_side_px: int = MAX_SIDE_PX,
                 max_px_per_mm: float = MAX_PX_PER_MM,
                 background: Optional[Tuple[int, int, int, int]] = FABRIC_BG,
                 show_underlay: bool = True,
                 show_jumps: bool = False,
                 ss: int = 2):
        self.max_side_px = max_side_px
        self.max_px_per_mm = max_px_per_mm
        self.background = background
        self.show_underlay = show_underlay
        self.show_jumps = show_jumps
        self.ss = max(1, int(ss))

    # --------------------------------------------------------
    # API pública
    # --------------------------------------------------------

    def render(self, design: EmbroideryDesign,
               progress_callback=None) -> Image.Image:
        """Renderiza o design completo (imagem RGBA)."""
        # A margem (8%) entra no teto de escala: conteúdo + margem <= max_side.
        # Com MAX_SIDE_PX=2400 e margem 8%, o conteúdo cabe em 2400/1.16.
        margin_ratio = 0.08
        content_cap = self.max_side_px / (1.0 + 2.0 * margin_ratio)
        scale = compute_scale(design, content_cap, self.max_px_per_mm)
        w_px = max(1, int(round(design.width_mm * scale)))
        h_px = max(1, int(round(design.height_mm * scale)))

        # Centraliza o design no canvas com margem de 8%.
        margin = int(round(max(w_px, h_px) * margin_ratio))
        canvas_w = w_px + margin * 2
        canvas_h = h_px + margin * 2
        canvas_w += canvas_w % 2  # par p/ downscale estável
        canvas_h += canvas_h % 2

        # Garantia do teto: arredondamentos da margem podem estourar 1-2px.
        shrink = min(1.0, self.max_side_px / max(canvas_w, canvas_h))
        if shrink < 1.0:
            scale *= shrink
            w_px = max(1, int(round(design.width_mm * scale)))
            h_px = max(1, int(round(design.height_mm * scale)))
            margin = int(round(max(w_px, h_px) * margin_ratio))
            canvas_w = w_px + margin * 2
            canvas_h = h_px + margin * 2
            canvas_w += canvas_w % 2
            canvas_h += canvas_h % 2

        # Origem em mm relativa ao canto superior esquerdo do design.
        min_x = design.bounding_box[0]
        min_y = design.bounding_box[1]
        if not design.objects:
            min_x = min_y = 0.0
        origin_px = (margin - min_x * scale, margin - min_y * scale)

        img = self._make_canvas(canvas_w, canvas_h)
        draw = ImageDraw.Draw(img)

        total = len([o for o in design.objects if o.visible]) or 1
        done = 0
        for obj in design.objects:
            if not obj.visible or not obj.generated_stitches:
                done += 1
                continue
            self._draw_object(draw, img, obj, scale, origin_px)
            done += 1
            if progress_callback:
                progress_callback(done / total)

        if self.ss > 1:
            img = img.resize((canvas_w // self.ss, canvas_h // self.ss),
                             Image.LANCZOS)
        return img

    def render_object(self, obj: EmbroideryObject,
                      px_per_mm: float = MAX_PX_PER_MM) -> Image.Image:
        """
        Renderiza um objeto isolado em seu bounding box.
        Útil para inspeção/depuração e testes unitários.
        """
        scale = px_per_mm
        w_px = max(1, int(round(max(obj.width, 1.0) * scale)))
        h_px = max(1, int(round(max(obj.height, 1.0) * scale)))
        margin = 8
        canvas_w = w_px + margin * 2
        canvas_h = h_px + margin * 2
        origin_px = (margin - obj.bounds[0] * scale,
                     margin - obj.bounds[1] * scale)

        img = self._make_canvas(canvas_w, canvas_h)
        draw = ImageDraw.Draw(img)
        self._draw_object(draw, img, obj, scale, origin_px)
        if self.ss > 1:
            img = img.resize((canvas_w // self.ss, canvas_h // self.ss),
                             Image.LANCZOS)
        return img

    # --------------------------------------------------------
    # Internos
    # --------------------------------------------------------

    def _make_canvas(self, w: int, h: int) -> Image.Image:
        img = Image.new("RGBA", (w * self.ss, h * self.ss),
                        self.background if self.background else (0, 0, 0, 0))
        return img

    def _draw_object(self, draw: ImageDraw.ImageDraw, img: Image.Image,
                     obj: EmbroideryObject, scale: float,
                     origin_px: Tuple[float, float]):
        points = obj.generated_stitches.points
        if not points:
            return

        rgb = obj.color.rgb if obj.color else (0, 0, 0)

        # Largura do fio principal proporcional à densidade.
        density = obj.density if obj.density and obj.density > 0 else 0.4
        thread_w = density * scale * THREAD_WIDTH_FACTOR
        thread_w = max(MIN_THREAD_WIDTH_PX,
                       min(MAX_THREAD_WIDTH_PX, thread_w))

        # ----- Underlay (primeiro, mais fino e translúcido) -----
        main_start = 0
        if obj.underlay_type.value != "none":
            split = estimate_underlay_split(points, density)
            if split > 0:
                main_start = split
                if self.show_underlay:
                    underlay_w = max(1.0, thread_w * UNDERLAY_WIDTH_RATIO)
                    under_color = (rgb[0], rgb[1], rgb[2], UNDERLAY_ALPHA)
                    self._draw_segments(draw, points[:split], scale, origin_px,
                                        under_color, underlay_w)

        # ----- Costura principal -----
        self._draw_segments(draw, points[main_start:], scale, origin_px,
                            (rgb[0], rgb[1], rgb[2], 255), thread_w)

        # ----- Jumps (diagnóstico opcional) -----
        if self.show_jumps:
            self._draw_jumps(draw, points, scale, origin_px)

    def _draw_segments(self, draw: ImageDraw.ImageDraw,
                       points: Sequence[object], scale: float,
                       origin_px: Tuple[float, float],
                       color: Tuple[int, int, int, int],
                       width: float):
        """Desenha cada stitch como segmento do último ponto ao atual.

        Comandos de corte (JUMP/TRIM/COLOR_CHANGE/TIE_OFF/etc.) não produzem
        linha; o próximo STITCH começa um novo segmento a partir dele.
        """
        last_x: Optional[float] = None
        last_y: Optional[float] = None
        px_per_mm = scale
        ox, oy = origin_px
        w = width * self.ss
        # Desenha na imagem em supersampling com o alpha desejado; o downscale
        # LANCZOS ao final produz o anti-aliasing (bordas de fio suaves).
        stroke_color = color

        for pt in points:
            if pt.command in _DRAW_COMMANDS:
                # Coordenadas escaladas pelo supersampling: o desenho ocupa o
                # canvas grande e o downscale LANCZOS suaviza as bordas.
                s = self.ss
                cx = (pt.x * px_per_mm * s) + ox * s
                cy = (pt.y * px_per_mm * s) + oy * s
                if last_x is not None:
                    draw.line([last_x, last_y, cx, cy], fill=stroke_color,
                              width=max(1, int(round(w))), joint="curve")
                last_x, last_y = cx, cy
            else:
                # Corte: nenhuma linha. O próximo STITCH inicia novo fio.
                last_x = last_y = None

    def _draw_jumps(self, draw: ImageDraw.ImageDraw,
                    points: Sequence[object], scale: float,
                    origin_px: Tuple[float, float]):
        """Jumps em linha tracejada azul (apenas diagnóstico)."""
        ox, oy = origin_px
        s = self.ss
        prev = None
        for pt in points:
            if pt.command == StitchCommand.JUMP and prev is not None:
                x1 = prev.x * scale * s + ox * s
                y1 = prev.y * scale * s + oy * s
                x2 = pt.x * scale * s + ox * s
                y2 = pt.y * scale * s + oy * s
                draw.line([x1, y1, x2, y2], fill=(74, 144, 217, 255),
                          width=max(1, int(round(self.ss))),
                          joint="curve")
                # tracejado simulado por pequenos espaços (4 pontos no meio)
                # não é aplicado aqui por simplicidade; a linha cheia serve
                # apenas para diagnóstico rápido.
            if pt.command in _DRAW_COMMANDS:
                prev = pt


# ============================================================
# Atalhos funcionais
# ============================================================

def render_design(design: EmbroideryDesign,
                  max_side_px: int = MAX_SIDE_PX,
                  max_px_per_mm: float = MAX_PX_PER_MM,
                  background: Optional[Tuple[int, int, int, int]] = FABRIC_BG,
                  show_underlay: bool = True,
                  show_jumps: bool = False,
                  ss: int = 2) -> Image.Image:
    """Atalho: cria renderer e renderiza o design."""
    renderer = EmbroideryRenderer(
        max_side_px=max_side_px,
        max_px_per_mm=max_px_per_mm,
        background=background,
        show_underlay=show_underlay,
        show_jumps=show_jumps,
        ss=ss,
    )
    return renderer.render(design)


def render_object(obj: EmbroideryObject,
                  px_per_mm: float = MAX_PX_PER_MM,
                  background: Optional[Tuple[int, int, int, int]] = None,
                  show_underlay: bool = True,
                  ss: int = 2) -> Image.Image:
    """Atalho: renderiza um objeto isolado."""
    renderer = EmbroideryRenderer(
        max_px_per_mm=px_per_mm, background=background,
        show_underlay=show_underlay, ss=ss,
    )
    return renderer.render_object(obj, px_per_mm=px_per_mm)


# ============================================================
# Demonstração / CLI
# ============================================================

def _build_demo_design() -> EmbroideryDesign:
    """Design sintético mínimo para demonstração e self-test."""
    import math as _m

    from ..core.design.embroidery_design import (
        EmbroideryDesign, EmbroideryObject, StitchType,
        UnderlayType, ThreadColor, ThreadPalette,
    )
    from ..core.stitches.stitch_primitives import StitchPath, StitchCommand

    design = EmbroideryDesign(name="Demonstração Renderer",
                              width_mm=80, height_mm=80)
    design.palette = ThreadPalette(name="Demo", threads=[
        ThreadColor("Azul", r=30, g=80, b=200),
        ThreadColor("Vermelho", r=200, g=40, b=40),
        ThreadColor("Verde", r=40, g=160, b=60),
    ])

    def _tatami(contour, color_index, density, angle):
        """Varredura em zigue-zague (para o demo — não substitui o motor)."""
        path = StitchPath()
        angle_rad = _m.radians(angle)
        ca, sa = _m.cos(angle_rad), _m.sin(angle_rad)
        rotated = [(p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca)
                   for p in contour]
        min_y = min(p[1] for p in rotated)
        max_y = max(p[1] for p in rotated)
        direction = 1
        y = min_y + density / 2
        while y <= max_y:
            xs = []
            n = len(rotated)
            for i in range(n):
                j = (i + 1) % n
                y1, y2 = rotated[i][1], rotated[j][1]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if y1 != y2:
                        x = rotated[i][0] + (y - y1) / (y2 - y1) * (
                            rotated[j][0] - rotated[i][0])
                        xs.append(x)
            if len(xs) >= 2:
                xs.sort()
                pts = [(xs[0], y), (xs[-1], y)]
                if direction == -1:
                    pts = list(reversed(pts))
                for px, py in pts:
                    ox = px * ca + py * sa
                    oy = -px * sa + py * ca
                    path.add_stitch_absolute(ox, oy, StitchCommand.STITCH)
            direction *= -1
            y += density
        return path

    cx, cy = 40, 40
    radius = 18
    pentagon = [(cx + radius * _m.cos(_m.radians(72 * i - 90)),
                 cy + radius * _m.sin(_m.radians(72 * i - 90)))
                for i in range(5)]
    obj1 = EmbroideryObject(name="Pentágono", stitch_type=StitchType.TATAMI,
                            color_index=0, color=design.palette.threads[0],
                            contour=pentagon,
                            bounds=(cx - radius, cy - radius, cx + radius, cy + radius),
                            density=0.4, underlay_type=UnderlayType.DOUBLE_ZIGZAG)
    obj1.generated_stitches = _tatami(pentagon, 0, 0.4, 0)
    design.objects.append(obj1)

    tri_cx, tri_cy = 16, 66
    tri_r = 10
    triangle = [(tri_cx + tri_r * _m.cos(_m.radians(120 * i - 90)),
                 tri_cy + tri_r * _m.sin(_m.radians(120 * i - 90)))
                for i in range(3)]
    obj2 = EmbroideryObject(name="Triângulo", stitch_type=StitchType.FILL,
                            color_index=1, color=design.palette.threads[1],
                            contour=triangle,
                            bounds=(tri_cx - tri_r, tri_cy - tri_r, tri_cx + tri_r, tri_cy + tri_r),
                            density=0.4, underlay_type=UnderlayType.ZIGZAG)
    obj2.generated_stitches = _tatami(triangle, 0, 0.4, 45)
    design.objects.append(obj2)

    rect = [(62, 14), (76, 14), (76, 26), (62, 26)]
    obj3 = EmbroideryObject(name="Retângulo", stitch_type=StitchType.TATAMI,
                            color_index=2, color=design.palette.threads[2],
                            contour=rect, bounds=(62, 14, 76, 26),
                            density=0.4, underlay_type=UnderlayType.ZIGZAG)
    obj3.generated_stitches = _tatami(rect, 0, 0.4, 10)
    design.objects.append(obj3)

    design.recalculate_metadata()
    return design


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: python -m src.simulation.embroidery_renderer [imagem] [saida.png]"""
    import os
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)

    out_path = None
    img_path = None
    if argv:
        img_path = argv[0]
        out_path = argv[1] if len(argv) > 1 else None

    if img_path and os.path.exists(img_path):
        from ..pipeline.digitizer_pipeline import DigitizerPipeline
        design = DigitizerPipeline(density=0.4, max_colors=8,
                                   scale_mm=0.2).digitize(img_path)
        print(f"Pipeline: {design.name} "
              f"({design.width_mm:.1f}x{design.height_mm:.1f}mm, "
              f"{design.total_stitches} pontos)")
    else:
        if img_path:
            print(f"Arquivo não encontrado: {img_path} — usando demo sintética")
        design = _build_demo_design()
        print(f"Demo sintética: {design.name} "
              f"({design.width_mm:.1f}x{design.height_mm:.1f}mm, "
              f"{design.total_stitches} pontos)")

    image = render_design(design)
    if not out_path:
        out_path = "embroidery_render.png"
    image.save(out_path)
    print(f"Imagem salva: {out_path} "
          f"({image.width}x{image.height}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())