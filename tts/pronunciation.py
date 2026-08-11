"""PronunciationEngine — aplica substituições de pronúncia personalizadas.

Carrega o pronuncias.json e aplica as substituições de texto puro
(campo "fala") no texto destinado ao TTS.
"""
import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import PRON_PATH


class PronunciationEngine:
    """Motor de pronúncia autoevolutivo.

    Uso:
        engine = PronunciationEngine()
        texto, alterado = engine.apply(texto)
    """

    def __init__(self, pron_path: Optional[Path] = None):
        self._pron_path = pron_path or PRON_PATH
        self._cache: Optional[Dict] = None
        self._cache_mtime: float = 0

    def _load_pronunciations(self) -> Dict:
        """Carrega pronuncias.json com cache por mtime."""
        try:
            if not self._pron_path.exists():
                return {}
            mtime = self._pron_path.stat().st_mtime
            if mtime != self._cache_mtime or self._cache is None:
                with open(self._pron_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                self._cache_mtime = mtime
            return self._cache or {}
        except Exception:
            return {}

    def apply(self, text: str) -> Tuple[str, bool]:
        """Aplica substituições de pronúncia no texto.

        Args:
            text: Texto normalizado para receber substituições.

        Returns:
            Tupla (texto_modificado, alterado).
        """
        pronunciations = self._load_pronunciations()
        if not pronunciations:
            return text, False

        # Ordena por comprimento (mais longo primeiro) para evitar
        # substituições parciais
        palavras = sorted(pronunciations.keys(), key=len, reverse=True)

        def _substituir(m):
            palavra = m.group(0)
            key = palavra.lower()
            if key in pronunciations and "fala" in pronunciations[key]:
                return pronunciations[key]["fala"]
            return palavra

        # Substitui apenas palavras inteiras
        texto_modificado, n = re.subn(
            r'\b([^\W\d_]+)\b',
            _substituir,
            text
        )

        return texto_modificado, n > 0

    def add_pronunciation(self, palavra: str, fala: str) -> bool:
        """Adiciona uma pronúncia ao dicionário.

        Args:
            palavra: Palavra original (ex.: "GitHub").
            fala: Como deve ser falada (ex.: "Guitirrãbi").

        Returns:
            True se salvo com sucesso.
        """
        path = self._pron_path
        for _tentativa in range(3):
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding='utf-8'))
                else:
                    data = {}
                if not isinstance(data, dict):
                    data = {}
                entry = data.get(palavra)
                if not isinstance(entry, dict):
                    entry = {}
                entry["fala"] = fala
                data[palavra] = entry
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                # Invalida cache
                self._cache = None
                return True
            except Exception:
                import time
                time.sleep(0.2)
        return False

    def get_all(self) -> Dict:
        """Retorna todas as pronúncias registradas."""
        return self._load_pronunciations()

    def has_pronunciation(self, palavra: str) -> bool:
        """Verifica se uma palavra tem pronúncia registrada."""
        pron = self._load_pronunciations()
        key = palavra.lower()
        return key in pron and "fala" in pron[key]
