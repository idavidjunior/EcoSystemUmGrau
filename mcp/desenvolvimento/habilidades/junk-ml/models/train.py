#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Treino do modelo Junk-ML.
Lê dataset.jsonl, treina classificador (LightGBM/Sklearn), salva modelo + metadata.
"""
import json
import argparse
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings("ignore")

# Tenta importar LightGBM (opcional)
try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
    print("[warn] LightGBM não instalado, usando RandomForest")

# ─── Features & Target ───
NUMERIC_FEATURES = [
    "size_mb", "depth"
]

CATEGORICAL_FEATURES = [
    "ext", "parent_name", "grandparent_name"
]

BOOLEAN_FEATURES = [
    "has_apk_ext", "has_log_ext", "has_temp_ext", "is_media_ext",
    "name_has_cache", "name_has_temp", "name_has_trash",
    "name_is_thumbnails", "name_is_temp_dir",
    "is_hidden", "is_system_dir", "is_dir"
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES

TARGET_COL = "label"


def load_dataset(path: Path) -> pd.DataFrame:
    """Carrega dataset JSONL para DataFrame."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    df = pd.DataFrame(records)
    print(f"[load] {len(df)} samples, {df['label_name'].nunique()} classes")
    return df


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara features combinadas em um único DataFrame."""
    # Features numéricas
    X_num = df[NUMERIC_FEATURES].fillna(0).astype(float)
    
    # Features categóricas
    X_cat = df[CATEGORICAL_FEATURES].fillna("unknown").astype(str)
    
    # Features booleanas
    X_bool = df[BOOLEAN_FEATURES].astype(int)
    
    # Combina tudo em um DataFrame com colunas nomeadas
    X = pd.concat([X_num, X_cat, X_bool], axis=1)
    return X


def build_pipeline(use_lgbm: bool = False) -> Pipeline:
    """Constrói pipeline de pré-processamento + classificador."""
    # Pré-processamento
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("bool", "passthrough", BOOLEAN_FEATURES),
        ],
        remainder="drop"
    )
    
    if use_lgbm and HAS_LGBM:
        clf = lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=8,
            num_leaves=63,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )
    else:
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
    
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", clf)
    ])
    return pipeline


def train_model(
    data_path: Path,
    model_path: Path,
    metadata_path: Path,
    encoder_path: Path,
    use_lgbm: bool = False,
    test_size: float = 0.2
) -> Dict[str, Any]:
    """Treina modelo completo."""
    
    print(f"[train] Carregando dataset: {data_path}")
    df = load_dataset(data_path)
    
    # Label encoder
    le = LabelEncoder()
    df["label_enc"] = le.fit_transform(df["label_name"])
    
    # Features combinadas
    X = prepare_features(df)
    y = df["label_enc"]
    
    # Split estratificado
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        stratify=y,
        random_state=42
    )
    
    # Build pipeline
    pipeline = build_pipeline(use_lgbm)
    
    print("[train] Treinando...")
    pipeline.fit(X_train, y_train)
    
    # Avaliação
    print("[train] Avaliando...")
    y_pred = pipeline.predict(X_test)
    
    # Decode labels para relatório
    y_test_decoded = le.inverse_transform(y_test)
    y_pred_decoded = le.inverse_transform(y_pred)
    
    acc = accuracy_score(y_test_decoded, y_pred_decoded)
    f1_macro = f1_score(y_test_decoded, y_pred_decoded, average="macro")
    f1_weighted = f1_score(y_test_decoded, y_pred_decoded, average="weighted")
    
    print(f"\n[metrics] Accuracy: {acc:.4f}")
    print(f"[metrics] F1-macro: {f1_macro:.4f}")
    print(f"[metrics] F1-weighted: {f1_weighted:.4f}")
    print(f"\n[report]\n{classification_report(y_test_decoded, y_pred_decoded)}")
    print(f"\n[confusion]\n{confusion_matrix(y_test_decoded, y_pred_decoded)}")
    
    # Salva modelo
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"[save] Modelo salvo em: {model_path}")
    
    # Salva label encoder
    joblib.dump(le, encoder_path)
    print(f"[save] Encoder salvo em: {encoder_path}")
    
    # Metadata
    metadata = {
        "model_type": "LightGBM" if (use_lgbm and HAS_LGBM) else "RandomForest",
        "features": ALL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "boolean_features": BOOLEAN_FEATURES,
        "target_classes": le.classes_.tolist(),
        "target_mapping": {int(i): name for i, name in enumerate(le.classes_)},
        "n_samples_train": len(y_train),
        "n_samples_test": len(y_test),
        "accuracy": float(acc),
        "f1_macro": float(f1_macro),
        "f1_weighted": float(f1_weighted),
        "sklearn_version": joblib.__version__,
        "features_count": len(ALL_FEATURES)
    }
    
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"[save] Metadata salvo em: {metadata_path}")
    
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Treina modelo Junk-ML")
    parser.add_argument("--data", default="../data/dataset.jsonl", help="Dataset JSONL")
    parser.add_argument("--model", default="model.joblib", help="Modelo de saída")
    parser.add_argument("--metadata", default="metadata.json", help="Metadata JSON")
    parser.add_argument("--encoder", default="encoder.joblib", help="Label encoder")
    parser.add_argument("--lgbm", action="store_true", help="Usar LightGBM (se disponível)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Split de teste")
    args = parser.parse_args()
    
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"[ERRO] Dataset não encontrado: {data_path}")
        return 1
    
    model_path = Path(args.model)
    metadata_path = Path(args.metadata)
    encoder_path = Path(args.encoder)
    
    metadata = train_model(
        data_path=data_path,
        model_path=model_path,
        metadata_path=metadata_path,
        encoder_path=encoder_path,
        use_lgbm=args.lgbm,
        test_size=args.test_size
    )
    
    print("\n[train] Concluído com sucesso!")
    return 0


if __name__ == "__main__":
    exit(main())