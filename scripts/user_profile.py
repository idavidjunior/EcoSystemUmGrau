"""user_profile.py — Perfil do usuário que aprende e adapta o comportamento do ecossistema.

Armazena preferências aprendidas implicitamente a partir das interações:
- Estilo de resposta (verbooso/direto, markdown/texto, formal/casual)
- Comandos preferidos, aliases
- Formatação (markdown/sem markdown, tabelas/sim/não)
- Nível de detalhe (resumo/detalhado)
- Tom (técnico/simples)
- Idioma preferido
- Horários de uso, frequência de comandos

Persiste em runtime/user_profile.json e sincroniza com memory_engine.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "runtime" / "user_profile.json"
INTERACTIONS_LOG = ROOT / "runtime" / "user_interactions.jsonl"


class UserProfile:
    """Perfil adaptativo do usuário."""

    DEFAULTS = {
        "style": {
            "verbosity": "direct",          # direct | balanced | verbose
            "format": "plain",              # plain | markdown | minimal
            "tables": False,                # usar tabelas
            "lists": "dash",                # dash | numbered | none
            "code_blocks": False,           # usar blocos de código
        },
        "tone": {
            "technical_level": "intermediate",  # basic | intermediate | advanced
            "formality": "casual",          # formal | casual | friendly
            "language": "pt-BR",
        },
        "preferences": {
            "auto_summarize": True,
            "show_reasoning": False,
            "confirm_destructive": True,
            "short_commands": True,
        },
        "learned_patterns": {
            "frequent_commands": {},        # cmd -> count
            "command_aliases": {},          # alias -> comando real
            "preferred_formats": {},        # contexto -> formato
            "rejected_formats": [],         # formatos que o usuário corrigiu
            "common_topics": {},            # tópico -> frequência
        },
        "stats": {
            "total_interactions": 0,
            "corrections_received": 0,
            "first_seen": None,
            "last_updated": None,
        }
    }

    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        if PROFILE_PATH.exists():
            try:
                with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge com defaults para novos campos
                return self._deep_merge(self.DEFAULTS, data)
            except Exception:
                pass
        data = self.DEFAULTS.copy()
        data["stats"]["first_seen"] = datetime.now().isoformat()
        return data

    def _deep_merge(self, default: Dict, loaded: Dict) -> Dict:
        """Merge recursivo mantendo defaults para chaves ausentes."""
        result = default.copy()
        for k, v in loaded.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def save(self):
        self.data["stats"]["last_updated"] = datetime.now().isoformat()
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PROFILE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(PROFILE_PATH)

    # ---------- Acesso a preferências ----------

    def get_style(self, key: str, default=None):
        return self.data["style"].get(key, default)

    def get_tone(self, key: str, default=None):
        return self.data["tone"].get(key, default)

    def get_pref(self, key: str, default=None):
        return self.data["preferences"].get(key, default)

    def set_style(self, key: str, value):
        self.data["style"][key] = value
        self.save()

    def set_tone(self, key: str, value):
        self.data["tone"][key] = value
        self.save()

    def set_pref(self, key: str, value):
        self.data["preferences"][key] = value
        self.save()

    # ---------- Aprendizado implícito ----------

    def record_interaction(self, user_text: str, agent_response: str, metadata: Dict = None):
        """Registra uma interação completa para aprendizado."""
        self.data["stats"]["total_interactions"] += 1
        self.data["stats"]["last_updated"] = datetime.now().isoformat()

        # Extrai padrões do texto do usuário
        self._extract_command_patterns(user_text)
        self._extract_topic_interest(user_text)
        self._detect_corrections(user_text, agent_response)

        # Log bruto para análise posterior
        self._log_interaction(user_text, agent_response, metadata)

        self.save()

    def _extract_command_patterns(self, text: str):
        """Detecta comandos e aliases usados."""
        words = text.lower().split()
        for w in words:
            if w.startswith("/") or w.startswith("@"):
                self.data["learned_patterns"]["frequent_commands"][w] = \
                    self.data["learned_patterns"]["frequent_commands"].get(w, 0) + 1

    def _extract_topic_interest(self, text: str):
        """Tópicos frequentes (palavras-chave técnicas)."""
        tech_keywords = [
            "android", "tts", "jarvis", "narrador", "widget", "bridge",
            "tts", "stt", "voice", "audio", "ecosystem", "sync",
            "build", "apk", "gradle", "kotlin", "flutter", "dart",
            "python", "javascript", "typescript", "react", "node",
            "docker", "kubernetes", "ci", "cd", "git", "github",
        ]
        text_lower = text.lower()
        for kw in tech_keywords:
            if kw in text_lower:
                self.data["learned_patterns"]["common_topics"][kw] = \
                    self.data["learned_patterns"]["common_topics"].get(kw, 0) + 1

    def _detect_corrections(self, user_text: str, agent_response: str):
        """Detecta quando usuário corrige o agente (padrões de correção)."""
        correction_patterns = [
            "não use", "não quero", "sem ", "não use markdown",
            "sem markdown", "sem formatação", "direto", "simples",
            "não fale", "pare de", "não diga", "não pronuncie",
            "errado", "incorreto", "não é assim", "do jeito errado",
        ]
        text_lower = user_text.lower()
        for pattern in correction_patterns:
            if pattern in text_lower:
                self.data["stats"]["corrections_received"] += 1
                # Tenta inferir o que foi corrigido
                if "markdown" in text_lower or "formatação" in text_lower:
                    self.data["learned_patterns"]["rejected_formats"].append("markdown")
                if "trecho de código" in agent_response.lower() or "arquivo" in agent_response.lower():
                    self.data["learned_patterns"]["rejected_formats"].append("code_announcement")
                break

    def _log_interaction(self, user_text: str, agent_response: str, metadata: Dict):
        """Log bruto em JSONL para análise posterior."""
        try:
            INTERACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": datetime.now().isoformat(),
                "user": user_text[:500],
                "agent_len": len(agent_response),
                "meta": metadata or {},
            }
            with open(INTERACTIONS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ---------- Aplicação de preferências ----------

    def get_response_config(self) -> Dict:
        """Retorna configuração derivada para o agente usar na resposta."""
        return {
            "use_markdown": self.get_style("format") == "markdown",
            "use_tables": self.get_style("tables"),
            "use_code_blocks": self.get_style("code_blocks"),
            "list_style": self.get_style("lists"),
            "verbosity": self.get_style("verbosity"),
            "technical_level": self.get_tone("technical_level"),
            "formality": self.get_tone("formality"),
            "language": self.get_tone("language"),
            "auto_summarize": self.get_pref("auto_summarize"),
            "show_reasoning": self.get_pref("show_reasoning"),
        }

    def apply_correction(self, correction_type: str, detail: str = ""):
        """Aplica correção explícita do usuário."""
        if correction_type == "no_markdown":
            self.set_style("format", "plain")
            self.set_style("code_blocks", False)
            self.set_style("tables", False)
            self.data["learned_patterns"]["rejected_formats"].append("markdown")
        elif correction_type == "no_code_announcement":
            self.data["learned_patterns"]["rejected_formats"].append("code_announcement")
        elif correction_type == "direct_only":
            self.set_style("verbosity", "direct")
            self.set_style("format", "plain")
        elif correction_type == "technical":
            self.set_tone("technical_level", "advanced")
        elif correction_type == "simple":
            self.set_tone("technical_level", "basic")
        elif correction_type == "formal":
            self.set_tone("formality", "formal")
        elif correction_type == "casual":
            self.set_tone("formality", "casual")
        self.save()

    def get_stats(self) -> Dict:
        return {
            "total_interactions": self.data["stats"]["total_interactions"],
            "corrections": self.data["stats"]["corrections_received"],
            "top_commands": sorted(
                self.data["learned_patterns"]["frequent_commands"].items(),
                key=lambda x: x[1], reverse=True
            )[:10],
            "top_topics": sorted(
                self.data["learned_patterns"]["common_topics"].items(),
                key=lambda x: x[1], reverse=True
            )[:10],
            "rejected_formats": list(set(self.data["learned_patterns"]["rejected_formats"])),
        }


# Instância global
_profile: Optional[UserProfile] = None


def get_profile() -> UserProfile:
    global _profile
    if _profile is None:
        _profile = UserProfile()
    return _profile


def reset_profile():
    global _profile
    _profile = None
    if PROFILE_PATH.exists():
        PROFILE_PATH.unlink()
    if INTERACTIONS_LOG.exists():
        INTERACTIONS_LOG.unlink()


if __name__ == "__main__":
    import sys
    p = get_profile()
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(p.get_stats(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "config":
        print(json.dumps(p.get_response_config(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "correct":
        p.apply_correction(sys.argv[2])
        print(f"Correção aplicada: {sys.argv[2]}")
    else:
        print(json.dumps(p.data, ensure_ascii=False, indent=2))