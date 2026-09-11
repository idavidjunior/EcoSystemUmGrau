"""
FASE 14 - Stitch Preview (Visualização de Bordado)

Janela tkinter com Canvas para visualizar o design de bordado antes de exportar.
Suporta zoom/pan, renderização por tipo de stitch, legenda e painel de informações.
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Optional

from ..core.design.embroidery_design import EmbroideryDesign, EmbroideryObject
from ..core.stitches.stitch_primitives import StitchCommand


BASE_PX_PER_MM = 3.0
STITCH_COLORS = {
    "stitch": "#000000",
    "jump": "#4A90D9",
    "trim": "#D94A4A",
    "color_change": "#9B59B6",
    "underlay": "#AAAAAA",
    "contour": "#888888",
    "fabric": "#F5F0E8",
    "hoop": "#CCCCCC",
    "grid": "#E0E0E0",
}


class StitchPreview:
    """Janela de preview de bordado."""

    def __init__(self, design: EmbroideryDesign):
        self.design = design
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._drag_start = None
        self._show_stitches = True
        self._show_jumps = False
        self._show_underlay = False
        self._show_contours = True
        self._show_grid = True

        self.root = tk.Tk()
        self.root.title("EmbroideryEngine — Stitch Preview")
        self.root.geometry("1100x700")

        self._build_ui()
        self._center_design()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, padx=2, pady=2)

        ttk.Button(toolbar, text="Fit", command=self.fit_to_view, width=4).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="1:1", command=self.zoom_1to1, width=4).pack(side=tk.LEFT, padx=1)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=4)

        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=STITCH_COLORS["fabric"],
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_move)
        self.canvas.bind("<Configure>", lambda e: self.render())

        self.root.bind("<f>", lambda e: self.fit_to_view())
        self.root.bind("<F>", lambda e: self.fit_to_view())
        self.root.bind("<plus>", lambda e: self.zoom_in())
        self.root.bind("<equal>", lambda e: self.zoom_in())
        self.root.bind("<minus>", lambda e: self.zoom_out())

        right_frame = ttk.Frame(main_frame, width=260)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        right_frame.pack_propagate(False)

        self._build_info_panel(right_frame)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        summary = self.design.stitch_summary
        status_text = (f"Objetos: {summary['objects']} | "
                       f"Cores: {summary['colors']} | "
                       f"Pontos: {summary['stitches']} | "
                       f"Jumps: {summary['jumps']} | "
                       f"Trims: {summary['trims']} | "
                       f"Tempo est.: {summary['estimated_time_seconds']:.0f}s")
        self.status_var = tk.StringVar(value=status_text)
        ttk.Label(status_frame, textvariable=self.status_var,
                  relief=tk.SUNKEN, anchor=tk.W, padding=3).pack(fill=tk.X)

    def _build_info_panel(self, parent):
        ttk.Label(parent, text="Informações", font=("", 10, "bold")).pack(
            anchor=tk.W, padx=4, pady=(4, 2))

        info_frame = ttk.LabelFrame(parent, text="Design", padding=4)
        info_frame.pack(fill=tk.X, padx=4, pady=2)

        summary = self.design.stitch_summary
        dims = f"{self.design.width_mm:.1f} x {self.design.height_mm:.1f} mm"
        ttk.Label(info_frame, text=f"Dimensões: {dims}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Objetos: {summary['objects']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Cores: {summary['colors']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Pontos: {summary['stitches']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Jumps: {summary['jumps']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Trims: {summary['trims']}").pack(anchor=tk.W)
        est_min = summary['estimated_time_seconds'] / 60.0
        ttk.Label(info_frame, text=f"Tempo est.: {est_min:.1f} min").pack(anchor=tk.W)

        colors_frame = ttk.LabelFrame(parent, text="Cores", padding=4)
        colors_frame.pack(fill=tk.X, padx=4, pady=2)

        colors_canvas = tk.Canvas(colors_frame, height=max(20, summary['colors'] * 22),
                                  highlightthickness=0)
        colors_canvas.pack(fill=tk.X)
        y = 2
        for ci in self.design.color_sequence:
            objs = self.design.get_objects_by_color(ci)
            if objs and objs[0].color:
                c = objs[0].color
                hex_color = c.hex
            else:
                hex_color = "#000000"
            colors_canvas.create_rectangle(4, y, 22, y + 16, fill=hex_color, outline="#000")
            colors_canvas.create_text(28, y + 8, text=f"Cor {ci} ({len(objs)} obj)",
                                      anchor=tk.W, font=("", 9))
            y += 22

        filter_frame = ttk.LabelFrame(parent, text="Filtros", padding=4)
        filter_frame.pack(fill=tk.X, padx=4, pady=2)

        ttk.Checkbutton(filter_frame, text="Costuras",
                        variable=tk.BooleanVar(value=self._show_stitches),
                        command=self._toggle_stitches).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="Jumps",
                        variable=tk.BooleanVar(value=self._show_jumps),
                        command=self._toggle_jumps).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="Underlay",
                        variable=tk.BooleanVar(value=self._show_underlay),
                        command=self._toggle_underlay).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="Contornos",
                        variable=tk.BooleanVar(value=self._show_contours),
                        command=self._toggle_contours).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="Grid mm",
                        variable=tk.BooleanVar(value=self._show_grid),
                        command=self._toggle_grid).pack(anchor=tk.W)

        objects_frame = ttk.LabelFrame(parent, text="Objetos", padding=4)
        objects_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        list_frame = ttk.Frame(objects_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.obj_list = tk.Listbox(list_frame, height=8, yscrollcommand=scrollbar.set,
                                   font=("", 9))
        scrollbar.config(command=self.obj_list.yview)
        self.obj_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, obj in enumerate(self.design.objects):
            stitch_count = obj.total_stitches if obj.generated_stitches else 0
            hex_c = obj.color.hex if obj.color else "#000"
            label = f"[{hex_c}] {obj.name} ({obj.stitch_type.value}) pts:{stitch_count}"
            self.obj_list.insert(tk.END, label)

        legend_frame = ttk.LabelFrame(parent, text="Legenda", padding=4)
        legend_frame.pack(fill=tk.X, padx=4, pady=2)

        legends = [
            (STITCH_COLORS["stitch"], "Costura"),
            (STITCH_COLORS["jump"], "Jump"),
            (STITCH_COLORS["trim"], "Trim"),
            (STITCH_COLORS["underlay"], "Underlay"),
            (STITCH_COLORS["contour"], "Contorno"),
        ]
        for color, label in legends:
            row = ttk.Frame(legend_frame)
            row.pack(fill=tk.X)
            c = tk.Canvas(row, width=16, height=12, highlightthickness=0)
            c.pack(side=tk.LEFT, padx=(0, 4))
            c.create_rectangle(0, 0, 16, 12, fill=color, outline="#000")
            ttk.Label(row, text=label, font=("", 9)).pack(side=tk.LEFT)

    def _toggle_stitches(self):
        self._show_stitches = not self._show_stitches
        self.render()

    def _toggle_jumps(self):
        self._show_jumps = not self._show_jumps
        self.render()

    def _toggle_underlay(self):
        self._show_underlay = not self._show_underlay
        self.render()

    def _toggle_contours(self):
        self._show_contours = not self._show_contours
        self.render()

    def _toggle_grid(self):
        self._show_grid = not self._show_grid
        self.render()

    def _mm_to_canvas(self, x_mm: float, y_mm: float):
        scale = self.zoom * BASE_PX_PER_MM
        cx = self.canvas.winfo_width() / 2 + self.offset_x
        cy = self.canvas.winfo_height() / 2 + self.offset_y
        px = cx + (x_mm - self.design.width_mm / 2) * scale
        py = cy + (y_mm - self.design.height_mm / 2) * scale
        return px, py

    def _center_design(self):
        self.offset_x = 0.0
        self.offset_y = 0.0

    def fit_to_view(self):
        self.root.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        margin = 40
        dw = self.design.width_mm * BASE_PX_PER_MM + margin * 2
        dh = self.design.height_mm * BASE_PX_PER_MM + margin * 2
        self.zoom = min(cw / (self.design.width_mm * BASE_PX_PER_MM + margin),
                        ch / (self.design.height_mm * BASE_PX_PER_MM + margin))
        self.zoom = max(0.1, min(self.zoom, 20.0))
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._update_zoom_label()
        self.render()

    def zoom_in(self):
        self.zoom = min(self.zoom * 1.25, 50.0)
        self._update_zoom_label()
        self.render()

    def zoom_out(self):
        self.zoom = max(self.zoom / 1.25, 0.05)
        self._update_zoom_label()
        self.render()

    def zoom_1to1(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._update_zoom_label()
        self.render()

    def _update_zoom_label(self):
        pct = int(self.zoom * 100)
        self.zoom_label.config(text=f"{pct}%")

    def _on_mouse_wheel(self, event):
        if hasattr(event, 'delta') and event.delta != 0:
            factor = 1.1 if event.delta > 0 else 1 / 1.1
        elif event.num == 4:
            factor = 1.1
        elif event.num == 5:
            factor = 1 / 1.1
        else:
            return

        old_zoom = self.zoom
        self.zoom = max(0.05, min(self.zoom * factor, 50.0))

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        mx = event.x - cw / 2
        my = event.y - ch / 2
        ratio = self.zoom / old_zoom
        self.offset_x = mx - ratio * (mx - self.offset_x)
        self.offset_y = my - ratio * (my - self.offset_y)

        self._update_zoom_label()
        self.render()

    def _on_pan_start(self, event):
        self._drag_start = (event.x, event.y, self.offset_x, self.offset_y)

    def _on_pan_move(self, event):
        if self._drag_start is None:
            return
        sx, sy, sox, soy = self._drag_start
        self.offset_x = sox + (event.x - sx)
        self.offset_y = soy + (event.y - sy)
        self.render()

    def render(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        self._draw_fabric(cw, ch)
        if self._show_grid:
            self._draw_grid(cw, ch)
        self._draw_hoop(cw, ch)
        if self._show_contours:
            self._draw_contours()
        if self._show_underlay:
            self._draw_underlay()
        if self._show_stitches:
            self._draw_stitches()
        if self._show_jumps:
            self._draw_jumps()

    def _draw_fabric(self, cw, ch):
        self.canvas.create_rectangle(0, 0, cw, ch, fill=STITCH_COLORS["fabric"],
                                     outline="", tags="fabric")

    def _draw_grid(self, cw, ch):
        scale = self.zoom * BASE_PX_PER_MM
        mm_step = 1
        if scale < 1:
            mm_step = 10
        elif scale < 3:
            mm_step = 5
        elif scale < 8:
            mm_step = 2

        cx = cw / 2 + self.offset_x
        cy = ch / 2 + self.offset_y

        half_w = self.design.width_mm / 2
        half_h = self.design.height_mm / 2

        start_x_mm = -int(half_w + 20)
        end_x_mm = int(half_w + 20)
        start_y_mm = -int(half_h + 20)
        end_y_mm = int(half_h + 20)

        for mm in range(start_x_mm, end_x_mm + 1, mm_step):
            if mm == 0:
                continue
            px = cx + mm * scale
            if 0 <= px <= cw:
                self.canvas.create_line(px, 0, px, ch, fill=STITCH_COLORS["grid"],
                                        width=1, tags="grid")

        for mm in range(start_y_mm, end_y_mm + 1, mm_step):
            if mm == 0:
                continue
            py = cy + mm * scale
            if 0 <= py <= ch:
                self.canvas.create_line(0, py, cw, py, fill=STITCH_COLORS["grid"],
                                        width=1, tags="grid")

        for axis, coord_mm, is_x in [(0, 0, True), (1, 0, False)]:
            if is_x:
                py = cy
                if 0 <= py <= ch:
                    self.canvas.create_line(0, py, cw, py, fill="#B0B0B0",
                                            width=1, tags="grid")
            else:
                px = cx
                if 0 <= px <= cw:
                    self.canvas.create_line(px, 0, px, ch, fill="#B0B0B0",
                                            width=1, tags="grid")

    def _draw_hoop(self, cw, ch):
        hw = self.design.machine.hoop_width_mm / 2
        hh = self.design.machine.hoop_height_mm / 2
        x1, y1 = self._mm_to_canvas(-hw, -hh)
        x2, y2 = self._mm_to_canvas(hw, hh)
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=STITCH_COLORS["hoop"],
                                     width=2, dash=(6, 4), tags="hoop")

    def _draw_contours(self):
        for obj in self.design.objects:
            if not obj.visible or not obj.contour or len(obj.contour) < 3:
                continue
            coords = []
            for p in obj.contour:
                px, py = self._mm_to_canvas(p[0], p[1])
                coords.extend([px, py])
            if len(coords) >= 6:
                self.canvas.create_polygon(coords, outline=STITCH_COLORS["contour"],
                                           fill="", width=1, dash=(3, 3),
                                           tags="contour")

    def _draw_underlay(self):
        for obj in self.design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue
            points = obj.generated_stitches.points
            underlay_cmds = set()
            in_underlay = False
            for i, pt in enumerate(points):
                if pt.command == StitchCommand.STITCH:
                    if i == 0:
                        prev = pt
                        continue
                    prev_st = None
                    for j in range(i - 1, -1, -1):
                        if points[j].command == StitchCommand.STITCH:
                            prev_st = points[j]
                            break
                    if prev_st:
                        dist = math.sqrt((pt.x - prev_st.x) ** 2 +
                                         (pt.y - prev_st.y) ** 2)
                        if dist > 10.0:
                            in_underlay = True
                    prev = pt

            self._draw_path_segment(points, 0, len(points),
                                    STITCH_COLORS["underlay"], 0.5, "underlay")

    def _draw_stitches(self):
        for obj in self.design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue
            points = obj.generated_stitches.points
            if not points:
                continue

            color = obj.color.hex if obj.color else STITCH_COLORS["stitch"]

            seg_start = 0
            for i in range(1, len(points)):
                if points[i].command == StitchCommand.JUMP:
                    if seg_start < i:
                        self._draw_stitch_segment(points, seg_start, i, color)
                    seg_start = i + 1

            if seg_start < len(points):
                self._draw_stitch_segment(points, seg_start, len(points), color)

    def _draw_stitch_segment(self, points, start, end, color):
        coords = []
        for i in range(start, end):
            pt = points[i]
            if pt.command == StitchCommand.STITCH:
                px, py = self._mm_to_canvas(pt.x, pt.y)
                coords.extend([px, py])
            elif pt.command == StitchCommand.JUMP:
                if len(coords) >= 4:
                    self.canvas.create_line(coords, fill=color, width=1.5,
                                            tags="stitch", capstyle=tk.ROUND,
                                            joinstyle=tk.ROUND)
                coords = []
                px, py = self._mm_to_canvas(pt.x, pt.y)
                coords.extend([px, py])
        if len(coords) >= 4:
            self.canvas.create_line(coords, fill=color, width=1.5,
                                    tags="stitch", capstyle=tk.ROUND,
                                    joinstyle=tk.ROUND)

    def _draw_path_segment(self, points, start, end, color, width, tag):
        coords = []
        for i in range(start, end):
            pt = points[i]
            if pt.command in (StitchCommand.STITCH, StitchCommand.JUMP):
                px, py = self._mm_to_canvas(pt.x, pt.y)
                coords.extend([px, py])
        if len(coords) >= 4:
            self.canvas.create_line(coords, fill=color, width=width,
                                    tags=tag, stipple="gray50")

    def _draw_jumps(self):
        for obj in self.design.objects:
            if not obj.visible or not obj.generated_stitches:
                continue
            points = obj.generated_stitches.points
            prev = None
            for pt in points:
                if pt.command == StitchCommand.JUMP and prev is not None:
                    x1, y1 = self._mm_to_canvas(prev.x, prev.y)
                    x2, y2 = self._mm_to_canvas(pt.x, pt.y)
                    self.canvas.create_line(x1, y1, x2, y2,
                                            fill=STITCH_COLORS["jump"],
                                            width=1, dash=(4, 4), tags="jump")
                if pt.command == StitchCommand.STITCH:
                    prev = pt

    def show(self):
        self.root.after(100, self.fit_to_view)
        self.root.mainloop()


def show_preview(design: EmbroideryDesign):
    """Atalho para abrir o preview."""
    preview = StitchPreview(design)
    preview.show()
