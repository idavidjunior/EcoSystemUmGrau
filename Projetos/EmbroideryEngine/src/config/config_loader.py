"""
Config Loader - Utility for loading JSON configuration files.

Loads fabric profiles, thread palettes, and machine limits from JSON files.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Loads and caches configuration from JSON files."""

    _instance = None
    _cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.config_dir = self._find_config_dir()
            self._initialized = True

    def _find_config_dir(self) -> Path:
        """Find the config directory."""
        # Try multiple locations
        candidates = [
            Path(__file__).parent.parent.parent / "config",  # Projetos/EmbroideryEngine/config
            Path(__file__).parent.parent / "config",  # src/config (wrong, but fallback)
            Path("Projetos/EmbroideryEngine/config"),
            Path("config"),
            Path.cwd() / "config"
        ]
        for c in candidates:
            if c.exists():
                return c
        # Default to project config
        return Path("Projetos/EmbroideryEngine/config")

    def load(self, name: str) -> Dict[str, Any]:
        """Load a configuration file by name (without .json extension)."""
        if name in self._cache:
            return self._cache[name]

        file_path = self.config_dir / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._cache[name] = data
        return data

    def get_fabric(self, fabric_key: str) -> Dict[str, Any]:
        """Get fabric profile by key."""
        fabrics = self.load("fabrics")
        return fabrics.get("fabrics", {}).get(fabric_key, fabrics.get("fabrics", {}).get("custom", {}))

    def get_machine(self, machine_key: str) -> Dict[str, Any]:
        """Get machine profile by key."""
        machines = self.load("machine_limits")
        return machines.get("machines", {}).get(machine_key, machines.get("machines", {}).get("generic", {}))

    def get_thread_palette(self, palette_key: str) -> Dict[str, Any]:
        """Get thread palette by key."""
        threads = self.load("threads")
        return threads.get("palettes", {}).get(palette_key, threads.get("palettes", {}).get("generic", {}))

    def get_all_fabrics(self) -> Dict[str, Any]:
        """Get all fabric profiles."""
        return self.load("fabrics").get("fabrics", {})

    def get_all_machines(self) -> Dict[str, Any]:
        """Get all machine profiles."""
        return self.load("machine_limits").get("machines", {})

    def get_all_palettes(self) -> Dict[str, Any]:
        """Get all thread palettes."""
        return self.load("threads").get("palettes", {})

    def clear_cache(self):
        """Clear the configuration cache."""
        self._cache.clear()


# Convenience functions
_config_loader = ConfigLoader()


def load_config(name: str) -> Dict[str, Any]:
    """Load a configuration file."""
    return _config_loader.load(name)


def get_fabric_profile(fabric_key: str) -> Dict[str, Any]:
    """Get fabric profile."""
    return _config_loader.get_fabric(fabric_key)


def get_machine_profile(machine_key: str) -> Dict[str, Any]:
    """Get machine profile."""
    return _config_loader.get_machine(machine_key)


def get_thread_palette(palette_key: str) -> Dict[str, Any]:
    """Get thread palette."""
    return _config_loader.get_thread_palette(palette_key)


def get_default_machine() -> Dict[str, Any]:
    """Get default machine profile."""
    machines = load_config("machine_limits")
    default_key = machines.get("defaults", {}).get("default_machine", "generic")
    return get_machine_profile(default_key)


def get_default_palette() -> Dict[str, Any]:
    """Get default thread palette."""
    threads = load_config("threads")
    default_key = threads.get("defaults", {}).get("default_palette", "generic")
    return get_thread_palette(default_key)


if __name__ == "__main__":
    # Test loading
    loader = ConfigLoader()
    print("Config dir:", loader.config_dir)

    fabrics = loader.get_all_fabrics()
    print(f"Fabrics: {list(fabrics.keys())}")

    machines = loader.get_all_machines()
    print(f"Machines: {list(machines.keys())}")

    palettes = loader.get_all_palettes()
    print(f"Palettes: {list(palettes.keys())}")

    # Test specific
    cotton = loader.get_fabric("cotton")
    print(f"Cotton pull: {cotton.get('pull_compensation_mm')}")

    generic_machine = loader.get_machine("generic")
    print(f"Generic max stitches: {generic_machine.get('max_stitches')}")

    madeira = loader.get_thread_palette("madeira")
    print(f"Madeira threads: {len(madeira.get('threads', []))}")