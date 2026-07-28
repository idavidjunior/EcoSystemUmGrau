import json
import os
import shutil
import tempfile
import time
from datetime import datetime

CHECKPOINT_DIR = None
CHECKPOINT_BASE_DIR = None
MAX_CHECKPOINTS = 50


def atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def atomic_read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_checkpoint_dir(base_dir):
    global CHECKPOINT_DIR, CHECKPOINT_BASE_DIR
    CHECKPOINT_BASE_DIR = base_dir
    CHECKPOINT_DIR = os.path.join(base_dir, "checkpoints")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def save_checkpoint(state, plan, progress, context, label="auto"):
    if CHECKPOINT_DIR is None:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cp_id = f"{timestamp}_{label}"
    cp_dir = os.path.join(CHECKPOINT_DIR, cp_id)
    os.makedirs(cp_dir, exist_ok=True)

    data = {
        "id": cp_id,
        "timestamp": timestamp,
        "label": label,
        "state": state.serialize() if hasattr(state, 'serialize') else state,
        "plan": plan,
        "progress": progress,
        "context": context,
    }
    atomic_write_json(os.path.join(cp_dir, "checkpoint.json"), data)

    _cleanup_old()
    return cp_id

def load_checkpoint(cp_id=None):
    if CHECKPOINT_DIR is None:
        return None
    if cp_id is None:
        cp_id = get_latest_checkpoint()
        if cp_id is None:
            return None
    cp_dir = os.path.join(CHECKPOINT_DIR, cp_id)
    cp_file = os.path.join(cp_dir, "checkpoint.json")
    return atomic_read_json(cp_file)

def get_latest_checkpoint():
    if CHECKPOINT_DIR is None or not os.path.isdir(CHECKPOINT_DIR):
        return None
    dirs = [d for d in os.listdir(CHECKPOINT_DIR)
            if os.path.isdir(os.path.join(CHECKPOINT_DIR, d))]
    if not dirs:
        return None
    dirs.sort(reverse=True)
    return dirs[0]

def list_checkpoints():
    if CHECKPOINT_DIR is None or not os.path.isdir(CHECKPOINT_DIR):
        return []
    dirs = [d for d in os.listdir(CHECKPOINT_DIR)
            if os.path.isdir(os.path.join(CHECKPOINT_DIR, d))]
    dirs.sort(reverse=True)
    result = []
    for d in dirs:
        cp_file = os.path.join(CHECKPOINT_DIR, d, "checkpoint.json")
        if os.path.exists(cp_file):
            with open(cp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                result.append({"id": d, "timestamp": data.get("timestamp"), "label": data.get("label")})
    return result

def _cleanup_old():
    if CHECKPOINT_DIR is None or not os.path.isdir(CHECKPOINT_DIR):
        return
    dirs = sorted([d for d in os.listdir(CHECKPOINT_DIR)
                   if os.path.isdir(os.path.join(CHECKPOINT_DIR, d))],
                  reverse=True)
    for d in dirs[MAX_CHECKPOINTS:]:
        shutil.rmtree(os.path.join(CHECKPOINT_DIR, d), ignore_errors=True)
