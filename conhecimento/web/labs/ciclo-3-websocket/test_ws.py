"""Teste canônico do Ciclo 3 - Realtime WebSocket (bloco F/H).

Valida: eco (/echo), broadcast entre 2 clientes (/broadcast), heartbeat
ping/pong (/estado) e snapshot do estado persistente do runtime (/estado).

Uso:
  python conhecimento/web/labs/ciclo-3-websocket/test_ws.py
"""

import asyncio
import json
import os
import socket
import sys

from websockets.asyncio.client import connect

import ws_server

RAIZ = os.path.dirname(os.path.abspath(__file__))
ws_server.ESTADO_PATH = os.path.abspath(
    os.path.join(RAIZ, "..", "..", "..", "..", "runtime", "state.json")
)

RESULTADOS = []


def _free_porta():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check(nome, ok, detalhe=""):
    RESULTADOS.append((nome, ok, detalhe))
    print(f"[{'PASS' if ok else 'FAIL'}] {nome}" + (f" - {detalhe}" if detalhe else ""))


async def exercitar(porta):
    base = f"ws://127.0.0.1:{porta}"

    async with connect(base + "/echo") as eco:
        await eco.send(json.dumps({"tipo": "eco", "valor": 42}))
        resp = json.loads(await eco.recv())
        check("echo", resp.get("tipo") == "eco" and resp.get("dados", {}).get("valor") == 42)

        await eco.send("{quebrado")
        resp = json.loads(await eco.recv())
        check("echo json inválido", resp.get("tipo") == "erro")

    async with connect(base + "/broadcast") as cli_a, connect(base + "/broadcast") as cli_b:
        await cli_a.recv()  # bem_vindo A
        await cli_b.recv()  # bem_vindo B
        await cli_a.send(json.dumps({"tipo": "aviso", "texto": "ola"}))
        got = None
        for _ in range(2):
            msg = json.loads(await cli_b.recv())
            if msg.get("tipo") == "aviso":
                got = msg
                break
        check("broadcast para outro cliente", got is not None and got.get("dados", {}).get("texto") == "ola")

    async with connect(base + "/estado") as est:
        await est.send(json.dumps({"tipo": "ping"}))
        pong = json.loads(await est.recv())
        check("heartbeat ping/pong", pong.get("tipo") == "pong" and pong.get("hora", "") != "")

        await est.send(json.dumps({"tipo": "estado"}))
        estado = json.loads(await est.recv())
        check(
            "estado persistente do runtime",
            estado.get("tipo") == "estado"
            and estado.get("projeto_ativo", "") != "",
            f"projeto={estado.get('projeto_ativo', 'vazio')}",
        )

    try:
        async with connect(base + "/inexistente") as cli:
            await asyncio.wait_for(cli.wait_closed(), timeout=3)
            check("rota inexistente rejeitada", True)
    except Exception:
        check("rota inexistente rejeitada", True)


async def main():
    porta = _free_porta()
    _th, _loop = ws_server.iniciar(porta)
    try:
        await asyncio.sleep(0.6)
        await exercitar(porta)
    finally:
        ws_server.parar()
        _th.join(timeout=3)

    falhas = [r for r in RESULTADOS if not r[1]]
    total = len(RESULTADOS)
    print(f"\nSTATUS: {'OK' if not falhas else 'FALHOU'} ({total} checks, {len(falhas)} falhas)")
    return 0 if not falhas else 1


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)