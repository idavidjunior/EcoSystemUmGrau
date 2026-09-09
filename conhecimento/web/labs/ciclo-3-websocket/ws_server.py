"""Ciclo 3 - Realtime WebSocket (bloco F/H).

Servidor WebSocket com websockets (ASGI-like asyncio server):
  /echo       - eco de mensagens JSON (protocolo {tipo, ...})
  /broadcast  - repassa cada mensagem a todos os clientes conectados na rota
  /estado     - heartbeat (ping/pong) + snapshot do runtime persistente (state.json)

Uso:
  python conhecimento/web/labs/ciclo-3-websocket/ws_server.py [porta]
"""

import asyncio
import json
import sys
from datetime import datetime, timezone

from websockets.asyncio.server import serve

SUDOKU_ROTAS = {"/echo", "/broadcast", "/estado"}
ESTADO_PATH = None


def _utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_ok(tipo, **campos):
    resposta = {"tipo": tipo, "ok": True}
    resposta.update(campos)
    return json.dumps(resposta, ensure_ascii=False)


def _json_erro(motivo):
    return _json_ok("erro", motivo=motivo)


def _carregar_estado_runtime():
    """Snapshot do estado persistente do ecossistema (runtime/state.json)."""
    if not ESTADO_PATH:
        return {}
    try:
        with open(ESTADO_PATH, encoding="utf-8") as fh:
            dados = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        "projeto_ativo": dados.get("projeto_ativo", ""),
        "objetivo": dados.get("objetivo", ""),
        "ultima_tarefa": dados.get("ultima_tarefa", ""),
        "last_task": dados.get("last_task", ""),
    }


async def _processar_mensagem(websocket, rota, texto):
    dados = {}
    if texto.strip():
        try:
            dados = json.loads(texto)
        except json.JSONDecodeError:
            try:
                await websocket.send(_json_erro("corpo JSON invalido"))
            except Exception:
                pass
            return

    tipo = dados.get("tipo", "")

    if rota == "/echo":
        await websocket.send(_json_ok("eco", dados=dados))

    elif rota == "/broadcast":
        if not tipo:
            return
        destinatarios = _BROADCAST_CLIENTES
        corpo = _json_ok(tipo, origem="broadcast", dados=dados)
        for ws in list(destinatarios):
            if ws is websocket:
                continue
            try:
                await ws.send(corpo)
            except Exception:
                destinatarios.discard(ws)

    elif rota == "/estado":
        if tipo == "ping":
            await websocket.send(_json_ok("pong", hora=_utc_iso()))
        elif tipo == "estado":
            estado = _carregar_estado_runtime()
            await websocket.send(_json_ok("estado", hora=_utc_iso(), **estado))


_BROADCAST_CLIENTES = set()
_EVENTO_PARADA = None


async def _amain(porta):
    global _EVENTO_PARADA
    _EVENTO_PARADA = asyncio.Event()
    async with serve(_handler, "127.0.0.1", porta):
        print(f"ws server em ws://127.0.0.1:{porta} (rotas: echo, broadcast, estado)", flush=True)
        await _EVENTO_PARADA.wait()


def iniciar(porta=8093):
    """Sobe o servidor numa thread daemon (padrão dos labs). Use parar() para encerrar."""
    import threading

    loop = asyncio.new_event_loop()

    def _rodar():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_amain(porta))

    th = threading.Thread(target=_rodar, name="ciclo3-ws", daemon=True)
    th.start()
    return th, loop


def parar():
    """Encerra o servidor de forma ordenada (loop continua vivo até o serve sair)."""
    if _EVENTO_PARADA is not None:
        _EVENTO_PARADA.set()


async def _handler(websocket):
    rota = websocket.request.path or "/"
    if rota not in SUDOKU_ROTAS:
        try:
            await websocket.close(code=1008, reason="rota invalida")
        except Exception:
            pass
        return

    if rota == "/broadcast":
        _BROADCAST_CLIENTES.add(websocket)
        await websocket.send(_json_ok("bem_vindo", rota=rota))

    try:
        async for mensagem in websocket:
            await _processar_mensagem(websocket, rota, mensagem)
    except Exception:
        pass
    finally:
        _BROADCAST_CLIENTES.discard(websocket)


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8093
    try:
        asyncio.run(_amain(porta))
    except KeyboardInterrupt:
        print("encerrado", flush=True)


if __name__ == "__main__":
    main()