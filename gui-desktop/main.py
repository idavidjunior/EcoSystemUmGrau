"""
GUI Desktop do Jarvis — entry point.

Abre a janela Arc Reactor (HUDOverlay), conecta na bridge WebSocket
(AgentBridge) e mapeia mensagens para a HUD via Qt signals.

Smoke test: roda mesmo sem a bridge online (HUD fica em STANDBY e reconecta
a cada 2s quando o worker detecta queda).
"""

import logging
import sys
from pathlib import Path

# Pacote se chama gui-desktop (kebab-case), mas Python precisa de identificador
# valido para import. Adicionamos a pasta do projeto ao sys.path e usamos
# importlib para carregar modulos com nome canonico "gui_desktop.*".

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib.util as _ilu
import types as _types

def _load(name: str, file_path: str) -> _types.ModuleType:
    spec = _ilu.spec_from_file_location(name, file_path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_pkg_name = "gui_desktop"
_pkg_root = Path(__file__).resolve().parent
sys.modules.setdefault(_pkg_name, _types.ModuleType(_pkg_name))
sys.modules[_pkg_name].__path__ = [str(_pkg_root)]

_load(f"{_pkg_name}.core", str(_pkg_root / "core" / "__init__.py"))
_state = _load(f"{_pkg_name}.core.state", str(_pkg_root / "core" / "state.py"))
_streaming = _load(f"{_pkg_name}.core.streaming", str(_pkg_root / "core" / "streaming.py"))
_agent_bridge = _load(f"{_pkg_name}.core.agent_bridge", str(_pkg_root / "core" / "agent_bridge.py"))
_load(f"{_pkg_name}.ui", str(_pkg_root / "ui" / "__init__.py"))
_hud = _load(f"{_pkg_name}.ui.hud_overlay", str(_pkg_root / "ui" / "hud_overlay.py"))
_chat_panel = _load(f"{_pkg_name}.ui.chat_panel", str(_pkg_root / "ui" / "chat_panel.py"))
_test_console = _load(f"{_pkg_name}.ui.test_console", str(_pkg_root / "ui" / "test_console.py"))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

AgentBridge = _agent_bridge.AgentBridge
JarvisState = _state.JarvisState
HUDOverlay = _hud.HUDOverlay
ChatPanel = _chat_panel.ChatPanel
TestConsole = _test_console.TestConsole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gui-desktop")


def _state_from_str(name: str) -> JarvisState:
    name = (name or "").strip().lower()
    return {
        "idle": JarvisState.IDLE,
        "listening": JarvisState.LISTENING,
        "thinking": JarvisState.THINKING,
        "speaking": JarvisState.SPEAKING,
    }.get(name, JarvisState.IDLE)


def main() -> int:
    app = QApplication(sys.argv)

    hud = HUDOverlay()
    bridge = AgentBridge(parent=hud)

    chat = ChatPanel(assistant_name="Eco")
    console = TestConsole()

    chat.send_message.connect(bridge.send_user_text)
    console.request_state.connect(hud.set_state)

    def _on_state(s: str):
        state = _state_from_str(s)
        hud.set_state(state)
        console.set_current_state(state)
        if state == JarvisState.SPEAKING:
            chat.end_reply()

    bridge.state_changed.connect(_on_state)
    bridge.voice_level.connect(hud.set_voice_level)
    bridge.profile_changed.connect(lambda name, hue: hud.set_palette_hue(hue))
    bridge.connected.connect(lambda: logger.info("Bridge online"))
    bridge.connected.connect(lambda: chat.append_reply_chunk("  [online]"))
    bridge.disconnected.connect(
        lambda: logger.warning("Bridge offline — HUD em STANDBY")
    )
    bridge.error.connect(lambda m: logger.error(f"Bridge error: {m}"))

    def _on_user_text(text: str):
        chat.begin_reply()

    def _on_reply_chunk(text: str):
        chat.append_reply_chunk(text)
        # Estado SPEAKING assim que comeca a responder
        hud.set_state(JarvisState.SPEAKING)
        console.set_current_state(JarvisState.SPEAKING)

    bridge.user_text.connect(_on_user_text)
    bridge.reply_chunk.connect(_on_reply_chunk)

    bridge.start()
    hud.show()

    chat.show()
    chat.move(30, 30)
    console.show()
    console.move(470, 30)

    # Fechamento limpo: para o worker quando a janela fechar.
    app.aboutToQuit.connect(bridge.stop)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
