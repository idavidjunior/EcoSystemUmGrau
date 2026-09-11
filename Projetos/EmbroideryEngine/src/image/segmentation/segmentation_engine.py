"""
FASE 8 - Image Segmentation Engine

Pipeline de processamento de imagem para bordado:
1. Redução de cores (k-means / median cut)
2. Segmentação por cor (connected components)
3. Extração de contornos
4. Classificação de regiões
"""

import math
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

try:
    import numpy as np
    from PIL import Image
    from skimage import measure, morphology
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class ColorReductionEngine:
    """Redução de cores para simplificar a imagem."""

    def __init__(self, max_colors: int = 15):
        self.max_colors = max_colors

    def reduce(self, image: 'Image.Image') -> Tuple['Image.Image', List[Tuple[int, int, int]]]:
        """Reduz as cores da imagem e retorna imagem reduzida + paleta."""
        if not HAS_DEPS:
            raise ImportError("numpy, Pillow, scikit-image necessários")

        img_rgb = image.convert('RGB')
        pixels = np.array(img_rgb).reshape(-1, 3).astype(np.float32)

        n_colors = min(self.max_colors, len(set(map(tuple, pixels.tolist()))))
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
    """Segmenta imagem reduzida em regiões por cor."""

    def __init__(self, min_region_area: int = 50):
        self.min_region_area = min_region_area

    def segment(self, image: 'Image.Image',
                palette: List[Tuple[int, int, int]]) -> List[Dict]:
        """
        Segmenta a imagem em regiões conectadas por cor.

        Retorna lista de dicts:
        {
            'color_index': int,
            'color_rgb': (r, g, b),
            'mask': np.array (boolean),
            'contour': [(x, y), ...],
            'bounds': (min_x, min_y, max_x, max_y),
            'area': float,
            'width': float,
            'height': float,
            'aspect_ratio': float,
        }
        """
        if not HAS_DEPS:
            raise ImportError("numpy, Pillow, scikit-image necessários")

        img_rgb = np.array(image.convert('RGB'))
        regions = []

        for idx, color in enumerate(palette):
            r, g, b = color
            tolerance = 30
            mask = (
                (np.abs(img_rgb[:, :, 0].astype(int) - r) < tolerance) &
                (np.abs(img_rgb[:, :, 1].astype(int) - g) < tolerance) &
                (np.abs(img_rgb[:, :, 2].astype(int) - b) < tolerance)
            )

            mask_cleaned = morphology.remove_small_objects(mask, min_size=self.min_region_area)
            labeled = measure.label(mask_cleaned.astype(int))

            for region_id in range(1, labeled.max() + 1):
                region_mask = labeled == region_id
                area = region_mask.sum()

                if area < self.min_region_area:
                    continue

                ys, xs = np.where(region_mask)
                min_x, max_x = int(xs.min()), int(xs.max())
                min_y, max_y = int(ys.min()), int(ys.max())

                contour = self._extract_contour(region_mask)

                regions.append({
                    'color_index': idx,
                    'color_rgb': color,
                    'mask': region_mask,
                    'contour': contour,
                    'bounds': (min_x, min_y, max_x, max_y),
                    'area': float(area),
                    'width': float(max_x - min_x),
                    'height': float(max_y - min_y),
                    'aspect_ratio': float((max_x - min_x) / max(1, max_y - min_y)),
                })

        regions.sort(key=lambda r: r['area'], reverse=True)
        return regions

    def _extract_contour(self, mask) -> List[Tuple[float, float]]:
        """Extrai contorno de uma máscara booleana."""
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
