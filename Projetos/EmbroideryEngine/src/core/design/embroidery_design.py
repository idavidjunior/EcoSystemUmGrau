"""
FASE 1 - Modelo Interno de Bordado (Embroidery Design)

O modelo interno NÃO é PES. É uma representação semântica completa
do design de bordado que permite editar, recalcular e exportar
para qualquer formato de máquina.

Referência: Prompt de implementação - Seção 4
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import uuid
import math


# ============================================================
# Enums do Modelo
# ============================================================

class StitchType(Enum):
    """Tipos de costura suportados."""
    RUN = "run"
    TRIPLE_RUN = "triple_run"
    SATIN = "satin"
    TATAMI = "tatami"
    FILL = "fill"
    COLUMN = "column"
    OUTLINE = "outline"
    CENTER_RUN = "center_run"
    EDGE_RUN = "edge_run"
    MANUAL_STITCH = "manual_stitch"
    CONTOUR = "contour"
    SPIRAL = "spiral"
    CROSS_STITCH = "cross_stitch"
    MOTIF = "motif"
    PROGRAM_SPLIT = "program_split"


class FabricType(Enum):
    """Tipos de tecido."""
    COTTON = "cotton"
    KNIT = "knit"
    DENIM = "denim"
    FLEECE = "fleece"
    POLYESTER = "polyester"
    SILK = "silk"
    LEATHER = "leather"
    CAP = "cap"
    WOOL = "wool"
    LINEN = "linen"
    CUSTOM = "custom"


class UnderlayType(Enum):
    """Tipos de underlay (base)."""
    NONE = "none"
    EDGE_RUN = "edge_run"
    CENTER_RUN = "center_run"
    ZIGZAG = "zigzag"
    DOUBLE_ZIGZAG = "double_zigzag"
    FILL = "fill"
    CONTOUR = "contour"


class ObjectRole(Enum):
    """Papel do objeto no design."""
    BACKGROUND = "background"
    MAIN_SHAPE = "main_shape"
    SECONDARY_SHAPE = "secondary_shape"
    DETAIL = "detail"
    OUTLINE = "outline"
    TEXT = "text"
    HOLE = "hole"
    BORDER = "border"


# ============================================================
# Dados de Cor e Fio
# ============================================================

@dataclass
class ThreadColor:
    """Cor de fio (bobbin/linha)."""
    name: str
    brand: str = "Generic"
    code: str = ""
    r: int = 0
    g: int = 0
    b: int = 0

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def distance_to(self, other: 'ThreadColor') -> float:
        """Distância euclidiana no espaço RGB."""
        return math.sqrt(
            (self.r - other.r) ** 2 +
            (self.g - other.g) ** 2 +
            (self.b - other.b) ** 2
        )


@dataclass
class ThreadPalette:
    """Paleta de fios disponível."""
    name: str = "Default"
    threads: List[ThreadColor] = field(default_factory=list)

    def find_closest(self, r: int, g: int, b: int) -> ThreadColor:
        """Encontra a cor mais próxima na paleta."""
        if not self.threads:
            return ThreadColor("Black", r=r, g=g, b=b)

        target = ThreadColor("target", r=r, g=g, b=b)
        closest = min(self.threads, key=lambda t: t.distance_to(target))
        return closest


# ============================================================
# Perfis de Máquina
# ============================================================

@dataclass
class MachineProfile:
    """Perfil da máquina de bordado."""
    name: str
    hoop_width_mm: float = 200.0
    hoop_height_mm: float = 200.0
    max_stitch_length_mm: float = 12.7
    max_jump_length_mm: float = 12.7
    supports_trim: bool = True
    supports_color_change: bool = True
    needle_count: int = 15
    coordinate_limit: int = 127  # ±127mm para DST
    uses_01_units: bool = False  # True para PES (0.1mm)

    @property
    def coordinate_scale(self) -> float:
        """Escala de coordenadas (unidades por mm)."""
        return 10.0 if self.uses_01_units else 1.0


# ============================================================
# Objeto de Bordado
# ============================================================

@dataclass
class EmbroideryObject:
    """
    Objeto individual de bordado.

    Cada região da imagem segmentada vira um EmbroideryObject
    com sua geometria, parâmetros e pontos gerados.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    role: ObjectRole = ObjectRole.MAIN_SHAPE

    # Geometria
    contour: List[Tuple[float, float]] = field(default_factory=list)
    holes: List[List[Tuple[float, float]]] = field(default_factory=list)
    bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)

    # Propriedades visuais
    color: ThreadColor = field(default_factory=lambda: ThreadColor("Black", r=0, g=0, b=0))
    color_index: int = 0

    # Tipo de costura
    stitch_type: StitchType = StitchType.FILL
    direction_angle: float = 0.0  # graus

    # Parâmetros de costura
    density: float = 0.4         # espaçamento em mm
    stitch_length: float = 4.0   # comprimento máximo do ponto em mm
    pull_compensation: float = 0.0  # compensação pull em mm
    push_compensation: float = 0.0  # compensação push em mm

    # Underlay
    underlay_type: UnderlayType = UnderlayType.ZIGZAG
    underlay_density: float = 0.6  # menos denso que o preenchimento

    # Limites
    min_stitch_length: float = 0.5  # mm
    max_stitch_length: float = 12.0  # mm

    # Pontos gerados (saída do stitch engine)
    generated_stitches: Optional['StitchPath'] = None

    # Hierarquia
    layer: int = 0
    priority: int = 0
    parent_object_id: Optional[str] = None

    # Metadados
    visible: bool = True
    locked: bool = False

    @property
    def width(self) -> float:
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self) -> float:
        return self.bounds[3] - self.bounds[1]

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return float('inf')
        return self.width / self.height

    @property
    def center(self) -> Tuple[float, float]:
        cx = (self.bounds[0] + self.bounds[2]) / 2
        cy = (self.bounds[1] + self.bounds[3]) / 2
        return (cx, cy)

    @property
    def perimeter(self) -> float:
        """Perímetro do contorno."""
        if len(self.contour) < 2:
            return 0
        total = 0
        for i in range(len(self.contour)):
            x1, y1 = self.contour[i]
            x2, y2 = self.contour[(i + 1) % len(self.contour)]
            total += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return total

    @property
    def is_narrow(self) -> bool:
        """Objeto estreito (candidato a satin)."""
        return self.width < 12.0  # mm

    @property
    def is_large_area(self) -> bool:
        """Área grande (candidato a tatami)."""
        return self.area > 200.0  # mm²

    @property
    def total_stitches(self) -> int:
        if self.generated_stitches:
            return self.generated_stitches.total_stitches
        return 0


# ============================================================
# Design de Bordado Completo
# ============================================================

@dataclass
class EmbroideryDesign:
    """
    Representação completa de um design de bordado.
    Modelo interno do motor de digitalização.
    """
    name: str = "Untitled"
    objects: List[EmbroideryObject] = field(default_factory=list)
    palette: ThreadPalette = field(default_factory=ThreadPalette)
    machine: MachineProfile = field(default_factory=lambda: MachineProfile("Generic"))

    # Dimensões do canvas
    width_mm: float = 200.0
    height_mm: float = 200.0

    # Metadados
    author: str = ""
    description: str = ""
    fabric: FabricType = FabricType.COTTON

    @property
    def total_objects(self) -> int:
        return len([o for o in self.objects if o.visible])

    @property
    def total_stitches(self) -> int:
        return sum(o.total_stitches for o in self.objects)

    @property
    def total_colors(self) -> int:
        return len(set(o.color_index for o in self.objects if o.visible))

    @property
    def color_sequence(self) -> List[int]:
        """Sequência de cores na ordem de costura."""
        seen = []
        for obj in self.objects:
            if obj.visible and obj.color_index not in seen:
                seen.append(obj.color_index)
        return seen

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Bounding box de todos os objetos."""
        if not self.objects:
            return (0, 0, self.width_mm, self.height_mm)

        min_x = min(o.bounds[0] for o in self.objects)
        min_y = min(o.bounds[1] for o in self.objects)
        max_x = max(o.bounds[2] for o in self.objects)
        max_y = max(o.bounds[3] for o in self.objects)
        return (min_x, min_y, max_x, max_y)

    @property
    def stitch_summary(self) -> Dict:
        """Resumo de pontos do design."""
        total_stitches = 0
        total_jumps = 0
        total_trims = 0
        total_color_changes = 0

        for obj in self.objects:
            if obj.generated_stitches:
                total_stitches += obj.generated_stitches.total_stitches
                total_jumps += obj.generated_stitches.total_jumps
                total_trims += obj.generated_stitches.total_trims
                total_color_changes += obj.generated_stitches.color_changes

        return {
            "objects": self.total_objects,
            "colors": self.total_colors,
            "stitches": total_stitches,
            "jumps": total_jumps,
            "trims": total_trims,
            "color_changes": total_color_changes,
            "estimated_time_seconds": total_stitches * 0.05
        }

    def get_object_by_id(self, obj_id: str) -> Optional[EmbroideryObject]:
        for obj in self.objects:
            if obj.id == obj_id:
                return obj
        return None

    def get_objects_by_color(self, color_index: int) -> List[EmbroideryObject]:
        return [o for o in self.objects if o.color_index == color_index]

    def remove_object(self, obj_id: str):
        self.objects = [o for o in self.objects if o.id != obj_id]

    def add_object(self, obj: EmbroideryObject):
        self.objects.append(obj)

    def recalculate_metadata(self):
        """Recalcula bounding box a partir dos objetos visíveis."""
        if not self.objects:
            return
        visible = [o for o in self.objects if o.visible and o.bounds != (0, 0, 0, 0)]
        if not visible:
            return
        min_x = min(o.bounds[0] for o in visible)
        min_y = min(o.bounds[1] for o in visible)
        max_x = max(o.bounds[2] for o in visible)
        max_y = max(o.bounds[3] for o in visible)
        self.width_mm = max(max_x - min_x, 1.0)
        self.height_mm = max(max_y - min_y, 1.0)
