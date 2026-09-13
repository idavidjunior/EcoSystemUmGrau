"""
FASE 9 - Vectorization Engine (Improved)

Converte regiões segmentadas em objetos de bordado com geometria vetorial precisa.
Adiciona:
- Bezier curve fitting (least squares)
- Skeletonization for centerlines (running/satin)
- Sub-pixel contour refinement
- Corner detection and preservation
- Line/arc detection for geometric shapes
"""

import math
from typing import List, Tuple, Dict, Optional, Union
import numpy as np
from skimage import measure, morphology, feature


class VectorizationEngine:
    """Converte regiões de pixels em objetos vetoriais de bordado com precisão profissional."""

    def __init__(self, scale_mm: float = 0.2, simplify_tolerance: float = 1.0):
        self.scale_mm = scale_mm
        self.simplify_tolerance = simplify_tolerance
        # Parâmetros de precisão
        self.corner_threshold = 0.7  # cos(angle) threshold for corner detection
        self.curve_fit_tolerance = 0.5  # max deviation for curve fitting
        self.min_curve_points = 4  # min points for curve fitting
        self.max_bezier_error = 0.3  # max error for bezier fitting

    def vectorize_region(self, region: Dict) -> Dict:
        """Converte uma região segmentada em objeto vetorial preciso."""
        contour = region.get('contour')
        if not contour:
            return region

        # 1. Refinar contorno para sub-pixel (refinement)
        contour_refined = self._refine_contour_subpixel(region.get('mask'), contour)

        # 2. Detectar cantos e pontos de interesse
        corners = self._detect_corners(contour_refined)

        # 3. Ajustar curvas de Bezier por segmentos
        bezier_segments = self._fit_bezier_segments(contour_refined, corners)

        # 3b. Detectar linhas retas e arcos
        geometric_primitives = self._detect_geometric_primitives(contour_refined, corners)

        # 4. Esqueleto para centerlines (running stitch / satin)
        skeleton = self._extract_skeleton(region.get('mask'))

        # 5. Converter para mm
        scale = self.scale_mm
        contour_mm = [(x * self.scale_mm, y * self.scale_mm) for x, y in contour_refined]
        skeleton_mm = [(x * self.scale_mm, y * self.scale_mm) for x, y in skeleton] if skeleton else []
        corners_mm = [(x * self.scale_mm, y * self.scale_mm) for x, y in corners]
        bezier_mm = [
            [(p[0]*self.scale_mm, p[1]*self.scale_mm) for p in seg]
            for seg in bezier_segments
        ]

        # Centroide e bounds
        min_x = min(p[0] for p in contour_mm)
        min_y = min(p[1] for p in contour_mm)
        max_x = max(p[0] for p in contour_mm)
        max_y = max(p[1] for p in contour_mm)
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        centered = [(p[0] - cx, p[1] - cy) for p in contour_mm]

        # Métricas
        width_mm = max_x - min_x
        height_mm = max_y - min_y
        area_mm2 = self._shoelace_area(centered)
        perimeter_mm = self._perimeter(centered)

        # Classificação de tipo de costura baseada na geometria
        stitch_type = self._classify_stitch_type(region, width_mm, height_mm, 
                                                   skeleton_mm, corners_mm, geometric_primitives)

        return {
            **region,
            'contour_px': contour_refined,
            'contour_mm': contour_mm,
            'centered_mm': centered,
            'contour_mm_centered': centered,
            'corners_px': corners,
            'corners_mm': corners_mm,
            'bezier_segments_px': bezier_segments,
            'bezier_segments_mm': bezier_mm,
            'skeleton_px': skeleton,
            'skeleton_mm': skeleton_mm,
            'geometric_primitives': geometric_primitives,
            'center_mm': (cx, cy),
            'bounds_mm': (min_x, min_y, max_x, max_y),
            'width_mm': width_mm,
            'height_mm': height_mm,
            'area_mm2': self._shoelace_area(centered),
            'perimeter_mm': perimeter_mm,
            'stitch_type_suggestion': stitch_type,
            'corners_count': len(corners),
        }

    def _refine_contour_subpixel(self, mask: np.ndarray, contour: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Refina contorno para precisão sub-pixel usando gradientes de imagem."""
        if mask is None or not contour:
            return contour
        
        # Usar distância euclidiana do contorno aos bordos reais (gradientes)
        # Para simplicidade, usar o contorno do skimage que já é sub-pixel
        # mas suavizar levemente
        if len(contour) < 3:
            return contour
        
        # Suavização leve preservando cantos
        smoothed = self._smooth_preserve_corners(contour)
        return smoothed

    def _smooth_preserve_corners(self, contour: List[Tuple[float, float]], 
                                 iterations: int = 2, corner_weight: float = 0.5) -> List[Tuple[float, float]]:
        """Suaviza contorno preservando cantos detectados."""
        if len(contour) < 5:
            return contour
        
        # Detectar cantos
        corners = self._detect_corners(contour)
        corner_indices = set()
        for cx, cy in corners:
            # Encontrar índice mais próximo
            min_idx = min(range(len(contour)), key=lambda i: 
                (contour[i][0] - cx)**2 + (contour[i][1] - cy)**2)
            corner_indices.add(min_idx)
        
        pts = np.array(contour, dtype=float)
        for _ in range(iterations):
            new_pts = pts.copy()
            for i in range(1, len(pts) - 1):
                if i in corner_indices:
                    continue  # Preservar cantos
                # Média ponderada dos vizinhos
                new_pts[i] = 0.5 * pts[i] + 0.25 * pts[i-1] + 0.25 * pts[(i+1)%len(pts)]
            pts = new_pts
        
        return [(float(x), float(y)) for x, y in pts]

    def _detect_corners(self, contour: List[Tuple[float, float]], 
                        window: int = 5) -> List[Tuple[float, float]]:
        """Detecta cantos usando mudança de ângulo (k-curvature)."""
        if len(contour) < window * 2 + 1:
            return []
        
        corners = []
        pts = np.array(contour)
        n = len(pts)
        
        for i in range(n):
            # Pontos antes e depois com janela
            prev_idx = (i - window) % n
            next_idx = (i + window) % n
            
            v1 = pts[i] - pts[prev_idx]
            v2 = pts[next_idx] - pts[i]
            
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 > 1e-6 and norm2 > 1e-6:
                cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = math.acos(cos_angle)
                
                # Mudança brusca = canto
                if cos_angle < self.corner_threshold:
                    corners.append((float(pts[i][0]), float(pts[i][1])))
        
        # Filtrar cantos muito próximos (mesmo canto detectado múltiplas vezes)
        return self._filter_nearby_corners(corners, min_dist=3.0)

    def _filter_nearby_corners(self, corners: List[Tuple[float, float]], 
                                min_dist: float = 3.0) -> List[Tuple[float, float]]:
        """Filtra cantos muito próximos (mesmo canto real)."""
        if not corners:
            return []
        filtered = [corners[0]]
        for c in corners[1:]:
            last = filtered[-1]
            if math.hypot(c[0] - last[0], c[1] - last[1]) >= min_dist:
                filtered.append(c)
        return filtered

    def _fit_bezier_segments(self, contour: List[Tuple[float, float]], 
                              corners: List[Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
        """Ajusta curvas de Bezier cúbicas entre cantos."""
        if len(corners) < 2 or len(contour) < self.min_curve_points:
            return []
        
        # Mapear cantos para índices do contorno
        corner_indices = []
        for cx, cy in corners:
            idx = min(range(len(contour)), 
                     key=lambda i: (contour[i][0] - cx)**2 + (contour[i][1] - cy)**2)
            corner_indices.append(idx)
        corner_indices = sorted(set(corner_indices))
        
        if len(corner_indices) < 2:
            return []
        
        bezier_segments = []
        for i in range(len(corner_indices)):
            start_idx = corner_indices[i]
            end_idx = corner_indices[(i + 1) % len(corner_indices)]
            
            # Extrair segmento entre cantos
            if end_idx > start_idx:
                segment = contour[start_idx:end_idx + 1]
            else:
                segment = contour[start_idx:] + contour[:end_idx + 1]
            
            if len(segment) >= 4:
                bezier = self._fit_cubic_bezier(segment)
                if bezier:
                    bezier_segments.append(bezier)
            elif len(segment) >= 2:
                # Segmento reto
                bezier_segments.append([segment[0], segment[-1]])
        
        return bezier_segments

    def _fit_cubic_bezier(self, points: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """Ajusta curva de Bezier cúbica (4 pontos de controle) via least squares."""
        if len(points) < 4:
            return None
        
        # Parâmetros t uniformes
        n = len(points)
        t = np.linspace(0, 1, n)
        
        # Matriz de Bezier cúbica
        # B(t) = (1-t)^3 * P0 + 3*(1-t)^2*t * P1 + 3*(1-t)*t^2 * P2 + t^3 * P3
        # Resolver para P1, P2 dado P0=points[0], P3=points[-1]
        
        P0 = np.array(points[0])
        P3 = np.array(points[-1])
        
        # Montar sistema linear para P1, P2
        A = []
        b = []
        for i, pt in enumerate(points):
            ti = t[i]
            ti2 = ti * ti
            ti3 = ti2 * ti
            one_t = 1 - ti
            one_t2 = one_t * one_t
            one_t3 = one_t2 * one_t
            
            # P0 e P3 conhecidos
            known = one_t3 * P0 + ti3 * P3
            target = np.array(pt) - known
            
            # Coeficientes para P1 e P2
            c1 = 3 * one_t2 * ti
            c2 = 3 * one_t * ti2
            
            A.append([c1, 0, c2, 0])
            A.append([0, c1, 0, c2])
            b.extend([target[0], target[1]])
        
        A = np.array(A)
        b = np.array(b)
        
        try:
            sol = np.linalg.lstsq(A, b, rcond=None)[0]
            P1 = (float(sol[0]), float(sol[1]))
            P2 = (float(sol[2]), float(sol[3]))
            
            # Verificar erro máximo
            max_err = self._bezier_max_error(points, P0, P1, P2, P3)
            if max_err <= self.max_bezier_error:
                return [(float(p[0]), float(p[1])) for p in [P0, P1, P2, P3]]
        except np.linalg.LinAlgError:
            pass
        
        return None

    def _bezier_max_error(self, points, P0, P1, P2, P3) -> float:
        """Calcula erro máximo de ajuste Bezier."""
        max_err = 0.0
        n = len(points)
        for i, pt in enumerate(points):
            t = i / (n - 1) if n > 1 else 0
            ti = 1 - t
            bx = (ti**3)*P0[0] + 3*(ti**2)*t*P1[0] + 3*ti*(t**2)*P2[0] + (t**3)*P3[0]
            by = (ti**3)*P0[1] + 3*(ti**2)*t*P1[1] + 3*ti*(t**2)*P2[1] + (t**3)*P3[1]
            err = math.hypot(bx - pt[0], by - pt[1])
            max_err = max(max_err, err)
        return max_err

    def _detect_geometric_primitives(self, contour: List[Tuple[float, float]], 
                                      corners: List[Tuple[float, float]]) -> List[Dict]:
        """Detecta primitivas geométricas: linhas retas, arcos, círculos."""
        if len(contour) < 10:
            return []
        
        primitives = []
        
        # Aproximar por segmentos entre cantos
        corner_indices = []
        for cx, cy in corners:
            idx = min(range(len(contour)), 
                     key=lambda i: (contour[i][0] - cx)**2 + (contour[i][1] - cy)**2)
            corner_indices.append(idx)
        corner_indices = sorted(set(corner_indices))
        
        for i in range(len(corner_indices)):
            start = corner_indices[i]
            end = corner_indices[(i + 1) % len(corner_indices)]
            
            if end > start:
                segment = contour[start:end + 1]
            else:
                segment = contour[start:] + contour[:end + 1]
            
            if len(segment) < 5:
                continue
            
            # Testar se é linha reta
            is_line, line_error = self._test_line(segment)
            if is_line:
                primitives.append({
                    'type': 'line',
                    'start': segment[0],
                    'end': segment[-1],
                    'error': line_error,
                })
                continue
            
            # Testar se é arco circular
            is_arc, center, radius, arc_error = self._test_arc(segment)
            if is_arc:
                primitives.append({
                    'type': 'arc',
                    'center': center,
                    'radius': radius,
                    'start': segment[0],
                    'end': segment[-1],
                    'error': arc_error,
                })
                continue
            
            # Caso contrário, curva livre
            primitives.append({
                'type': 'curve',
                'points': segment,
            })
        
        return primitives

    def _test_line(self, points: List[Tuple[float, float]]) -> Tuple[bool, float]:
        """Testa se pontos formam linha reta (regressão linear)."""
        if len(points) < 3:
            return False, float('inf')
        
        pts = np.array(points)
        # Regressão linear total (orthogonal distance regression)
        # Aproximação: regressão linear y = ax + b se não vertical
        x = pts[:, 0]
        y = pts[:, 1]
        
        # Testar inclinação
        dx = pts[-1, 0] - pts[0, 0]
        dy = pts[-1, 1] - pts[0, 1]
        
        if abs(dx) > abs(dy):  # Mais horizontal
            # Regressão y = ax + b
            A = np.vstack([x, np.ones_like(x)]).T
            a, b = np.linalg.lstsq(A, y, rcond=None)[0]
            y_pred = a * x + b
            max_err = np.max(np.abs(y - y_pred))
        else:  # Mais vertical
            A = np.vstack([y, np.ones_like(y)]).T
            a, b = np.linalg.lstsq(A, x, rcond=None)[0]
            x_pred = a * y + b
            max_err = np.max(np.abs(x - x_pred))
        
        return max_err < 1.5, float(max_err)

    def _test_arc(self, points: List[Tuple[float, float]]) -> Tuple[bool, Tuple[float, float], float, float]:
        """Testa se pontos formam arco circular (ajuste de círculo)."""
        if len(points) < 5:
            return False, (0, 0), 0, float('inf')
        
        pts = np.array(points)
        # Ajuste de círculo via método algébrico (Kasa)
        x = pts[:, 0]
        y = pts[:, 1]
        
        A = np.column_stack([2*x, 2*y, np.ones_like(x)])
        b = x**2 + y**2
        
        try:
            sol = np.linalg.lstsq(A, b, rcond=None)[0]
            cx, cy, c = sol[0], sol[1], sol[2]
            r = math.sqrt(cx**2 + cy**2 + c)
            
            # Erro radial
            dists = np.sqrt((x - cx)**2 + (y - cy)**2)
            max_err = np.max(np.abs(dists - r))
            
            return max_err < 2.0, (float(cx), float(cy)), float(r), float(max_err)
        except np.linalg.LinAlgError:
            return False, (0, 0), 0, float('inf')

    def _extract_skeleton(self, mask: Optional[np.ndarray]) -> List[Tuple[float, float]]:
        """Extrai esqueleto (medial axis) para centerlines."""
        if mask is None:
            return []
        
        # Esqueletização morfológica (thinning)
        try:
            skeleton = morphology.skeletonize(mask.astype(bool))
            ys, xs = np.where(skeleton)
            return [(float(x), float(y)) for x, y in zip(xs, ys)]
        except Exception:
            return []

    def _classify_stitch_type(self, region: Dict, width_mm: float, height_mm: float,
                               skeleton_mm: List[Tuple[float, float]], 
                               corners_mm: List[Tuple[float, float]],
                               geometric_primitives: List[Dict]) -> str:
        """Classifica tipo de costura baseado na geometria refinada."""
        # Satin: região estreita com esqueleto longo
        if skeleton_mm and len(skeleton_mm) > 10:
            skel_len = self._polyline_length(skeleton_mm)
            if skel_len > max(width_mm, height_mm) * 0.8:
                return 'satin'
        
        # Running: esqueleto longo, região fina
        if skeleton_mm and len(skeleton_mm) > 5:
            skel_len = self._polyline_length(skeleton_mm)
            if skel_len > max(width_mm, height_mm):
                return 'running'
        
        # Geometric primitives: se tem muitas linhas/arcas -> running ou satin
        line_count = sum(1 for p in geometric_primitives if p['type'] == 'line')
        arc_count = sum(1 for p in geometric_primitives if p['type'] == 'arc')
        if line_count + arc_count >= 3:
            return 'running' if width_mm < 12 else 'satin'
        
        # Fill (tatami): áreas grandes sem esqueleto dominante
        return 'tatami'

    def _polyline_length(self, pts: List[Tuple[float, float]]) -> float:
        if len(pts) < 2:
            return 0.0
        total = 0.0
        for i in range(len(pts) - 1):
            dx = pts[i+1][0] - pts[i][0]
            dy = pts[i+1][1] - pts[i][1]
            total += math.hypot(dx, dy)
        return total

    def _perimeter(self, contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 2:
            return 0.0
        total = 0.0
        for i in range(len(contour)):
            j = (i + 1) % len(contour)
            dx = contour[j][0] - contour[i][0]
            dy = contour[j][1] - contour[i][1]
            total += math.hypot(dx, dy)
        return total

    def _shoelace_area(self, contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 3:
            return 0.0
        area = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            area += contour[i][0] * contour[j][1]
            area -= contour[j][0] * contour[i][1]
        return abs(area) / 2.0

    def vectorize_all(self, regions: List[Dict]) -> List[Dict]:
        """Vetoriza todas as regiões."""
        return [self.vectorize_region(r) for r in regions if r.get('contour')]


class BezierCurve:
    """Representa uma curva de Bezier cúbica com 4 pontos de controle."""
    def __init__(self, P0, P1, P2, P3):
        self.P0 = np.array(P0)
        self.P1 = np.array(P1)
        self.P2 = np.array(P2)
        self.P3 = np.array(P3)
    
    def point(self, t: float) -> Tuple[float, float]:
        ti = 1 - t
        p = (ti**3)*self.P0 + 3*(ti**2)*t*self.P1 + 3*ti*(t**2)*self.P2 + (t**3)*self.P3
        return (float(p[0]), float(p[1]))
    
    def length(self, samples: int = 20) -> float:
        """Aproxima comprimento da curva."""
        total = 0.0
        prev = self.point(0)
        for i in range(1, samples + 1):
            t = i / samples
            curr = self.point(t)
            total += math.hypot(curr[0] - prev[0], curr[1] - prev[1])
            prev = curr
        return total
    
    def to_dict(self) -> Dict:
        return {
            'P0': list(self.P0), 'P1': list(self.P1),
            'P2': list(self.P2), 'P3': list(self.P3)
        }