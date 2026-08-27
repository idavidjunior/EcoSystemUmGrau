"""Cache — evita refazer pesquisas idênticas dentro do TTL.

Cache por hash SHA256 do tema normalizado. TTL padrão: 24h.
Armazenado em JSON no diretório do vault.
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

log = logging.getLogger("research.cache")

DEFAULT_TTL = 86400  # 24h
CACHE_FILENAME = "research_cache.json"


class ResearchCache:
    """Cache de pesquisas com TTL."""

    def __init__(self, vault_path: str, ttl: int = DEFAULT_TTL):
        self.cache_path = os.path.join(vault_path, CACHE_FILENAME)
        self.ttl = ttl
        self._data: Dict[str, Any] = self._load()

    def get(self, theme: str) -> Optional[Dict[str, Any]]:
        """Busca resultado em cache para o tema.

        Returns:
            Dict com dados do relatório ou None se não houver cache válido
        """
        key = self._key(theme)
        entry = self._data.get(key)

        if not entry:
            return None

        # Verifica TTL
        age = time.time() - entry.get("timestamp", 0)
        if age > self.ttl:
            log.info("Cache: expirado para '%s' (%.0fh)", theme[:30], age / 3600)
            del self._data[key]
            self._save()
            return None

        log.info("Cache: hit para '%s' (%.0fh atrás)", theme[:30], age / 3600)
        return entry.get("report")

    def set(self, theme: str, report: Dict[str, Any]):
        """Salva resultado no cache."""
        key = self._key(theme)
        self._data[key] = {
            "theme": theme,
            "timestamp": time.time(),
            "report": report,
        }
        self._save()
        log.info("Cache: salvo para '%s'", theme[:30])

    def invalidate(self, theme: str):
        """Remove entrada do cache."""
        key = self._key(theme)
        if key in self._data:
            del self._data[key]
            self._save()

    def clear_expired(self):
        """Remove todas as entradas expiradas."""
        now = time.time()
        expired = [
            k for k, v in self._data.items()
            if now - v.get("timestamp", 0) > self.ttl
        ]
        for k in expired:
            del self._data[k]
        if expired:
            self._save()
            log.info("Cache: %d entradas expiradas removidas", len(expired))

    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        now = time.time()
        active = sum(1 for v in self._data.values() if now - v.get("timestamp", 0) <= self.ttl)
        return {
            "total": len(self._data),
            "active": active,
            "expired": len(self._data) - active,
        }

    def _key(self, theme: str) -> str:
        """Gera chave hash do tema normalizado."""
        normalized = theme.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def _load(self) -> Dict[str, Any]:
        """Carrega cache do disco."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                log.warning("Cache: arquivo corrompido, criando novo")
        return {}

    def _save(self):
        """Salva cache no disco."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            log.warning("Cache: falha ao salvar (%s)", e)
