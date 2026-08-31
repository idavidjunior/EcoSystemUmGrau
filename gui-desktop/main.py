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

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from gui_desktop.core.agent_bridge import AgentBridge
from gui_desktop.core.state import JarvisState
from gui_desktop.ui.hud_overlay import HUDOverlay

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

    bridge.state_changed.connect(lambda s: hud.set_state(_state_from_str(s)))
    bridge.voice_level.connect(hud.set_voice_level)
    bridge.profile_changed.connect(lambda name, hue: hud.set_palette_hue(hue))
    bridge.connected.connect(lambda: logger.info("Bridge online"))
    bridge.disconnected.connect(lambda: logger.warning("Bridge offline — HUD em STANDBY"))
    bridge.error.connect(lambda m: logger.error(f"Bridge error: {m}"))

    bridge.start()
    hud.show()

    # Fechamento limpo: para o worker quando a janela fechar.
    app.aboutToQuit.connect(bridge.stop)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
