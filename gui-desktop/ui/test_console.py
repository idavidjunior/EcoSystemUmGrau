"""
TestConsole — painel de teste de estados do HUD.

Uma janelinha com botoes para forcar cada estado (STANDBY, LISTENING,
THINKING, SPEAKING) e um botao "Teste automatico" que roda a sequencia
completa, para a gente ver a HUD reagir em tempo real.

Signals:
    request_state(JarvisState) -> emitido quando um botao de estado e clicado
"""

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui_desktop.core.state import JarvisState

_SEQUENCE = [
    (JarvisState.LISTENING, 1200),
    (JarvisState.THINKING, 1200),
    (JarvisState.SPEAKING, 1500),
    (JarvisState.IDLE, 800),
]


class TestConsole(QWidget):
    request_state = pyqtSignal(JarvisState)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Teste do HUD")
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)

        self._status = QLabel("Estado atual: STANDBY")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        grid = QVBoxLayout()
        for state in JarvisState:
            btn = QPushButton(state.label)
            btn.clicked.connect(lambda _=False, s=state: self._manual(s))
            grid.addWidget(btn)
        layout.addLayout(grid)

        self._auto_btn = QPushButton("Teste automatico (sequencia)")
        self._auto_btn.clicked.connect(self._run_auto)
        layout.addWidget(self._auto_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._step_auto)

        self._pending = []

    def set_current_state(self, state: JarvisState):
        self._status.setText(f"Estado atual: {state.label}")

    def _manual(self, state: JarvisState):
        self._pending = []
        self._timer.stop()
        self.request_state.emit(state)

    def _run_auto(self):
        self._pending = list(_SEQUENCE)
        self._step_auto()

    def _step_auto(self):
        if not self._pending:
            self._status.setText("Teste concluido. Fim.")
            return
        state, delay = self._pending.pop(0)
        self.request_state.emit(state)
        self._timer.start(delay)
