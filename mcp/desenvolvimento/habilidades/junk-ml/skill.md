---
name: junk-ml
description: ML para categorização de arquivos junk (JunkScanner). Dataset generation, treino leve (sklearn/lightgbm), serving via skill. Trigger: "junk ml", "categorizar arquivo", "treino junk", "ml junk".
---

# junk-ml — ML para Categorização de Junk (JunkScanner)

## Objetivo
Substituir/auxiliar classificador baseado em regras (ScanEngine.java) por modelo ML leve (CPU-only, sklearn/lightgbm) para categorizar arquivos "suspeitos" sem regra explícita.

## Estrutura
```
junk-ml/
├── data/
│   ├── generate_dataset.py      # Extrai features + labels (ground-truth = regras)
│   ├── dataset.jsonl            # Dataset gerado (features + label)
│   └── schema.json              # Schema das features
├── models/
│   ├── train.py                 # Treino (sklearn/lightgbm)
│   ├── model.joblib             # Modelo treinado
│   ├── metadata.json            # Métricas, features, versão
│   └── encoder.joblib           # Label encoder
├── serving/
│   ├── predict.py               # Carrega modelo + prediz
│   └── skill.py                 # Integração no ecossistema (dialogo.py)
└── skill.md                     # Este arquivo
```

## Pipeline

### 1. Dataset Generation
```bash
python data/generate_dataset.py --root /storage/emulated/0 --output data/dataset.jsonl --balance --max-per-class 2000
```
- Usa classificador de regras (ScanEngine) como ground-truth
- Features: path, size, ext, parent dirs, name patterns, system flags
- 7 classes: cache, temp, apk, log, empty_dir, large_file, download
- Output: JSONL (uma linha por sample)

### 2. Training
```bash
python models/train.py --data data/dataset.jsonl --model models/model.joblib --algo lightgbm
```
- Split 80/20 stratificado
- Métricas: accuracy, f1-macro, confusion matrix
- Salva model.joblib + metadata.json + encoder.joblib

### 3. Serving / Skill
```python
# Em dialogo.py ou jarvis_bridge
from junk_ml.serving.predict import categorize_file
label = categorize_file("/sdcard/Download/app.apk")  # -> "apk"
```

## Features (23)
| Feature | Tipo | Descrição |
|---------|------|-----------|
| size_mb | float | Tamanho em MB |
| depth | int | Profundidade no caminho |
| ext | str | Extensão |
| has_apk_ext | bool | .apk/.apks |
| has_log_ext | bool | .log/.crash |
| has_temp_ext | bool | .tmp/.bak |
| is_media_ext | bool | media ext |
| name_has_cache | bool | "cache"/"trash"/"lixo" |
| name_has_temp | bool | "temp"/"tmp" |
| name_has_trash | bool | "trash"/"lixo" |
| name_is_thumbnails | bool | ".thumbnails" |
| name_is_temp_dir | bool | parent em {temp,tmp} |
| is_hidden | bool | name.startswith(".") |
| is_system_dir | bool | path em /android/data, etc |
| is_dir | bool | é diretório |
| parent_name | str | pai direto |
| grandparent_name | str | avô |

## Target
- CPU-only (sem GPU)
- Modelo < 5MB (joblib comprimido)
- Inferência < 10ms por arquivo
- Acurácia alvo > 95% (vs regras)

## Integração
- `dialogo.py` → importa `junk_ml.serving.predict.categorize_file`
- Usa cache em memória (LRU) para paths repetidos
- Fallback para regras se modelo falhar

## Métricas de Sucesso
- F1-macro > 0.93
- Latência p99 < 15ms
- Modelo < 5MB
- Zero dependências GPU