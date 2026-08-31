"""
Jarvis HUD Overlay — PyQt6 widget with Arc Reactor animation.

Frameless, translucent window that renders:
- Dark vignette backdrop
- Outer glow rings
- Arc Reactor (center) with concentric rings
- Partial arcs with rotation
- Wave rings (emit on state changes)
- Voice level bars
- Floating particles with connections
- State label

Animated by QTimer at 60fps. Activity level drives color (cyan idle → amber speaking)
and animation speed.

Reaproveitado de spidertje/jarvis-pyqt (MIT). Adaptações para o EcoSystemUmGrau:
- Sem face recognition, sem profile (MariaDB), sem dependência de Wyoming.
- Import de JarvisState absoluto a partir do módulo gui-desktop.core.state.
"""

import math
import random

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QWidget

from gui_desktop.core.state import JarvisState  # noqa: F401  (resolvido pelo shim em main.py)

PARTICLE_COUNT = 60
BAR_COUNT = 40
RING_RADII = [120, 200, 280]
PARTICLE_SPEED_BASE = 0.6
BAR_SMOOTHING = 0.18
WAVE_LIFETIME = 2.5
WAVE_SPEED = 0.8
CONN_DISTANCE = 100
CONN_DISTANCE_ACTIVE = 140


class HUDOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #000000;")
        self.resize(800, 600)

        self._state = JarvisState.IDLE
        self._activity = 0.0
        self._voice_level = 0.0
        self._voice_level_timer = 0
        self._angle = 0.0
        self._pulse = 0.0

        self._assistant_name = "Eco"

        self._cx = 400
        self._cy = 300

        self._particles = self._init_particles()
        self._bar_heights = [2.0] * BAR_COUNT
        self._wave_rings = []

        self._palette_hue: int | None = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 60)

    def _draw_assistant_name(self, p: QPainter):
        padding = 10
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(0, 0, 0, 180))
        p.drawText(padding + 2, 24 + 2, self._assistant_name)
        p.setPen(QColor(255, 255, 255, 230))
        p.drawText(padding, 24, self._assistant_name)

    def set_palette_hue(self, hue: int):
        self._palette_hue = hue
        self.update()

    def clear_palette_hue(self):
        self._palette_hue = None
        self.update()

    def set_assistant_name(self, name: str):
        self._assistant_name = name
        self.update()

    def set_state(self, state: JarvisState):
        self._state = state
        if state == JarvisState.SPEAKING:
            for i in range(3):
                self._wave_rings.append({"phase": i * 0.6, "speed": WAVE_SPEED})

    def set_voice_level(self, level: float):
        self._voice_level = max(0.0, min(1.0, level))
        self._voice_level_timer = 30
        self.update()

    @property
    def state(self) -> JarvisState:
        return self._state

    @property
    def activity(self) -> float:
        return self._activity

    def _tick(self):
        target = self._state.target_activity
        lerp = 0.15 if self._activity < target else 0.08
        self._activity += (target - self._activity) * lerp

        if self._voice_level_timer > 0:
            self._voice_level_timer -= 1
        else:
            self._voice_level *= 0.93

        speed = 1.0 + self._activity * 3.0
        self._angle += 0.02 * speed
        self._pulse = (self._pulse + 0.06) % (math.pi * 2)

        self._update_particles(speed)
        self._update_bars(speed)

        self._wave_rings = [w for w in self._wave_rings if w["phase"] < WAVE_LIFETIME]
        for w in self._wave_rings:
            w["phase"] += w["speed"] * 0.04

        self.update()

    def _update_particles(self, speed):
        for p in self._particles:
            p["x"] += p["sx"] * speed
            p["y"] += p["sy"] * speed
            if p["x"] < 0:
                p["x"] = 800
            elif p["x"] > 800:
                p["x"] = 0
            if p["y"] < 0:
                p["y"] = 600
            elif p["y"] > 600:
                p["y"] = 0

    def _update_bars(self, speed):
        for i in range(BAR_COUNT):
            target = 2.0
            if self._state == JarvisState.LISTENING:
                lvl = self._voice_level ** 0.6
                target = 6.0 + random.random() * 24.0 * lvl
            elif self._state == JarvisState.SPEAKING:
                target = 10.0 + random.random() * 20.0 * self._activity
            self._bar_heights[i] += (target - self._bar_heights[i]) * BAR_SMOOTHING

    @staticmethod
    def _init_particles():
        particles = []
        for _ in range(PARTICLE_COUNT):
            particles.append({
                "x": random.uniform(0, 800),
                "y": random.uniform(0, 600),
                "size": random.uniform(1, 3),
                "sx": random.uniform(-PARTICLE_SPEED_BASE, PARTICLE_SPEED_BASE),
                "sy": random.uniform(-PARTICLE_SPEED_BASE, PARTICLE_SPEED_BASE),
                "op": random.uniform(0.3, 0.8),
            })
        return particles

    @staticmethod
    def _color(h: int, s: int, light: int, a: int) -> QColor:
        c = QColor()
        c.setHsl(h, s, light)
        c.setAlpha(max(0, min(255, int(a))))
        return c

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self._cx, self._cy
        act = self._activity

        if self._palette_hue is not None:
            hue = self._palette_hue
            sat = 170
        elif act < 0.4:
            hue = 182
        elif act > 0.7:
            hue = 45
        else:
            hue = 120
        sat = min(255, max(0, int(170 + int((1 - act) * 30))))

        self._draw_assistant_name(p)
        self._draw_vignette(p, cx, cy, act, hue, sat)
        self._draw_glow_rings(p, cx, cy, act, hue, sat)
        self._draw_reactor(p, cx, cy, act, hue, sat)
        self._draw_arcs(p, cx, cy, act, hue, sat)
        self._draw_wave_rings(p, cx, cy, act, hue, sat)
        self._draw_voice_bars(p, cx, cy, act, hue, sat)
        self._draw_particles(p, act, hue, sat)
        self._draw_connections(p, act, hue, sat)
        self._draw_state_label(p, cx, cy, act, hue, sat)

        p.end()

    def _draw_vignette(self, p, cx, cy, act, hue, sat):
        vg = QRadialGradient(cx, cy, 400)
        vg.setColorAt(0, self._color(0, 0, 0, int(60 + act * 80)))
        vg.setColorAt(0.6, self._color(0, 0, 0, int(30 + act * 50)))
        vg.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), vg)

    def _draw_glow_rings(self, p, cx, cy, act, hue, sat):
        pen = QPen(self._color(hue, sat, 70, int(100 + act * 100)), 2 + act * 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        for r in RING_RADII:
            s = 0.92 + 0.08 * math.sin(self._pulse + r * 0.01)
            p.drawEllipse(QPointF(cx, cy), int(r * s), int(r * s))

    def _draw_reactor(self, p, cx, cy, act, hue, sat):
        cg = QRadialGradient(cx, cy, 35)
        cg.setColorAt(0, self._color(hue, sat, 90, int(200 + 55 * act)))
        cg.setColorAt(0.5, self._color(hue, sat, 70, int(100 + 80 * act)))
        cg.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(cg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 35, 35)

        for r in [22, 14, 6]:
            a = 180 + int(75 * act)
            lw = 2.5 if r == 22 else (2.0 if r == 14 else 1.5)
            pen = QPen(self._color(hue, sat, 90, a), lw)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)

        if self._state == JarvisState.SPEAKING:
            fa = int(100 + 155 * (0.5 + 0.5 * math.sin(self._pulse * 4)))
            fp = QPen(self._color(hue, sat, 98, fa), 3)
            p.setPen(fp)
            s = 1 + 0.08 * math.sin(self._pulse * 3)
            p.drawEllipse(QPointF(cx, cy), int(28 * s), int(28 * s))

    def _draw_arcs(self, p, cx, cy, act, hue, sat):
        span = math.pi * 1.5
        for i, radius in enumerate(RING_RADII):
            a = self._angle + i * 0.5
            lw = 3.0 + act * 4.0 + i * 1.0
            pen = QPen(self._color(hue, sat, 65 + i * 8, int(140 + act * 115)), lw)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            r = radius
            start_deg = int(math.degrees(a) * 16)
            span_deg = int(math.degrees(span) * 16)
            p.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2), start_deg, span_deg)

            if act > 0.2:
                fill = self._color(hue, sat, 65, int(35 + act * 50))
                p.setBrush(fill)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPie(int(cx - r), int(cy - r), int(r * 2), int(r * 2), start_deg, span_deg)

    def _draw_wave_rings(self, p, cx, cy, act, hue, sat):
        for w in self._wave_rings:
            scale = 0.5 + w["phase"] * 1.2
            wr = 70 * scale
            wa = int(150 - w["phase"] * 90)
            pen = QPen(self._color(hue, sat, 70, max(0, wa)), 2.5 - w["phase"] * 0.6)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), int(wr), int(wr))

    def _draw_voice_bars(self, p, cx, cy, act, hue, sat):
        bar_w, gap = 5, 3
        total_w = BAR_COUNT * (bar_w + gap)
        start_x = cx - total_w / 2
        base_y = cy + 70

        for i, h in enumerate(self._bar_heights):
            if h < 1:
                continue
            x = start_x + i * (bar_w + gap)
            ba = int(150 + 105 * act)
            bcol = self._color(hue, sat, 70 + int(h / 60 * 30), ba)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bcol)
            p.drawRoundedRect(int(x), int(base_y - h), bar_w, int(h), 2, 2)

    def _draw_particles(self, p, act, hue, sat):
        for pt in self._particles:
            pa = int(pt["op"] * 255 * (0.5 + act * 0.5))
            sz = pt["size"] * (1 + act * 0.5)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._color(hue, sat, 85, pa))
            p.drawEllipse(QPointF(pt["x"], pt["y"]), int(sz), int(sz))

    def _draw_connections(self, p, act, hue, sat):
        conn_a = int(15 + act * 30)
        dist = CONN_DISTANCE + act * (CONN_DISTANCE_ACTIVE - CONN_DISTANCE)
        pen = QPen(self._color(hue, sat, 50, conn_a), 0.8)
        p.setPen(pen)

        for i, a_p in enumerate(self._particles):
            for b_p in self._particles[i + 1:]:
                dx = a_p["x"] - b_p["x"]
                dy = a_p["y"] - b_p["y"]
                d = math.sqrt(dx * dx + dy * dy)
                if d < dist:
                    p.drawLine(QPointF(a_p["x"], a_p["y"]), QPointF(b_p["x"], b_p["y"]))

    def _draw_state_label(self, p, cx, cy, act, hue, sat):
        labels = ["STANDBY", "LISTENING", "THINKING", "SPEAKING"]
        pen = QPen(self._color(hue, sat, 80, 220), 1)
        p.setPen(pen)
        fnt = p.font()
        fnt.setPointSize(11)
        fnt.setBold(True)
        p.setFont(fnt)
        p.drawText(int(cx - 50), int(cy + 110), labels[self._state])
