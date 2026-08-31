"""
AgentBridge — cliente WebSocket da bridge do EcoSystemUmGrau.

Conecta em ws://localhost:8765 (a jarvis_bridge.py já existente), escuta as
mensagens definidas no contrato e emite Qt signals para a HUD reagir sem
bloquear o event loop do Qt.

Contrato (recebimento — bridge → GUI):
    {"type": "state", "state": "idle|listening|thinking|speaking"}
    {"type": "user_text", "text": "..."}
    {"type": "reply_chunk", "text": "..."}
    {"type": "tool_call", "key": "...", "description": "..."}
    {"type": "approval_request", "action": "...", "detail": "..."}
    {"type": "error", "message": "..."}
    {"type": "voice_level", "level": 0.0-1.0}
    {"type": "profile_changed", "name": "...", "hue": 182}

Contrato (envio — GUI → bridge):
    {"type": "get_state"}
    {"type": "user_text", "text": "..."}
    {"type": "interrupt"}
    {"type": "approval", "allowed": true|false}
    {"type": "ping"}
"""

import asyncio
import json
import logging
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8765"


class _BridgeWorker(QObject):
    """Worker que roda o asyncio dentro de uma QThread."""

    state_changed = pyqtSignal(str)
    user_text = pyqtSignal(str)
    reply_chunk = pyqtSignal(str)
    tool_call = pyqtSignal(str, str)
    approval_request = pyqtSignal(str, str)
    error = pyqtSignal(str)
    voice_level = pyqtSignal(float)
    profile_changed = pyqtSignal(str, int)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, url: str = WS_URL):
        super().__init__()
        self.url = url
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = None
        self._stop = False

    async def _connect_and_listen(self):
        import websockets

        while not self._stop:
            try:
                async with websockets.connect(self.url, ping_interval=20) as ws:
                    self._ws = ws
                    self.connected.emit()
                    logger.info(f"Bridge connected: {self.url}")
                    try:
                        await ws.send(json.dumps({"type": "get_state"}))
                    except Exception:
                        pass

                    async for raw in ws:
                        if self._stop:
                            break
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        self._dispatch(msg)

            except Exception as e:
                logger.warning(f"Bridge connection error: {e}")
                self.disconnected.emit()
                if not self._stop:
                    await asyncio.sleep(2)
            else:
                self.disconnected.emit()

    def _dispatch(self, msg: dict):
        t = msg.get("type")
        if t == "state":
            self.state_changed.emit(str(msg.get("state", "idle")))
        elif t == "user_text":
            self.user_text.emit(str(msg.get("text", "")))
        elif t == "reply_chunk":
            self.reply_chunk.emit(str(msg.get("text", "")))
        elif t == "tool_call":
            self.tool_call.emit(str(msg.get("key", "")), str(msg.get("description", "")))
        elif t == "approval_request":
            self.approval_request.emit(str(msg.get("action", "")), str(msg.get("detail", "")))
        elif t == "error":
            self.error.emit(str(msg.get("message", "")))
        elif t == "voice_level":
            try:
                self.voice_level.emit(float(msg.get("level", 0.0)))
            except (TypeError, ValueError):
                pass
        elif t == "profile_changed":
            try:
                self.profile_changed.emit(str(msg.get("name", "")), int(msg.get("hue", 182)))
            except (TypeError, ValueError):
                pass

    async def _send(self, payload: dict):
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps(payload))
        except Exception as e:
            logger.warning(f"Bridge send error: {e}")

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        finally:
            self._loop.close()

    def stop(self):
        self._stop = True


class AgentBridge(QObject):
    """Cliente Qt-friendly para a bridge WebSocket."""

    state_changed = pyqtSignal(str)
    user_text = pyqtSignal(str)
    reply_chunk = pyqtSignal(str)
    tool_call = pyqtSignal(str, str)
    approval_request = pyqtSignal(str, str)
    error = pyqtSignal(str)
    voice_level = pyqtSignal(float)
    profile_changed = pyqtSignal(str, int)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, url: str = WS_URL, parent: QObject | None = None):
        super().__init__(parent)
        self._worker = _BridgeWorker(url)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._worker.connected.connect(self.connected)
        self._worker.disconnected.connect(self.disconnected)
        self._worker.state_changed.connect(self.state_changed)
        self._worker.user_text.connect(self.user_text)
        self._worker.reply_chunk.connect(self.reply_chunk)
        self._worker.tool_call.connect(self.tool_call)
        self._worker.approval_request.connect(self.approval_request)
        self._worker.error.connect(self.error)
        self._worker.voice_level.connect(self.voice_level)
        self._worker.profile_changed.connect(self.profile_changed)

        self._thread.started.connect(self._worker.run)

    def start(self):
        self._thread.start()

    def stop(self):
        self._worker.stop()
        self._thread.quit()
        self._thread.wait(3000)

    def send_user_text(self, text: str):
        self._worker._send({"type": "user_text", "text": text})

    def send_interrupt(self):
        self._worker._send({"type": "interrupt"})

    def send_approval(self, allowed: bool):
        self._worker._send({"type": "approval", "allowed": allowed})

    def send_ping(self):
        self._worker._send({"type": "ping"})
