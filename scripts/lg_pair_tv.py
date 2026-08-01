#!/usr/bin/env python
"""Pareamento SSAP seguro com a TV LG webOS (porta 3001 wss://).

Fluxo:
  - conecta wss://IP:3001
  - envia register (client-id aleatório)
  - se TV responder pairingType=PROMPT, informa que o usuário deve aceitar na TV
  - reenvia register periodicamente; quando a TV aceitar, responde registrado + client-key
  - salva o client-key + histórico de chaves em keys/lgtv_50UT8050PSA.json para uso futuro

Uso:
  python lg_pair_tv.py                    # tenta usar chave salva; senao inicia pareamento
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import asyncio
import json
import os
import uuid
import ssl
import websockets
import time

HOST = "192.168.15.6"
PORT = 3001
KEY_FILE = os.path.join(os.path.dirname(__file__), "keys", "lgtv_50UT8050PSA.json")


def load_store():
    if os.path.exists(KEY_FILE):
        try:
            return json.load(open(KEY_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_store(store):
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


async def main():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    store = load_store()
    client_key = store.get("client-key", str(uuid.uuid4()))
    print(f"client-key: {client_key}")

    async def regen():
        async with websockets.connect(f"wss://{HOST}:{PORT}", ssl=ssl_ctx,
                                      ping_interval=None, open_timeout=15) as ws:
            # envia register
            msg = {"id": 1, "type": "register",
                   "payload": {"client-id": client_key, "forcePairing": True}}
            await ws.send(json.dumps(msg))
            resp_raw = await asyncio.wait_for(ws.recv(), timeout=10)
            resp = json.loads(resp_raw)
            print("Resposta register:", resp)
            payload = resp.get("payload", {})
            if payload.get("pairingType") == "PROMPT":
                return "PROMPT", payload
            if payload.get("returnValue") and not payload.get("pairingType"):
                # pode ser REGISTERED direto (ja pareado)
                return "REGISTERED", payload
            return "UNKNOWN", payload

    print("Conectando na TV LG (wss://3001)...")
    try:
        tag, payload = await regen()
    except Exception as e:
        print("erro conexao:", type(e).__name__, e)
        return

    if tag == "PROMPT":
        print("PAREIE: um codigo aparecera na tela da TV. Confirme 'Permitir' na TV.")
        # pede ao usuario para confirmar
        input("Aperte ENTER depois de confirmar na TV... ")
        # reenvia register para capturar o client-key aprovado
        attempts = 0
        while attempts < 15:
            try:
                tag2, p2 = await regen()
            except Exception as e:
                print("erro re-registro:", e)
                tag2 = None
            print(f"tentativa {attempts+1}: tag={tag2}")
            if tag2 == "REGISTERED" or (p2.get("returnValue") and "client-key" in str(p2)):
                new_key = p2.get("client-key", client_key)
                print("Pareado! client-key:", new_key)
                store["client-key"] = new_key
                save_store(store)
                print("Chave salva em", KEY_FILE)
                return
            attempts += 1
            time.sleep(2)
        print("Nao foi aprovado (timeout). Tente novamente.")
    elif tag == "REGISTERED":
        print("Ja pareado. client-key:", client_key)
        store["client-key"] = client_key
        save_store(store)


if __name__ == "__main__":
    asyncio.run(main())
