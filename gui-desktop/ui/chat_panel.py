"""
ChatPanel — janela de conversa do Eco.

Um widget PyQt6 (janela flutuante) que mostra as mensagens do Eco em tempo
real, com streaming progressivo (a resposta aparece frase a frase), e permite
ao usuario digitar e enviar texto para a bridge.

Signals:
    send_message(str)  -> emitido quando o usuario envia um texto
    (conectado ao AgentBridge.send_user_text)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    send_message = pyqtSignal(str)

    def __init__(self, assistant_name: str = "Eco", parent=None):
        super().__init__(parent)

        self._assistant_name = assistant_name
        # Lista de mensagens finalizadas: cada uma e (quem, texto)
        # quem = "user" | "eco"
        self._messages: list[tuple[str, str]] = []
        self._streaming = ""      # texto parcial da resposta atual do Eco
        self._streaming_open = False

        self.setWindowTitle(f"Conversa com {assistant_name}")
        self.resize(420, 520)

        layout = QVBoxLayout(self)

        self._history = QTextEdit()
        self._history.setReadOnly(True)
        self._history.setPlaceholderText(
            "O que o Eco fala vai aparecer aqui, ao vivo."
        )
        layout.addWidget(self._history, stretch=1)

        input_row = QHBoxLayout()
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Digite aqui e aperte Enter...")
        self._entry.returnPressed.connect(self._on_send)
        input_row.addWidget(self._entry, stretch=1)

        self._send_btn = QPushButton("Enviar")
        self._send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self._send_btn)

        layout.addLayout(input_row)

    # ---- entrada do usuario ----

    def _on_send(self):
        text = self._entry.text().strip()
        if not text:
            return
        self.add_user(text)
        self._entry.clear()
        self.send_message.emit(text)

    def add_user(self, text: str):
        self._messages.append(("user", text))
        self._rebuild()

    # ---- streaming da resposta do Eco ----

    def begin_reply(self):
        self._streaming_open = True
        self._streaming = ""

    def append_reply_chunk(self, text: str):
        if not self._streaming_open:
            self.begin_reply()
        self._streaming += text
        self._rebuild()

    def end_reply(self):
        if not self._streaming_open:
            return
        body = self._streaming.strip()
        if body:
            self._messages.append(("eco", body))
        self._streaming_open = False
        self._streaming = ""
        self._rebuild()

    # ---- render ----

    def _rebuild(self):
        self._history.clear()
        for who, text in self._messages:
            self._history.append(self._block(who, text))
        if self._streaming_open:
            body = self._streaming
            self._history.append(
                self._block("eco", body) + ("▌" if body else "")
            )
        # rola para o fim
        sb = self._history.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _block(who: str, text: str) -> str:
        if who == "user":
            color = "#7dd3fc"
            label = "Voce"
        else:
            color = "#67e8f9"
            label = "Eco"
        return (
            f'<div style="color:{color}; font-weight:bold;">{label}:</div>'
            f'<div style="color:#e2e8f0; margin-bottom:8px;">{_esc(text)}</div>'
        )


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
