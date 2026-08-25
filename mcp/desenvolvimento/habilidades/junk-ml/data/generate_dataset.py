#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Generator para JunkScanner ML.
Extrai features do sistema de arquivos e usa o classificador baseado em regras
como label ground-truth para treino supervisionado.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import platform

# ─── Categorias (espelham JunkItem.java) ───
TYPE_CACHE = 0
TYPE_TEMP = 1
TYPE_APK = 2
TYPE_LOG = 3
TYPE_EMPTY_DIR = 4
TYPE_LARGE_FILE = 5
TYPE_DOWNLOAD = 6  # Futuro

TYPE_NAMES = {
    TYPE_CACHE: "cache",
    TYPE_TEMP: "temp",
    TYPE_APK: "apk",
    TYPE_LOG: "log",
    TYPE_EMPTY_DIR: "empty_dir",
    TYPE_LARGE_FILE: "large_file",
    TYPE_DOWNLOAD: "download",
}

LARGE_FILE_THRESHOLD = 20 * 1024 * 1024  # 20MB

# Extensões por categoria
APK_EXTS = {".apk", ".apks", ".xapk"}
LOG_EXTS = {".log", ".txt", ".crash", ".trace", ".dmp", ".dump"}
TEMP_EXTS = {".tmp", ".temp", ".bak", ".backup", ".swp", ".swx", ".swo"}
CACHE_DIRS = {"cache", "trash", "lixo", ".thumbnails", "thumbnails"}
TEMP_DIRS = {"temp", "tmp"}

MEDIA_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm",
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic",
    ".zip", ".rar", ".7z", ".tar", ".gz"
}

@dataclass
class FileFeatures:
    """Features extraídas de um arquivo/diretório."""
    # Identificação
    path: str
    name: str
    is_dir: bool
    
    # Tamanho
    size_bytes: int
    size_mb: float
    
    # Caminho/estrutura
    depth: int
    parent_name: str
    grandparent_name: str
    
    # Extensão/tipo
    ext: str
    has_apk_ext: bool
    has_log_ext: bool
    has_temp_ext: bool
    is_media_ext: bool
    
    # Padrões de nome
    name_has_cache: bool
    name_has_temp: bool
    name_has_trash: bool
    name_is_thumbnails: bool
    name_is_temp_dir: bool
    
    # Sistema
    is_hidden: bool
    is_system_dir: bool
    
    # Label (ground truth do classificador de regras)
    label: int
    label_name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def classify_by_rules(path: Path) -> int:
    """
    Replica a lógica do ScanEngine.java para gerar ground-truth.
    Retorna o tipo da categoria (0-5).
    """
    name = path.name.lower()
    is_dir = path.is_dir()
    
    if is_dir:
        # Diretórios
        if any(x in name for x in ("cache", "trash", "lixo")) or name == ".thumbnails":
            return TYPE_CACHE
        if name == "temp" or name == "tmp" or "temp" in name:
            return TYPE_TEMP
        # Verifica se vazio
        try:
            if not any(path.iterdir()):
                return TYPE_EMPTY_DIR
        except (PermissionError, OSError):
            pass
        return -1  # Diretório não classificado como junk
    
    # Arquivos
    try:
        size = path.stat().st_size
    except (PermissionError, OSError, FileNotFoundError):
        return -1
    
    ext = path.suffix.lower()
    name_lower = path.name.lower()
    
    # APK
    if ext in APK_EXTS:
        return TYPE_APK
    
    # Log
    if ext in LOG_EXTS or "log" in name_lower or "crash" in name_lower:
        return TYPE_LOG
    
    # Temp
    if ext in TEMP_EXTS or "temp" in name_lower or "tmp" in name_lower:
        return TYPE_TEMP
    
    # Large file
    if size >= LARGE_FILE_THRESHOLD:
        return TYPE_LARGE_FILE
    
    return -1  # Não classificado


def extract_features(path: Path, label: int) -> Optional[FileFeatures]:
    """Extrai features de um arquivo/diretório."""
    try:
        stat = path.stat()
        size = stat.st_size
    except (PermissionError, OSError, FileNotFoundError):
        return None
    
    name = path.name
    name_lower = name.lower()
    is_dir = path.is_dir()
    ext = path.suffix.lower()
    
    # Profundidade no caminho
    parts = path.parts
    depth = len(parts)
    parent_name = parts[-2].lower() if len(parts) >= 2 else ""
    grandparent_name = parts[-3].lower() if len(parts) >= 3 else ""
    
    return FileFeatures(
        path=str(path),
        name=name,
        is_dir=is_dir,
        size_bytes=size if not is_dir else 0,
        size_mb=round(size / (1024 * 1024), 2) if not is_dir else 0.0,
        depth=depth,
        parent_name=parent_name,
        grandparent_name=grandparent_name,
        ext=ext,
        has_apk_ext=ext in APK_EXTS,
        has_log_ext=ext in LOG_EXTS,
        has_temp_ext=ext in TEMP_EXTS,
        is_media_ext=ext in MEDIA_EXTS,
        name_has_cache="cache" in name_lower or "trash" in name_lower or "lixo" in name_lower,
        name_has_temp="temp" in name_lower or "tmp" in name_lower,
        name_has_trash="trash" in name_lower or "lixo" in name_lower,
        name_is_thumbnails=name_lower == ".thumbnails" or "thumbnail" in name_lower,
        name_is_temp_dir=parent_name in TEMP_DIRS or name_lower in ("temp", "tmp"),
        is_hidden=name.startswith("."),
        is_system_dir=any(x in str(path).lower() for x in ("/android/data", "/android/obb", "/windows", "/program files", "/system32")),
        label=label,
        label_name=TYPE_NAMES.get(label, "unknown")
    )


def scan_directory(root: Path, max_files: int = 50000) -> List[FileFeatures]:
    """Escaneia diretório e extrai features + labels."""
    features_list = []
    count = 0
    
    print(f"[scan] Iniciando em: {root}")
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip protected dirs
        dirpath_lower = dirpath.lower()
        if "/android/data" in dirpath_lower or "/android/obb" in dirpath_lower:
            continue
        
        # Diretórios
        for dname in dirnames[:]:  # copy to allow modification
            dpath = Path(dirpath) / dname
            try:
                label = classify_by_rules(dpath)
                if label >= 0:
                    feats = extract_features(dpath, label)
                    if feats:
                        features_list.append(feats)
                        count += 1
            except Exception:
                pass
            
            if count >= max_files:
                break
        
        if count >= max_files:
            break
        
        # Arquivos
        for fname in filenames:
            fpath = Path(dirpath) / fname
            try:
                label = classify_by_rules(fpath)
                if label >= 0:
                    feats = extract_features(fpath, label)
                    if feats:
                        features_list.append(feats)
                        count += 1
            except Exception:
                pass
            
            if count >= max_files:
                break
        
        if count >= max_files:
            break
    
    print(f"[scan] Coletados {len(features_list)} samples")
    return features_list


def balance_dataset(samples: List[FileFeatures], max_per_class: int = 2000) -> List[FileFeatures]:
    """Balanceia o dataset limitando samples por classe."""
    by_class: Dict[int, List[FileFeatures]] = {}
    for s in samples:
        by_class.setdefault(s.label, []).append(s)
    
    balanced = []
    for cls, items in by_class.items():
        balanced.extend(items[:max_per_class])
        print(f"  Classe {TYPE_NAMES[cls]} ({cls}): {len(items)} -> {min(len(items), max_per_class)}")
    
    return balanced


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gera dataset Junk-ML")
    parser.add_argument("--root", default=None, help="Diretório raiz para escanear")
    parser.add_argument("--output", default="dataset.jsonl", help="Arquivo de saída")
    parser.add_argument("--max-files", type=int, default=50000, help="Máximo de arquivos")
    parser.add_argument("--max-per-class", type=int, default=2000, help="Máximo por classe")
    parser.add_argument("--balance", action="store_true", help="Balancear classes")
    args = parser.parse_args()
    
    # Default root: storage externo simulado (diretório atual)
    if args.root:
        root = Path(args.root)
    else:
        root = Path.cwd()
    
    if not root.exists():
        print(f"[ERRO] Root não existe: {root}")
        return 1
    
    print(f"[main] Gerando dataset de {root}")
    
    samples = scan_directory(root, args.max_files)
    
    if args.balance:
        samples = balance_dataset(samples, args.max_per_class)
    
    # Salva
    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
    
    print(f"[main] Dataset salvo em {out_path} ({len(samples)} samples)")
    
    # Stats
    from collections import Counter
    cnt = Counter(s.label_name for s in samples)
    print("[stats] Distribuição:")
    for k, v in cnt.most_common():
        print(f"  {k}: {v}")
    
    return 0


if __name__ == "__main__":
    exit(main())