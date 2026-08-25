#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serving / Predição Junk-ML.
Carrega modelo treinado e expõe função categorize_file(path).
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache
import warnings
warnings.filterwarnings("ignore")

# ─── Paths ───
BASE = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE / "models"
MODEL_PATH = MODELS_DIR / "model.joblib"
ENCODER_PATH = MODELS_DIR / "encoder.joblib"
METADATA_PATH = MODELS_DIR / "metadata.json"

# ─── Cache LRU ───
@lru_cache(maxsize=1024)
def _cached_predict(path_str: str) -> Dict[str, Any]:
    """Wrapper com cache LRU para paths repetidos."""
    return _predict_uncached(Path(path_str))


def _load_artifacts() -> tuple:
    """Carrega modelo, encoder e metadata (lazy loading)."""
    global _MODEL, _ENCODER, _METADATA, _FEATURES
    
    if not hasattr(_load_artifacts, "_MODEL"):
        _load_artifacts._MODEL = joblib.load(MODEL_PATH)
        _load_artifacts._ENCODER = joblib.load(ENCODER_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _load_artifacts._METADATA = json.load(f)
        _load_artifacts._FEATURES = _load_artifacts._METADATA["features"]
    
    return (
        _load_artifacts._MODEL,
        _load_artifacts._ENCODER,
        _load_artifacts._METADATA,
        _load_artifacts._FEATURES
    )


# ─── Feature Extraction (mesma lógica do generate_dataset) ───
# NOTE: Não usar constantes hardcoded! O label encoder do modelo define a ordem.
# As constantes abaixo são apenas para referência do generate_dataset.
# Em runtime, SEMPRE usar encoder.inverse_transform() do modelo.

TYPE_NAMES = {}  # Será preenchido no _load_artifacts
TYPE_NAMES_REVERSE = {}  # Será preenchido no _load_artifacts

LARGE_FILE_THRESHOLD = 20 * 1024 * 1024

APK_EXTS = {".apk", ".apks", ".xapk"}
LOG_EXTS = {".log", ".txt", ".crash", ".trace", ".dmp", ".dump"}
TEMP_EXTS = {".tmp", ".temp", ".bak", ".backup", ".swp", ".swx", ".swo"}
CACHE_DIRS = {"cache", "trash", "lixo", ".thumbnails", "thumbnails"}
TEMP_DIRS = {"temp", "tmp"}
MEDIA_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm",
              ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
              ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic",
              ".zip", ".rar", ".7z", ".tar", ".gz"}

NUMERIC_FEATURES = ["size_mb", "depth"]
CATEGORICAL_FEATURES = ["ext", "parent_name", "grandparent_name"]
BOOLEAN_FEATURES = [
    "has_apk_ext", "has_log_ext", "has_temp_ext", "is_media_ext",
    "name_has_cache", "name_has_temp", "name_has_trash",
    "name_is_thumbnails", "name_is_temp_dir",
    "is_hidden", "is_system_dir", "is_dir"
]


def _extract_features(path: Path) -> pd.DataFrame:
    """Extrai features de um único path (mesma lógica do generate_dataset)."""
    try:
        stat = path.stat()
        size = stat.st_size
    except (PermissionError, OSError, FileNotFoundError):
        return None
    
    name = path.name
    name_lower = name.lower()
    is_dir = path.is_dir()
    ext = path.suffix.lower()
    
    parts = path.parts
    depth = len(parts)
    parent_name = parts[-2].lower() if len(parts) >= 2 else ""
    grandparent_name = parts[-3].lower() if len(parts) >= 3 else ""
    
    feats = {
        "size_mb": round(size / (1024 * 1024), 2) if not is_dir else 0.0,
        "depth": depth,
        "ext": ext,
        "has_apk_ext": ext in {".apk", ".apks", ".xapk"},
        "has_log_ext": ext in {".log", ".txt", ".crash", ".trace", ".dmp", ".dump"},
        "has_temp_ext": ext in {".tmp", ".temp", ".bak", ".backup", ".swp", ".swx", ".swo"},
        "is_media_ext": ext in {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm",
                                ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
                                ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic",
                                ".zip", ".rar", ".7z", ".tar", ".gz"},
        "name_has_cache": any(x in name_lower for x in ("cache", "trash", "lixo")) or name_lower == ".thumbnails",
        "name_has_temp": "temp" in name_lower or "tmp" in name_lower,
        "name_has_trash": "trash" in name_lower or "lixo" in name_lower,
        "name_is_thumbnails": name_lower == ".thumbnails" or "thumbnail" in name_lower,
        "name_is_temp_dir": parent_name in {"temp", "tmp"} or name_lower in ("temp", "tmp"),
        "is_hidden": name.startswith("."),
        "is_system_dir": any(x in str(path).lower() for x in ("/android/data", "/android/obb", "/windows", "/program files", "/system32")),
        "is_dir": is_dir,
        "parent_name": parent_name,
        "grandparent_name": grandparent_name,
    }
    
    # Garante ordem das features
    row = {k: feats[k] for k in [
        "size_mb", "depth", "ext", "parent_name", "grandparent_name",
        "has_apk_ext", "has_log_ext", "has_temp_ext", "is_media_ext",
        "name_has_cache", "name_has_temp", "name_has_trash",
        "name_is_thumbnails", "name_is_temp_dir",
        "is_hidden", "is_system_dir", "is_dir"
    ]}
    
    return pd.DataFrame([row])


def _predict_uncached(path: Path) -> Dict[str, Any]:
    """Predição sem cache."""
    model, encoder, metadata, features = _load_artifacts()
    
    # Extrai features
    df = _extract_features(path)
    if df is None:
        return {"label": -1, "label_name": "error", "confidence": 0.0, "error": "cannot_access"}
    
    # Reordena colunas
    df = df[metadata["features"]]
    
    # Predição
    try:
        pred_enc = model.predict(df)[0]
        proba = model.predict_proba(df)[0]
        confidence = float(np.max(proba))
        label = int(pred_enc)
        label_name = encoder.inverse_transform([pred_enc])[0]
    except Exception as e:
        return {"label": -1, "label_name": "error", "confidence": 0.0, "error": str(e)}
    
    return {
        "label": label,
        "label_name": label_name,
        "confidence": confidence,
        "path": str(path)
    }


# ─── API Pública ───
def categorize_file(path: str) -> Dict[str, Any]:
    """
    Classifica um arquivo/diretório.
    
    Args:
        path: Caminho do arquivo/diretório
        
    Returns:
        dict com label, label_name, confidence, path
    """
    return _cached_predict(path)


def categorize_batch(paths: List[str]) -> List[Dict[str, Any]]:
    """Classifica múltiplos arquivos (sem cache para batch)."""
    return [_predict_uncached(Path(p)) if isinstance(p, str) else _predict_uncached(p) for p in paths]


def get_model_info() -> Dict[str, Any]:
    """Retorna metadata do modelo carregado."""
    _, _, metadata, _ = _load_artifacts()
    return metadata


def log_correction(path: str, corrected_label_name: str, confidence: float = 0.0) -> bool:
    """
    Registra correção do usuário para retreino automático.
    
    Args:
        path: Caminho do arquivo que foi classificado
        corrected_label_name: Nome do label correto (ex: "apk", "cache", "log")
        confidence: Confiança da predição original
        
    Returns:
        True se feedback foi registrado
    """
    # Obtém a predição original para saber o que o modelo previu
    result = categorize_file(path)
    if result.get("label") == -1:
        return False
    
    predicted_label = result["label"]
    corrected_label = TYPE_NAMES_REVERSE.get(corrected_label_name.lower())
    if corrected_label is None:
        return False
    
    # Extrai features do arquivo
    from pathlib import Path as _Path
    feats_df = _extract_features(_Path(path))
    if feats_df is None:
        return False
    
    features = feats_df.iloc[0].to_dict()
    
    # Loga correção (integra com pipeline contínuo)
    try:
        from ..data.feedback_collector import log_correction
        return log_correction(features, result["label"], corrected_label, result["confidence"], path)
    except Exception:
        return False


def warmup():
    """Pré-carrega artefatos (útil no startup)."""
    _load_artifacts()
    print("[warmup] Modelo carregado")


# ─── CLI ───
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Junk-ML Predict")
    parser.add_argument("paths", nargs="+", help="Arquivos/diretórios para classificar")
    parser.add_argument("--info", action="store_true", help="Mostra info do modelo")
    args = parser.parse_args()
    
    if args.info:
        info = get_model_info()
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return
    
    results = categorize_batch(args.paths)
    for r in results:
        print(f"{r['label_name']:12} ({r['confidence']:.3f})  {r['path']}")


if __name__ == "__main__":
    main()