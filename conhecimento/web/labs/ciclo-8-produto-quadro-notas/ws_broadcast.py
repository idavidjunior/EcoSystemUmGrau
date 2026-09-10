"""Ciclo 8 — canal realtime de eventos do Quadro de Notas (bloco F/H).

Broadcast WebSocket dedicado ao produto: cada mutação de nota (criar,
atualizar, arquivar, excluir) dispara um evento JSON para todos os clientes
conectados na rota /ws. Usado pelo server.py (produto) quando a API HTTP
persiste uma mudança no sqlite.

Uso (integrado ao produto):
  ws_broadcast.iniciar(porta)   # thread daemon
  ws_broadcast.emitir(tipo, **dados)
  ws_broadcast.parar()
"""

import asyncio
import json
import threading
from datetime import datetime, timezone

from websockets.asyncio.server import serve

_CLIENTES = set()
_LOOP = None
_PARADA = None
_THREAD = None


def _utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _payload(tipo, **campos):
    corpo = {"tipo": tipo, "ok": True}
    corpo.update(campos)
    return json.dumps(corpo, ensure_ascii=False)


async def _envia_para(tipo, campos):
    if not _CLIENTES:
        return
    corpo = _payload(tipo, **campos)
    for ws in list(_CLIENTES):
        try:
            await ws.send(corpo)
        except Exception:
            _CLIENTES.discard(ws)


async def _handler(websocket):
    rota = websocket.request.path or "/"
    if rota != "/ws":
        try:
            await websocket.close(code=1008, reason="rota invalida")
        except Exception:
            pass
        return
    _CLIENTES.add(websocket)
    await websocket.send(_payload("bem_vindo", rota=rota, hora=_utc_iso()))
    try:
        async for _ in websocket:
            pass
    except Exception:
        pass
    finally:
        _CLIENTES.discard(websocket)


async def _amain(porta):
    global _PARADA
    _PARADA = asyncio.Event()
    async with serve(_handler, "127.0.0.1", porta):
        await _PARADA.wait()


def iniciar(porta=8099):
    """Sobe o servidor de eventos numa thread daemon. Idempotente."""
    global _LOOP, _THREAD
    if _LOOP is not None:
        return _LOOP
    loop = asyncio.new_event_loop()

    def _rodar():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_amain(porta))

    th = threading.Thread(target=_rodar, name="ciclo8-ws", daemon=True)
    th.start()
    _LOOP = loop
    _THREAD = th
    return loop


def emitir(tipo, **dados):
    """Agenda broadcast a todos os clientes conectados (thread-safe)."""
    global _LOOP
    if _LOOP is None:
        return False
    try:
        asyncio.run_coroutine_threadsafe(_envia_para(tipo, dados), _LOOP)
        return True
    except Exception:
        return False


def parar():
    global _LOOP, _THREAD
    if _PARADA is not None:
        _PARADA.set()
    if _THREAD is not None:
        _THREAD.join(timeout=3)
    _LOOP = None
    _THREAD = None