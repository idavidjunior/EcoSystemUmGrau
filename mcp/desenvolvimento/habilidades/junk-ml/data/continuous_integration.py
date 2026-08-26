#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integração do junk-ml com o pipeline de aprendizado contínuo do EcoSystemUmGrau.

Conecta:
- feedback_collector (junk-ml) -> PAIS FeedbackLearningEngine -> feedback-log.json
- buffer threshold -> run_continuous_learning.py (trigger retreino)
- guardian integration (system_guardian.py) -> auto-retrain schedule
"""
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Paths do ecossistema
ECO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
SCRIPTS_DIR = ECO_ROOT / "scripts"
JUNK_ML_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = JUNK_ML_ROOT / "data"
MODELS_DIR = JUNK_ML_ROOT / "models"
SERVING_DIR = JUNK_ML_ROOT / "serving"

# Pipeline contínuo (claude-code-extra-agents)
CCEA_ROOT = ECO_ROOT / "Projetos" / "claude-code-extra-agents"
CCEA_SCRIPTS = CCEA_ROOT / "scripts"
LEARNING_REPO = CCEA_ROOT / "learning-repository"
FEEDBACK_LOG = LEARNING_REPO / "feedback-log.json"

# PAIS skill
PAIS_LEARNING = ECO_ROOT / "mcp" / "nucleo" / "habilidades" / "pais" / "pais" / "learning.py"

# ─── Integração Feedback ───

def log_ml_feedback(features: Dict[str, Any], predicted_label: int, 
                    corrected_label: int, confidence: float, path: str) -> bool:
    """
    Registra feedback do usuário no pipeline PAIS + feedback-log.json.
    
    Converte correção ML -> FeedbackKind PAIS + loga evento de aprendizado.
    """
    try:
        # 1. Usa PAIS para classificar tipo de feedback
        sys.path.insert(0, str(ECO_ROOT / "mcp" / "nucleo" / "habilidades" / "pais"))
        from pais.learning import FeedbackLearningEngine, FeedbackKind
        
        engine = FeedbackLearningEngine()
        
        # Determina tipo de feedback baseado na correção
        if corrected_label != predicted_label:
            # Usuário corrigiu -> CORRECTED
            kind = FeedbackKind.CORRECTED
        else:
            kind = FeedbackKind.ACCEPTED
        
        # 2. Registra no feedback-log.json (formato learning-repository)
        ensure_learning_dirs()
        
        feedback_log = load_json(FEEDBACK_LOG)
        if not isinstance(feedback_log, list):
            feedback_log = []
        
        # Cria evento de aprendizado ML-specific
        ml_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "junk-ml",
            "type": "model_correction",
            "details": {
                "features_hash": hash(str(sorted(features.items()))) % 1000000,
                "predicted_label": predicted_label,
                "corrected_label": corrected_label,
                "confidence": confidence,
                "file_path": str(path)[:100],
                "pais_kind": kind.value
            },
            "model_info": {
                "model_type": "junk-ml",
                "version": get_model_version()
            }
        }
        
        feedback_log.append(ml_event)
        
        # Mantém últimos 2000 eventos
        if len(feedback_log) > 2000:
            feedback_log = feedback_log[-2000:]
        
        save_json(FEEDBACK_LOG, feedback_log)
        
        # 3. Aplica no PAIS (atualiza preferências do usuário)
        try:
            # PAIS usa store interno - apenas loga interação
            from pais.store import UserStore
            store = UserStore()
            store.log_interaction({
                "kind": "feedback",
                "label": kind.value,
                "source": "junk-ml",
                "details": ml_event["details"]
            })
        except Exception:
            pass  # PAIS store pode não estar disponível
        
        return True
        
    except Exception as e:
        print(f"[ML Feedback] Erro ao registrar: {e}")
        return False


def ensure_learning_dirs():
    """Garante que diretórios do learning-repository existam."""
    LEARNING_REPO.mkdir(parents=True, exist_ok=True)
    (LEARNING_REPO / "agent-profiles").mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    if not path.exists():
        return [] if path.suffix == ".json" else {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


def get_model_version() -> str:
    """Retorna versão do modelo atual."""
    meta_path = MODELS_DIR / "metadata.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8")).get("model_type", "unknown")
        except Exception:
            pass
    return "unknown"


# ─── Trigger Retreino Automático ───

def should_trigger_retrain() -> bool:
    """Verifica se deve disparar retreino baseado no buffer + threshold."""
    import sys
    sys.path.insert(0, str(DATA_DIR))
    from feedback_collector import should_retrain_now
    return should_retrain_now()


def trigger_auto_retrain(reason: str = "buffer_threshold") -> Dict[str, Any]:
    """
    Dispara retreino automático via pipeline contínuo.
    
    Opções:
    1. Roda train.py local (junk-ml)
    2. Dispara run_continuous_learning.py (pipeline completo)
    3. Registra evento para guardian processar
    """
    result = {
        "triggered": False,
        "reason": reason,
        "method": None,
        "success": False,
        "details": ""
    }
    
    try:
        # Método 1: Treino local junk-ml (rápido, só ML)
        train_script = JUNK_ML_ROOT / "models" / "train.py"
        if train_script.exists():
            print(f"[AutoRetrain] Iniciando treino local: {train_script}")
            proc = subprocess.run(
                [sys.executable, str(train_script)],
                cwd=str(JUNK_ML_ROOT / "models"),
                capture_output=True,
                text=True,
                timeout=300
            )
            if proc.returncode == 0:
                result.update({
                    "triggered": True,
                    "method": "local_train",
                    "success": True,
                    "details": "Modelo retreinado localmente (junk-ml/models/train.py)"
                })
                mark_retrain_complete()
                return result
            else:
                result["details"] = f"Falha no treino local: {proc.stderr}"
        
        # Método 2: Pipeline completo (claude-code-extra-agents)
        ccea_script = CCEA_SCRIPTS / "run_continuous_learning.py"
        if ccea_script.exists():
            print(f"[AutoRetrain] Disparando pipeline completo: {ccea_script}")
            proc = subprocess.run(
                [sys.executable, str(ccea_script)],
                cwd=str(CCEA_ROOT),
                capture_output=True,
                text=True,
                timeout=600
            )
            if proc.returncode == 0:
                result.update({
                    "triggered": True,
                    "method": "full_pipeline",
                    "success": True,
                    "details": "Pipeline completo executado (run_continuous_learning.py)"
                })
                mark_retrain_complete()
                return result
            else:
                result["details"] += f" | Pipeline falhou: {proc.stderr}"
        
        # Método 3: Registra para guardian processar
        log_guardian_retrain_request(reason)
        result["details"] += " | Registrado para guardian processar"
        
    except Exception as e:
        result["details"] = f"Erro: {e}"
    
    return result


def mark_retrain_complete():
    """Marca retreino como concluído no feedback_collector."""
    try:
        import sys
        sys.path.insert(0, str(DATA_DIR))
        from feedback_collector import mark_retrain_complete as _mark
        _mark()
    except Exception:
        pass


def log_guardian_retrain_request(reason: str):
    """Registra solicitação de retreino para o system_guardian processar."""
    try:
        guardian_log = ECO_ROOT / "runtime" / "guardian_retrain_requests.jsonl"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "junk-ml",
            "reason": reason,
            "model": "junk-ml",
            "status": "pending"
        }
        with open(guardian_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception:
        pass


# ─── Guardian Integration ───

def guardian_check_retrain() -> bool:
    """
    Função chamada pelo system_guardian.py para verificar se deve retreinar.
    Retorna True se retreino foi disparado.
    """
    if should_trigger_retrain():
        result = trigger_auto_retrain("guardian_check")
        return result.get("success", False)
    return False


# ─── Status & Health ───

def get_integration_status() -> Dict[str, Any]:
    """Retorna status completo da integração."""
    import sys
    sys.path.insert(0, str(DATA_DIR))
    from feedback_collector import get_buffer_status
    
    buffer_stats = get_buffer_status()
    
    # Verifica se learning-repository existe
    learning_repo_exists = LEARNING_REPO.exists()
    feedback_log_exists = FEEDBACK_LOG.exists()
    feedback_log_count = 0
    if feedback_log_exists:
        try:
            feedback_log_count = len(load_json(FEEDBACK_LOG))
        except Exception:
            pass
    
    return {
        "junk_ml": {
            "buffer": buffer_stats,
            "model_version": get_model_version(),
            "model_exists": (MODELS_DIR / "model.joblib").exists(),
            "data_dir": str(DATA_DIR),
            "models_dir": str(MODELS_DIR)
        },
        "continuous_learning": {
            "learning_repo_exists": learning_repo_exists,
            "feedback_log_exists": feedback_log_exists,
            "feedback_log_count": feedback_log_count,
            "pipeline_scripts": {
                "run_continuous_learning": (CCEA_SCRIPTS / "run_continuous_learning.py").exists(),
                "orchestrate_feedback": (CCEA_SCRIPTS / "orchestrate_feedback_loop.py").exists(),
                "adapt_prompts": (CCEA_SCRIPTS / "adapt_agent_prompts.py").exists()
            }
        },
        "pais_integration": {
            "learning_module": PAIS_LEARNING.exists()
        },
        "guardian": {
            "retrain_requests_log": (ECO_ROOT / "runtime" / "guardian_retrain_requests.jsonl").exists()
        }
    }


# ─── API Pública ───

def log_correction(features: Dict[str, Any], predicted: int, corrected: int, 
                   confidence: float, path: str) -> bool:
    """API para serving chamar quando usuário corrige."""
    return log_ml_feedback(features, predicted, corrected, 0.0, "")


def check_and_retrain() -> Dict[str, Any]:
    """Verifica e dispara retreino se necessário."""
    if should_trigger_retrain():
        return trigger_auto_retrain("auto_check")
    return {"triggered": False, "reason": "threshold_not_met"}


def get_status() -> Dict[str, Any]:
    return get_integration_status()


# ─── CLI ───

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            print(json.dumps(get_integration_status(), ensure_ascii=False, indent=2))
        elif sys.argv[1] == "check":
            result = check_and_retrain()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif sys.argv[1] == "retrain":
            result = trigger_auto_retrain("manual")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif sys.argv[1] == "guardian":
            ok = guardian_check_retrain()
            print(f"Retreino disparado: {ok}")