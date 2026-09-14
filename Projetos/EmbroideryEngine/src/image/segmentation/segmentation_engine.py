"""
FASE 8 - Image Segmentation Engine (Improved)

Pipeline de processamento de imagem para bordado com precisão profissional:
1. Edge detection (Canny) para detectar linhas finas e bordas
2. Redução de cores (k-means) preservando bordas
3. Segmentação por cor + bordas (connected components)
3. Extração de contornos com refinamento sub-pixel
4. Classificação de regiões por geometria
"""

import math
from typing import List, Tuple, Dict, Optional, Union
from collections import defaultdict

try:
    import numpy as np
    from PIL import Image, ImageFilter
    from skimage import measure, morphology, feature, filters, segmentation
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class ColorReductionEngine:
    """Redução de cores para simplificar a imagem."""

    def __init__(self, max_colors: int = 15):
        self.max_colors = max_colors

    def reduce(self, image: 'Image.Image') -> Tuple['Image.Image', List[Tuple[int, int, int]]]:
        """Reduz as cores da imagem usando K-means simples (sem peso de borda)."""
        if not HAS_DEPS:
            raise ImportError("numpy, Pillow, scikit-image necessários")

        img_rgb = image.convert('RGB')
        pixels = np.array(img_rgb).reshape(-1, 3).astype(np.float32)

        n_colors = min(self.max_colors, len(set(map(tuple, pixels.astype(int).tolist()))))
        if n_colors < 2:
            n_colors = 2

        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pixels)
        palette = kmeans.cluster_centers_.astype(int)

        new_pixels = palette[labels]
        result_array = new_pixels.reshape(np.array(img_rgb).shape)
        result = Image.fromarray(result_array.astype(np.uint8))

        palette_list = [tuple(c) for c in palette]
        return result, palette_list


class SegmentationEngine:
    """Segmenta imagem reduzida em regiões por cor com detecção de bordas."""

    def __init__(self, min_region_area: int = 50, edge_threshold: float = 0.1):
        self.min_region_area = min_region_area
        self.edge_threshold = edge_threshold

    def segment(self, image: 'Image.Image',
                palette: List[Tuple[int, int, int]]) -> List[Dict]:
        """
        Segmenta a imagem em regiões conectadas por cor + bordas.

        Retorna lista de dicts com geometria refinada.
        """
        if not HAS_DEPS:
            raise ImportError("numpy, Pillow, scikit-image necessários")

        img_rgb = np.array(image.convert('RGB'))
        img_gray = np.mean(np.array(image.convert('RGB')), axis=2)
        
        # Detectar bordas globais (Canny) para guiar segmentação
        edges = feature.canny(np.mean(np.array(image.convert('RGB')), axis=2)/255.0, 
                              sigma=1.0, low_threshold=0.05, high_threshold=0.15)
        
        regions = []

        # Identificar a cor de fundo e gerar a máscara APENAS das partes
        # conectadas à moldura da imagem. Elementos internos que usam a
        # mesma cor do fundo são preservados (ex.: letras brancas no interior
        # de um brasão sobre fundo branco).
        bg_mask = self._compute_background_mask(image, palette)

        for idx, color in enumerate(palette):
            r, g, b = color
            tolerance = 30
            mask = (
                (np.abs(img_rgb[:, :, 0].astype(int) - r) < tolerance) &
                (np.abs(img_rgb[:, :, 1].astype(int) - g) < tolerance) &
                (np.abs(img_rgb[:, :, 2].astype(int) - b) < tolerance)
            )

            # Refinar máscara com bordas
            mask = self._refine_mask_with_edges(mask, edges, img_rgb, (r, g, b))

            # Subtrair apenas o fundo conectado à moldura
            if bg_mask is not None:
                mask = mask & ~bg_mask

            mask_cleaned = morphology.remove_small_objects(mask, max_size=self.min_region_area)
            labeled = measure.label(mask_cleaned.astype(int))

            for region_id in range(1, labeled.max() + 1):
                region_mask = labeled == region_id
                area = region_mask.sum()

                if area < self.min_region_area:
                    continue

                ys, xs = np.where(region_mask)
                min_x, max_x = int(xs.min()), int(xs.max())
                min_y, max_y = int(ys.min()), int(ys.max())

                contour = self._extract_contour_subpixel(region_mask, img_rgb)

                # Calcular métricas geométricas
                area_val = float(area)
                width = float(max_x - min_x)
                height = float(max_y - min_y)
                aspect = width / max(1, height)

                regions.append({
                    'color_index': idx,
                    'color_rgb': color,
                    'mask': region_mask,
                    'contour': contour,
                    'bounds': (min_x, min_y, max_x, max_y),
                    'area': area_val,
                    'width': width,
                    'height': height,
                    'aspect_ratio': aspect,
                })

        regions.sort(key=lambda r: r['area'], reverse=True)
        return regions

    def _identify_background_color(self, image: 'Image.Image',
                                    palette: List[Tuple[int, int, int]]) -> int:
        """Identifica a cor de fundo.

        Prioriza a cor dominante na moldura (anel externo) da imagem, pois
        imagens com borda uniforme (foto/logo/recorte) quase sempre têm o
        fundo na moldura — mesmo quando não é a cor mais frequente no total
        (ex.: brasão escuro ocupando a maior área sobre fundo branco).
        Sem moldura dominante, usa a cor mais frequente (comportamento antigo).
        """
        arr = np.array(image)
        h, w = arr.shape[:2]
        ring = max(1, min(h, w) // 50)

        border_px = np.concatenate([
            arr[:ring].reshape(-1, 3),
            arr[h - ring:].reshape(-1, 3),
            arr[:, :ring].reshape(-1, 3),
            arr[:, w - ring:].reshape(-1, 3),
        ])

        border_counts = []
        for idx, (r, g, b) in enumerate(palette):
            mask = (
                (np.abs(border_px[:, 0].astype(int) - r) < 30) &
                (np.abs(border_px[:, 1].astype(int) - g) < 30) &
                (np.abs(border_px[:, 2].astype(int) - b) < 30)
            )
            border_counts.append((int(mask.sum()), idx))

        border_counts.sort(reverse=True)
        top_border_count, top_border_idx = border_counts[0]
        if top_border_count >= 0.55 * max(1, len(border_px)):
            return top_border_idx

        counts = []
        for idx, (r, g, b) in enumerate(palette):
            mask = (
                (np.abs(arr[:, :, 0].astype(int) - r) < 30) &
                (np.abs(arr[:, :, 1].astype(int) - g) < 30) &
                (np.abs(arr[:, :, 2].astype(int) - b) < 30)
            )
            counts.append((int(mask.sum()), idx))

        counts.sort(reverse=True)
        return counts[0][1]

    def _compute_background_mask(self, image: 'Image.Image',
                                  palette: List[Tuple[int, int, int]]) -> Optional[np.ndarray]:
        """Máscara booleana do fundo conectado à moldura da imagem.

        Elimina apenas os pixels da cor de fundo ligados à borda externa,
        preservando elementos dessa mesma cor totalmente contidos no interior
        (letras/detalhes vazados). Retorna None quando não há fundo detectado.
        """
        arr = np.array(image)
        bg_idx = self._identify_background_color(image, palette)
        r, g, b = palette[bg_idx]

        color_mask = (
            (np.abs(arr[:, :, 0].astype(int) - r) < 30) &
            (np.abs(arr[:, :, 1].astype(int) - g) < 30) &
            (np.abs(arr[:, :, 2].astype(int) - b) < 30)
        )
        if color_mask.sum() == 0:
            return None

        connected = self._border_connected(color_mask)
        if connected.sum() < max(8, 0.01 * color_mask.sum()):
            return None
        return connected

    def _border_connected(self, mask: np.ndarray) -> np.ndarray:
        """Mantém apenas os componentes de uma máscara que tocam a moldura."""
        labeled = measure.label(mask.astype(int))
        h, w = labeled.shape
        border_labels = set()
        border_labels.update(labeled[0].tolist())
        border_labels.update(labeled[h - 1].tolist())
        border_labels.update(labeled[:, 0].tolist())
        border_labels.update(labeled[:, w - 1].tolist())
        border_labels.discard(0)
        if not border_labels:
            return np.zeros_like(mask, dtype=bool)
        selected = np.isin(labeled, list(border_labels))
        return selected

    def _refine_mask_with_edges(self, mask: np.ndarray, edges: np.ndarray, 
                                 img_rgb: np.ndarray, target_color: Tuple[int, int, int]) -> np.ndarray:
        """Refina máscara usando informação de bordas - menos agressivo."""
        # Dilatar máscara levemente para incluir bordas próximas
        dilated = morphology.dilation(mask, morphology.disk(1))
        
        # Usar a máscara original como base (já filtrada por cor no loop principal)
        # Adicionar bordas próximas à região dilatada
        refined = mask | (edges & dilated)
        
        return refined

    def _extract_contour_subpixel(self, mask: np.ndarray, img_rgb: np.ndarray) -> List[Tuple[float, float]]:
        """Extrai contorno com precisão sub-pixel."""
        # 1. Contorno inicial com find_contours (já sub-pixel)
        contours = measure.find_contours(mask.astype(float), 0.5)
        if not contours:
            return []
        
        longest = max(contours, key=len)
        
        # 2. Tentar refinar com active contour (snake) se disponível
        try:
            # Usar gradiente da máscara para energia
            gradient = filters.sobel(mask.astype(float))
            
            # Inicializar snake no contorno encontrado
            snake = segmentation.active_contour(
                -gradient,  # Energia negativa = atrair para bordas fortes
                np.array(longest),
                alpha=0.01, beta=0.1, gamma=0.001,
                max_iterations=30
            )
            # Converter (row, col) -> (x, y)
            contour = [(float(p[1]), float(p[0])) for p in snake]
        except Exception:
            # Fallback: Douglas-Peucker no contorno original
            simplified = self._douglas_peucker(longest, epsilon=1.5)
            return [(float(p[1]), float(p[0])) for p in simplified]

        # Simplificar preservando cantos
        return self._douglas_peucker_corners(contour)

    def _extract_contour(self, mask) -> List[Tuple[float, float]]:
        """Extrai contorno de uma máscara booleana (fallback)."""
        contours = measure.find_contours(mask.astype(float), 0.5)
        if not contours:
            return []

        longest = max(contours, key=len)
        simplified = self._douglas_peucker(longest, epsilon=2.0)

        return [(float(p[1]), float(p[0])) for p in simplified]

    def _douglas_peucker(self, points, epsilon: float) -> list:
        """Simplificação de contorno Douglas-Peucker."""
        if len(points) <= 2:
            return points.tolist()

        dmax = 0
        index = 0
        end = len(points) - 1

        for i in range(1, end):
            d = self._point_line_distance(points[i], points[0], points[end])
            if d > dmax:
                index = i
                dmax = d

        if dmax > epsilon:
            left = self._douglas_peucker(points[:index + 1], epsilon)
            right = self._douglas_peucker(points[index:], epsilon)
            return left[:-1] + right
        else:
            return [points[0].tolist(), points[end].tolist()]

    def _douglas_peucker_corners(self, contour: List[Tuple[float, float]], 
                                  epsilon: float = 1.5, corner_threshold: float = 0.7) -> List[Tuple[float, float]]:
        """Douglas-Peucker preservando cantos detectados."""
        if len(contour) <= 2:
            return [(float(p[0]), float(p[1])) for p in contour]

        # Detectar cantos
        pts = np.array(contour)
        n = len(pts)
        corner_indices = set()
        
        for i in range(n):
            prev_idx = (i - 5) % n
            next_idx = (i + 5) % n
            
            v1 = pts[i] - pts[prev_idx]
            v2 = pts[(i + 5) % n] - pts[i]
            
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 > 1e-6 and norm2 > 1e-6:
                cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                if cos_angle < 0.7:  # Canto detectado
                    corner_indices.add(i)

        # Douglas-Peucker recursivo preservando cantos
        def dp_recursive(start, end):
            if end <= start + 1:
                return [contour[start]]
            
            dmax = 0
            index = 0
            for i in range(start + 1, end):
                if i in corner_indices:
                    continue  # Pular cantos (sempre manter)
                d = self._point_line_distance(contour[i], contour[start], contour[end])
                if d > dmax:
                    index = i
                    dmax = d

            if dmax > epsilon:
                left = dp_recursive(start, index)
                right = dp_recursive(index, end)
                return left + right
            else:
                return [contour[start], contour[end]]

        # Aplicar recursivo entre cada par de cantos consecutivos
        result = []
        sorted_corners = sorted(corner_indices)
        if not sorted_corners:
            return self._douglas_peucker(contour, epsilon)

        for i in range(len(sorted_corners)):
            start = sorted_corners[i]
            end = sorted_corners[(i + 1) % len(sorted_corners)]
            if end > start:
                segment = dp_recursive(start, end)
            else:
                segment = dp_recursive(start, len(contour)) + dp_recursive(0, end)
            result.extend(segment[:-1])  # Evitar duplicar ponto final
        
        return result

    def _point_line_distance(self, point, line_start, line_end) -> float:
        """Distância de um ponto a uma linha."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        return math.sqrt((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2)