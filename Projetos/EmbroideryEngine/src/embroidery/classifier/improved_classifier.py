"""
FASE 10.5 - Improved Stitch Classifier (Contour / Text / Orientation)

Classificador avançado de tipo de costura que adiciona, sobre as regras
atuais (ObjectClassifier como fallback):

1. OUTLINE/CONTOUR — região cuja área de preenchimento é pequena relativa
   ao perímetro (raio hidráulico baixo) ou que possui buraco interno
   significativo (anel/coroa) -> OUTLINE (costurado como RUN no planner).
2. TEXTO — traços finos e pequenos, ou clusters de pequenas regiões
   próximas com orientação consistente -> RUN.
3. ÂNGULO DOMINANTE — orientação principal da região via PCA da máscara
   (skimage.measure.regionprops.orientation) ou PCA dos pontos do contorno
   quando a máscara não está disponível. NUNCA ângulo fixo zero.
4. FALLBACK — quando nenhuma heurística bate com confiança, delega para o
   classificador atual (ObjectClassifier), preservando o comportamento
   existente e garantindo zero regressão.

Interface (compatível com ObjectClassifier):
- classify(region) -> StitchType
- classify_with_metadata(region) -> dict
  {stitch_type, direction_angle, confidence, classification_source}
- classify_all(regions) -> list[dict]  (injeta chaves no dict de cada região)

O pipeline (digitizer_pipeline / stitch_planner) passa a ler o ângulo de
region['direction_angle'] e preencher EmbroideryObject.direction_angle.
"""

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from ...core.design.embroidery_design import StitchType
from .object_classifier import ObjectClassifier

try:
    from skimage import measure
    HAS_SKIMAGE = True
except Exception:  # pragma: no cover - fallback para PCA do contorno
    HAS_SKIMAGE = False


class ImprovedStitchClassifier:
    """Classificador de costura com detecção de contorno, texto e orientação.

    Atributos de ajuste (thresholds públicos para calibração):
      OUTLINE_HOLE_FRACTION : buraco mínimo (fração da filled_area) p/ OUTLINE
      OUTLINE_MAX_STROKE   : raio hidráulico máximo aceito p/ OUTLINE (mm)
      RUN_MAX_STROKE       : traço máximo p/ RUN (mm)
      TEXT_MAX_AREA        : área máxima de glifo p/ candidato a texto (mm²)
      TEXT_MAX_HEIGHT      : altura máxima de glifo p/ candidato a texto (mm)
      TEXT_CLUSTER_MIN     : nº mínimo de candidatos próximos p/ cluster
      TEXT_CLUSTER_DIST    : distância máxima centro-a-centro p/ cluster (mm)
      SATIN_MIN_ECCENTRICITY / SATIN_MIN_ASPECT
      TATAMI_MIN_AREA      : área mínima p/ TATAMI (mm²)
      FILL_MIN_AREA        : área mínima p/ FILL (mm²)
      FILL_MIN_DIM         : menor dimensão mínima p/ FILL (mm)
      FALLBACK_CONFIDENCE  : confiança atribuída quando usa fallback
    """

    OUTLINE_HOLE_FRACTION = 0.15
    OUTLINE_MAX_STROKE = 5.0
    RUN_MAX_STROKE = 1.5
    RUN_MIN_ASPECT = 4.0
    TEXT_MAX_AREA = 50.0
    TEXT_MAX_HEIGHT = 8.0
    TEXT_MIN_ECC_FOR_ORIENTATION = 0.5
    TEXT_ORIENTATION_TOL_DEG = 25.0
    TEXT_CLUSTER_MIN = 3
    TEXT_CLUSTER_DIST = 14.0
    SATIN_MIN_ECCENTRICITY = 0.85
    SATIN_MIN_ASPECT = 2.5
    SATIN_MAX_STROKE = 8.0
    SATIN_MAX_WIDTH = 12.0
    TATAMI_MIN_AREA = 200.0
    TATAMI_MAX_ASPECT = 2.5
    FILL_MIN_AREA = 30.0
    FILL_MIN_DIM = 5.0
    FALLBACK_CONFIDENCE = 0.5

    def __init__(self, fallback: Optional[object] = None,
                 default_scale_mm: float = 0.2):
        self.fallback = fallback or ObjectClassifier()
        self.default_scale_mm = default_scale_mm

    # ============================================================
    # API pública (compatível com ObjectClassifier)
    # ============================================================

    def classify(self, region: Dict) -> StitchType:
        """Retorna o StitchType da região (assinatura compatível)."""
        return self.classify_with_metadata(region)['stitch_type']

    def classify_with_metadata(self, region: Dict) -> Dict:
        """Retorna {stitch_type, direction_angle, confidence, classification_source}."""
        feats = self._features(region)
        candidate = self._text_candidate(feats)
        stitch_type, confidence = self._decide(feats)
        source = 'heuristic'

        if stitch_type is None:
            # Fallback para as regras atuais (ObjectClassifier)
            try:
                stitch_type = self.fallback.classify(region)
            except Exception:
                stitch_type = StitchType.FILL
            confidence = self.FALLBACK_CONFIDENCE
            source = 'fallback'

        return {
            'stitch_type': stitch_type,
            'direction_angle': feats['orientation_deg'],
            'confidence': confidence,
            'classification_source': source,
            '_text_candidate': candidate,
        }

    def classify_all(self, regions: List[Dict]) -> List[Dict]:
        """Classifica todas as regiões e injeta chaves no dict de cada uma.

        Faz detecção contextual de texto: clusters de pequenos candidatos
        próximos (com orientação consistente quando alongados) viram RUN.
        """
        # 1. Classificação individual + marcação de candidatos a texto
        results = []
        for region in regions:
            meta = self.classify_with_metadata(region)
            results.append((region, meta))

        # 2. Detecção de cluster de texto
        text_cluster_ids = self._detect_text_clusters(results)

        # 3. Aplicar decisão final
        for idx, (region, meta) in enumerate(results):
            if idx in text_cluster_ids and meta['stitch_type'] is not StitchType.RUN:
                meta = dict(meta)
                meta['stitch_type'] = StitchType.RUN
                meta['confidence'] = max(meta['confidence'], 0.8)
                meta['classification_source'] = 'text_cluster'

            region['stitch_type'] = meta['stitch_type']
            region['direction_angle'] = meta['direction_angle']
            region['classification_confidence'] = meta['confidence']
            region['classification_source'] = meta['classification_source']

        return regions

    # Alias para compatibilidade com ObjectClassifier.assign_all
    assign_all = classify_all

    # ============================================================
    # Features geométricas
    # ============================================================

    def _features(self, region: Dict) -> Dict:
        """Extrai features em mm a partir da região (máscara ou contorno)."""
        scale = float(region.get('scale_mm', self.default_scale_mm) or self.default_scale_mm)
        mask = region.get('mask')
        contour_mm = region.get('contour_mm') or region.get('centered_mm')
        contour_mm = contour_mm if contour_mm else None

        # Métricas em mm (prioriza as já calculadas pela vectorização)
        area = float(region.get('area_mm2', 0.0) or 0.0)
        perim = float(region.get('perimeter_mm', 0.0) or 0.0)
        width = float(region.get('width_mm', 0.0) or 0.0)
        height = float(region.get('height_mm', 0.0) or 0.0)
        aspect = float(region.get('aspect_ratio', 0.0) or 0.0)

        # Fallback: calcular do contorno em mm
        if (area <= 0 or perim <= 0) and contour_mm is not None and len(contour_mm) >= 3:
            area = self._shoelace_area(contour_mm)
            perim = self._perimeter(contour_mm)
        if (width <= 0 or height <= 0) and contour_mm:
            xs = [p[0] for p in contour_mm]
            ys = [p[1] for p in contour_mm]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)

        # Regiões da segmentação usam width/height/area em pixels
        if area <= 0:
            area = float(region.get('area', 0.0) or 0.0) * scale * scale
        if width <= 0:
            width = float(region.get('width', 0.0) or 0.0) * scale
        if height <= 0:
            height = float(region.get('height', 0.0) or 0.0) * scale
        if aspect <= 0 and height > 0:
            aspect = width / height
        if aspect <= 0:
            aspect = 1.0

        circularity = 0.0
        if perim > 0:
            circularity = 4.0 * math.pi * area / (perim * perim)
        stroke = 0.0
        if perim > 0 and area > 0:
            stroke = 2.0 * area / perim

        # Orientação + excentricidade + buracos (máscara ou PCA do contorno)
        hole_fraction = 0.0
        orientation_deg = self._contour_pca_angle(contour_mm) if contour_mm else 0.0
        eccentricity = self._contour_eccentricity(contour_mm) if contour_mm else 0.0

        if mask is not None and HAS_SKIMAGE and np.any(np.asarray(mask)):
            try:
                props = measure.regionprops(np.asarray(mask, dtype=np.int32))
                if props:
                    p = props[0]
                    filled = float(getattr(p, 'area_filled', None) or p.filled_area)
                    if filled > 0:
                        hole_fraction = max(0.0, (filled - float(p.area)) / filled)
                    orientation_deg = math.degrees(float(p.orientation)) % 180.0
                    eccentricity = float(p.eccentricity)
            except Exception:
                pass

        return {
            'area': area,
            'perimeter': perim,
            'width': width,
            'height': height,
            'aspect': aspect,
            'circularity': circularity,
            'stroke': stroke,
            'hole_fraction': hole_fraction,
            'orientation_deg': orientation_deg,
            'eccentricity': eccentricity,
        }

    # ============================================================
    # Heurística de decisão
    # ============================================================

    def _decide(self, f: Dict) -> Tuple[Optional[StitchType], float]:
        """Decide o tipo com base nas features. Retorna (None, 0) p/ fallback."""
        stroke = f['stroke']
        area = f['area']
        perimeter = f['perimeter']
        aspect = f['aspect']
        hole = f['hole_fraction']
        ecc = f['eccentricity']
        width = f['width']
        height = f['height']
        min_dim = min(width, height)

        # OUTLINE/CONTOUR: região oca (anel/coroa) OU traço fino fechado
        if hole > self.OUTLINE_HOLE_FRACTION and stroke < self.OUTLINE_MAX_STROKE:
            if aspect < 4.0:
                return StitchType.OUTLINE, 0.9
        if hole > self.OUTLINE_HOLE_FRACTION and stroke < 3.0:
            # Coroa bem alongada ainda é contorno (ex.: moldura de borda)
            return StitchType.OUTLINE, 0.85

        # RUN: fio / linha fina alongada (proporção alta)
        if stroke < self.RUN_MAX_STROKE and aspect > self.RUN_MIN_ASPECT:
            return StitchType.RUN, 0.85

        # RUN: traço pequeno e fino (glifo isolado / detalhe)
        if stroke < self.RUN_MAX_STROKE and area < self.TEXT_MAX_AREA * 1.5:
            if height < self.TEXT_MAX_HEIGHT + 2.0:
                return StitchType.RUN, 0.7

        # SATIN: coluna estreita e alongada
        is_slim = width < self.SATIN_MAX_WIDTH or stroke < self.SATIN_MAX_STROKE
        is_elongated = ecc > self.SATIN_MIN_ECCENTRICITY or aspect > self.SATIN_MIN_ASPECT
        if is_slim and is_elongated:
            return StitchType.SATIN, 0.85

        # TATAMI: área grande e compacta
        if area > self.TATAMI_MIN_AREA and aspect < self.TATAMI_MAX_ASPECT:
            return StitchType.TATAMI, 0.8

        # FILL: área cheia e compacta (média)
        if area >= self.FILL_MIN_AREA and min_dim >= self.FILL_MIN_DIM:
            return StitchType.FILL, 0.7

        # Sem heurística confiante -> fallback
        return None, 0.0

    def _text_candidate(self, f: Dict) -> bool:
        """Candidato a glifo de texto: pequeno, fino, de baixa altura."""
        return (
            f['stroke'] < self.RUN_MAX_STROKE + 0.5
            and f['area'] < self.TEXT_MAX_AREA
            and f['height'] < self.TEXT_MAX_HEIGHT
            and f['aspect'] < self.RUN_MIN_ASPECT
        )

    def _detect_text_clusters(self, results: List[Tuple[Dict, Dict]]) -> set:
        """Agrupa candidatos a texto por proximidade e consistência de ângulo.

        Retorna índices das regiões que pertencem a um cluster de >=
        TEXT_CLUSTER_MIN candidatos próximos. Quando os glifos são alongados
        (ecc >= TEXT_MIN_ECC_FOR_ORIENTATION) exige orientação consistente.
        """
        candidates = []
        for idx, (region, meta) in enumerate(results):
            feats = self._features(region)
            if meta.get('_text_candidate') or self._text_candidate(feats):
                bounds = region.get('bounds_mm') or (0, 0, 0, 0)
                candidates.append({
                    'idx': idx,
                    'x': bounds[0] + (bounds[2] - bounds[0]) / 2.0,
                    'y': bounds[1] + (bounds[3] - bounds[1]) / 2.0,
                    'angle': feats['orientation_deg'],
                    'ecc': feats['eccentricity'],
                })

        if len(candidates) < self.TEXT_CLUSTER_MIN:
            return set()

        clusters = []
        for cand in candidates:
            placed = False
            for cl in clusters:
                ref = cl[0]
                dist = math.hypot(cand['x'] - ref['x'], cand['y'] - ref['y'])
                if dist <= self.TEXT_CLUSTER_DIST:
                    # Consistência de orientação quando alongado
                    max_ecc = max(cand['ecc'], ref['ecc'])
                    if max_ecc >= self.TEXT_MIN_ECC_FOR_ORIENTATION:
                        diff = abs(cand['angle'] - ref['angle'])
                        diff = min(diff, 180.0 - diff)
                        if diff > self.TEXT_ORIENTATION_TOL_DEG:
                            continue
                    cl.append(cand)
                    placed = True
                    break
            if not placed:
                clusters.append([cand])

        cluster_ids = set()
        for cl in clusters:
            if len(cl) >= self.TEXT_CLUSTER_MIN:
                for cand in cl:
                    cluster_ids.add(cand['idx'])
        return cluster_ids

    # ============================================================
    # Cálculos geométricos auxiliares (numpy puro, sem skimage)
    # ============================================================

    def _contour_pca_angle(self, contour: List[Tuple[float, float]]) -> float:
        """Ângulo dominante (0-180°) via PCA dos pontos do contorno."""
        if not contour or len(contour) < 3:
            return 0.0
        pts = self._resample_contour(contour, 200)
        if pts.shape[0] < 3:
            return 0.0
        pts = pts - pts.mean(axis=0)
        cov = np.cov(pts.T)
        try:
            eigvals, eigvecs = np.linalg.eigh(cov)
        except np.linalg.LinAlgError:
            return 0.0
        main = eigvecs[:, int(np.argmax(eigvals))]
        angle = math.degrees(math.atan2(main[1], main[0]))
        return angle % 180.0

    def _contour_eccentricity(self, contour: List[Tuple[float, float]]) -> float:
        """Excentricidade aproximada a partir dos autovalores da PCA."""
        if not contour or len(contour) < 3:
            return 0.0
        pts = self._resample_contour(contour, 200)
        if pts.shape[0] < 3:
            return 0.0
        pts = pts - pts.mean(axis=0)
        cov = np.cov(pts.T)
        try:
            eigvals = np.linalg.eigvalsh(cov)
        except np.linalg.LinAlgError:
            return 0.0
        eigvals = np.sort(eigvals)[::-1]
        if eigvals[0] <= 1e-9:
            return 0.0
        ratio = max(0.0, eigvals[1] / eigvals[0])
        return math.sqrt(max(0.0, 1.0 - ratio))

    def _resample_contour(self, contour: List[Tuple[float, float]],
                          target: int = 200) -> np.ndarray:
        """Reamostra o contorno por comprimento de arco (amostragem uniforme)."""
        pts = np.asarray(contour, dtype=float)
        n = len(pts)
        if n < 2:
            return pts
        if n <= target:
            return pts

        seg_lens = np.sqrt(np.sum(np.diff(pts, axis=0) ** 2, axis=1))
        total = float(np.sum(seg_lens))
        if total <= 1e-9:
            return pts[:target]

        cum = np.concatenate([[0.0], np.cumsum(seg_lens)]) / total
        targets = np.linspace(0.0, 1.0, target)
        out = []
        for t in targets:
            idx = int(np.searchsorted(cum, t) - 1)
            idx = max(0, min(idx, n - 2))
            seg_t = (t - cum[idx]) / max(cum[idx + 1] - cum[idx], 1e-9)
            seg_t = min(max(seg_t, 0.0), 1.0)
            out.append(pts[idx] + seg_t * (pts[idx + 1] - pts[idx]))
        return np.asarray(out, dtype=float)

    @staticmethod
    def _shoelace_area(contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 3:
            return 0.0
        area = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            area += contour[i][0] * contour[j][1]
            area -= contour[j][0] * contour[i][1]
        return abs(area) / 2.0

    @staticmethod
    def _perimeter(contour: List[Tuple[float, float]]) -> float:
        if len(contour) < 2:
            return 0.0
        total = 0.0
        n = len(contour)
        for i in range(n):
            j = (i + 1) % n
            total += math.hypot(contour[j][0] - contour[i][0],
                                contour[j][1] - contour[i][1])
        return total