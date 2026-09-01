"""Smoke test — simula streaming de resposta e envia texto."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as app_main
from PyQt6.QtCore import QTimer

app = app_main.QApplication(sys.argv)

chat = app_main.ChatPanel(assistant_name="Eco")
sent = []
chat.send_message.connect(sent.append)

# simula streaming de resposta
def step():
    chat.begin_reply()
    chat.append_reply_chunk("Oi! ")
    chat.append_reply_chunk("Tudo ")
    chat.append_reply_chunk("bem?")
    chat.end_reply()
    chat.add_user("ola")
    check()

def check():
    plain = chat._history.toPlainText()
    ocorrencias = plain.count("Eco:")
    assert ocorrencias == 1, f"Streaming duplicou bloco Eco: {ocorrencias}x\n{plain!r}"
    assert "Oi! Tudo bem?" in plain, f"Resposta nao montou: {plain!r}"
    assert "Voce:" in plain and "ola" in plain, f"Msg usuario nao apareceu: {plain!r}"
    # simula envio via entry
    chat._entry.setText("teste")
    chat._on_send()
    assert sent == ["teste"], f"send_message nao emitiu: {sent!r}"
    print("OK - chat monta streaming sem duplicar, mostra usuario, envia")
    sys.exit(0)

QTimer.singleShot(100, step)
app.exec()
