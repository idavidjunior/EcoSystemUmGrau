"""Storage do PAIS — persistência atômica JSON com separação de modelos.

USER MODEL e EPISTEMIC MODEL vivem em arquivos separados. Fatos sobre o
usuário nunca são misturados com conhecimento factual.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
STORAGE = BASE / "storage"
USER_MODEL_FILE = STORAGE / "user_model.json"
EPISTEMIC_MODEL_FILE = STORAGE / "epistemic_model.json"
LOG_FILE = STORAGE / "interactions.log"

_lock = threading.Lock()

USER_MODEL_DEFAULT = {
    "version": 1,
    "facts": {},            # key -> Trait.to_dict()
    "preferences": {},
    "patterns": {},
    "projects": {},
    "goals": {},
    "habits": {},
    "inferences": {},
    "predictions": {},      # key -> list[Prediction.to_dict()]
    "linguistic_profile": {},
    "reasoning_profile": {},
    "response_preferences": {},
    "last_interaction": "",
}

EPISTEMIC_MODEL_DEFAULT = {
    "version": 1,
    "claims": {},           # key -> Claim.to_dict()
    "sources": {},
    "verifications": [],
    "contradictions": [],
    "uncertainties": [],
    "research_log": [],
    "metrics": {},
}


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _read(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(default)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, OSError):
        return dict(default)


class Store:
    """Dois modelos independentes + log de interações."""

    def __init__(self, user_file: Path = USER_MODEL_FILE,
                 epistemic_file: Path = EPISTEMIC_MODEL_FILE):
        self.user_file = Path(user_file)
        self.epistemic_file = Path(epistemic_file)
        self._user = _read(self.user_file, USER_MODEL_DEFAULT)
        self._epistemic = _read(self.epistemic_file, EPISTEMIC_MODEL_DEFAULT)

    def user(self) -> dict:
        return self._user

    def epistemic(self) -> dict:
        return self._epistemic

    def save_user(self) -> None:
        with _lock:
            _atomic_write(self.user_file, self._user)

    def save_epistemic(self) -> None:
        with _lock:
            _atomic_write(self.epistemic_file, self._epistemic)

    def save_all(self) -> None:
        self.save_user()
        self.save_epistemic()

    def log_interaction(self, entry: dict) -> None:
        with _lock:
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError:
                pass
