#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feedback Collector — coleta correções do usuário para retreino automático.
Integra-se ao serving: quando usuário corrige, salva (features, label_correto) no buffer.
"""
import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import fcntl
import os

BASE = Path(__file__).resolve().parent.parent
BUFFER_DIR = BASE / "data" / "buffer"
BUFFER_DIR.mkdir(parents=True, exist_ok=True)

BUFFER_FILE = BUFFER_DIR / "feedback_buffer.jsonl"
LOCK_FILE = BUFFER_DIR / "buffer.lock"
META_FILE = BUFFER_DIR / "meta.json"

# Threshold para disparar retreino
RETRAIN_THRESHOLD = 50  # samples novos
MIN_INTERVAL_HOURS = 6  # intervalo mínimo entre retreinos


class FeedbackCollector:
    """Thread-safe feedback collector com lock de arquivo."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def _acquire_lock(self, timeout=10):
        """Lock baseado em arquivo (funciona cross-process)."""
        start = time.time()
        while True:
            try:
                self._lock_fd = open(LOCK_FILE, 'w')
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if time.time() - start > timeout:
                    return False
                time.sleep(0.1)
    
    def _release_lock(self):
        try:
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
            self._lock_fd.close()
        except Exception:
            pass
    
    def add_feedback(self, features: Dict[str, Any], predicted_label: int, 
                     corrected_label: int, confidence: float, path: str) -> bool:
        """
        Adiciona feedback do usuário.
        
        Args:
            features: dict com features extraídas
            predicted_label: label que o modelo previu
            corrected_label: label correto (fornecido pelo usuário)
            confidence: confiança da predição original
            path: caminho do arquivo
        """
        if predicted_label == corrected_label:
            return False  # não há correção
        
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "features": features,
            "predicted_label": predicted_label,
            "corrected_label": corrected_label,
            "confidence": confidence,
            "path": path,
            "source": "user_correction"
        }
        
        with self._lock:
            if not self._acquire_lock():
                return False
            try:
                with open(BUFFER_FILE, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                self._update_meta()
                return True
            finally:
                self._release_lock()
    
    def _update_meta(self):
        """Atualiza metadata do buffer."""
        try:
            if META_FILE.exists():
                meta = json.loads(META_FILE.read_text(encoding='utf-8'))
            else:
                meta = {"total_samples": 0, "last_retrain": None, "created": datetime.utcnow().isoformat() + "Z"}
            
            meta["total_samples"] = self._count_buffer()
            meta["last_update"] = datetime.utcnow().isoformat() + "Z"
            
            tmp = META_FILE.with_suffix('.tmp')
            tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
            tmp.replace(META_FILE)
        except Exception:
            pass
    
    def _count_buffer(self) -> int:
        try:
            return sum(1 for _ in open(BUFFER_FILE, 'r', encoding='utf-8'))
        except Exception:
            return 0
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do buffer."""
        with self._lock:
            count = self._count_buffer()
            meta = {}
            if META_FILE.exists():
                try:
                    meta = json.loads(META_FILE.read_text(encoding='utf-8'))
                except Exception:
                    pass
            return {
                "pending_samples": count,
                "threshold": RETRAIN_THRESHOLD,
                "ready_for_retrain": count >= RETRAIN_THRESHOLD,
                "last_retrain": meta.get("last_retrain"),
                "last_update": meta.get("last_update"),
                "min_interval_hours": MIN_INTERVAL_HOURS
            }
    
    def should_retrain(self) -> bool:
        """Verifica se deve disparar retreino."""
        stats = self.get_buffer_stats()
        if not stats["ready_for_retrain"]:
            return False
        
        # Verifica intervalo mínimo
        if stats["last_retrain"]:
            try:
                last = datetime.fromisoformat(stats["last_retrain"].replace('Z', '+00:00'))
                hours_since = (datetime.utcnow() - last).total_seconds() / 3600
                if hours_since < MIN_INTERVAL_HOURS:
                    return False
            except Exception:
                pass
        return True
    
    def mark_retrain_done(self):
        """Marca retreino como concluído."""
        with self._lock:
            if not self._acquire_lock():
                return
            try:
                meta = {}
                if META_FILE.exists():
                    meta = json.loads(META_FILE.read_text(encoding='utf-8'))
                meta["last_retrain"] = datetime.utcnow().isoformat() + "Z"
                meta["samples_at_retrain"] = self._count_buffer()
                tmp = META_FILE.with_suffix('.tmp')
                tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
                tmp.replace(META_FILE)
            finally:
                self._release_lock()
    
    def export_training_data(self, output_path: Path) -> int:
        """Exporta buffer + dataset original para retreino."""
        records = []
        if BUFFER_FILE.exists():
            with open(BUFFER_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        # Converte para formato de treino (usa label corrigido)
                        rec_copy = rec["features"].copy()
                        rec_copy["label"] = rec["corrected_label"]
                        rec_copy["label_name"] = None  # será preenchido pelo train.py
                        records.append(rec_copy)
        return len(records)


# Instância global
_collector = FeedbackCollector()


def log_correction(features: Dict[str, Any], predicted: int, corrected: int, 
                   confidence: float, path: str) -> bool:
    """API simples para o serving chamar quando usuário corrige."""
    # Salva no buffer local
    local_ok = _collector.add_feedback(features, predicted, corrected, 0.0, "")
    
    # Integra com pipeline contínuo (PAIS + feedback-log.json + trigger)
    try:
        from .continuous_integration import log_ml_feedback
        log_ml_feedback(features, predicted, corrected, confidence, path)
    except Exception:
        pass  # Integração é best-effort
    
    return local_ok


def should_retrain_now() -> bool:
    return _collector.should_retrain()


def mark_retrain_complete():
    _collector.mark_retrain_done()


def get_buffer_status() -> Dict[str, Any]:
    return _collector.get_buffer_stats()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(_collector.get_buffer_stats(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "export":
        out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("training_export.jsonl")
        n = _collector.export_training_data(out)
        print(f"Exportados {n} samples para {out}")