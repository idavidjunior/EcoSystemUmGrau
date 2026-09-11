"""
FASE 2 - Primitivas de Costura (Stitch Primitives)

Comandos que a máquina de bordado entende.
Cada ponto possui coordenada X, Y e um comando.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Tuple
import struct


class StitchCommand(IntEnum):
    """Comandos de máquina de bordado."""
    STITCH = 0        # Ponto normal
    JUMP = 1          # Salto (máquina se move sem costurar)
    TRIM = 2          # Corte de linha
    COLOR_CHANGE = 3  # Mudança de cor
    SEQUIN = 4        # Pailleté
    START = 5         # Início do design
    END = 6           # Fim do design
    NEEDLE_UP = 7     # Agulha para cima
    NEEDLE_DOWN = 8   # Agulha para baixo
    TIE_IN = 9        # Nó de início (prender linha)
    TIE_OFF = 10      # Nó de fim (prender linha)


@dataclass
class StitchPoint:
    """Um ponto individual de bordado."""
    x: float              # Coordenada X em mm (ou 0.1mm para formatos inteiros)
    y: float              # Coordenada Y em mm
    command: StitchCommand = StitchCommand.STITCH
    color_index: int = 0  # Índice da cor (para COLOR_CHANGE)

    def to_int(self, scale: float = 10.0) -> Tuple[int, int]:
        """Converte para inteiro (formato de arquivo)."""
        return (int(round(self.x * scale)), int(round(self.y * scale)))

    def distance_to(self, other: 'StitchPoint') -> float:
        """Distância euclidiana para outro ponto."""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5


@dataclass
class StitchPath:
    """Sequência ordenada de pontos de costura."""
    points: List[StitchPoint] = field(default_factory=list)

    def add_stitch(self, x: float, y: float, command: StitchCommand = StitchCommand.STITCH):
        """Adiciona um ponto."""
        self.points.append(StitchPoint(x, y, command))

    def add_stitch_absolute(self, x: float, y: float, command: StitchCommand = StitchCommand.STITCH):
        """Adiciona ponto com coordenadas absolutas."""
        self.points.append(StitchPoint(x, y, command))

    @property
    def total_stitches(self) -> int:
        return sum(1 for p in self.points if p.command == StitchCommand.STITCH)

    @property
    def total_jumps(self) -> int:
        return sum(1 for p in self.points if p.command == StitchCommand.JUMP)

    @property
    def total_trims(self) -> int:
        return sum(1 for p in self.points if p.command == StitchCommand.TRIM)

    @property
    def color_changes(self) -> int:
        return sum(1 for p in self.points if p.command == StitchCommand.COLOR_CHANGE)

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Retorna (min_x, min_y, max_x, max_y)."""
        stitch_points = [p for p in self.points if p.command == StitchCommand.STITCH]
        if not stitch_points:
            return (0, 0, 0, 0)
        xs = [p.x for p in stitch_points]
        ys = [p.y for p in stitch_points]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def total_distance(self) -> float:
        """Distância total percorrida."""
        total = 0.0
        for i in range(1, len(self.points)):
            total += self.points[i-1].distance_to(self.points[i])
        return total

    def trim_stitch_distance(self) -> float:
        """Distância total de costura (sem jumps/trims)."""
        total = 0.0
        for i in range(1, len(self.points)):
            if self.points[i].command == StitchCommand.STITCH:
                total += self.points[i-1].distance_to(self.points[i])
        return total

    def reverse(self):
        """Inverte a ordem dos pontos."""
        self.points.reverse()

    def append_path(self, other: 'StitchPath'):
        """Adiciona outra sequência ao final."""
        self.points.extend(other.points)

    def clear(self):
        """Limpa todos os pontos."""
        self.points.clear()

    def __len__(self):
        return len(self.points)

    def __getitem__(self, idx):
        return self.points[idx]

    def __iter__(self):
        return iter(self.points)
