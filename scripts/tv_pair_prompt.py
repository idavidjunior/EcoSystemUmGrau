import sys, os, json, uuid, ssl, asyncio, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from websockets.asyncio.client import connect

# manifest reaproveitado de lgtvremote-cli (porta 3001 wss)
REGISTRATION_PAYLOAD = {
    "manifest": {
        "manifestVersion": 1,
        "appVersion": "1.1",
        "signed": {
            "created": "20140509",
            "appId": "com.lge.test",
            "vendorId": "com.lge",
            "permissions": ["TEST_SECURE","CONTROL_INPUT_TEXT","CONTROL_MOUSE_AND_KEYBOARD",
                "READ_INSTALLED_APPS","READ_LGE_SDX","READ_NOTIFICATIONS","SEARCH","WRITE_SETTINGS",
                "WRITE_NOTIFICATION_ALERT","CONTROL_POWER","READ_CURRENT_CHANNEL","READ_RUNNING_APPS",
                "READ_UPDATE_INFO","UPDATE_FROM_REMOTE_APP","READ_LGE_TV_INPUT_EVENTS","READ_TV_CURRENT_TIME"],
        },
        "permissions": ["LAUNCH","LAUNCH_WEBAPP","APP_TO_APP","CLOSE","TEST_OPEN","TEST_PROTECTED",
            "CONTROL_AUDIO","CONTROL_DISPLAY","CONTROL_INPUT_JOYSTICK","CONTROL_INPUT_MEDIA_RECORDING",
            "CONTROL_INPUT_MEDIA_PLAYBACK","CONTROL_INPUT_TV","CONTROL_MOUSE_AND_KEYBOARD","CONTROL_INPUT_TEXT",
            "CONTROL_POWER","READ_APP_STATUS","READ_CURRENT_CHANNEL","READ_INPUT_DEVICE_LIST","READ_NETWORK_STATE",
            "READ_RUNNING_APPS","READ_TV_CHANNEL_LIST","WRITE_NOTIFICATION_TOAST","READ_POWER_STATE","READ_COUNTRY_INFO",
            "READ_SETTINGS","CONTROL_TV_SCREEN","CONTROL_TV_STANDBY","CONTROL_FAVORITE_GROUP","CONTROL_USER_INFO",
            "CHECK_BLUETOOTH_DEVICE","CONTROL_BLUETOOTH","CONTROL_TIMER_INFO","STB_INTERNAL_CONNECTION",
            "CONTROL_RECORDING","READ_RECORDING_STATE","WRITE_RECORDING_LIST","READ_RECORDING_LIST","READ_RECORDING_SCHEDULE","WRITE_RECORDING_SCHEDULE"],
    }
}
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys", "lgtv_50UT8050PSA.json")


async def main():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    print("Conectando wss://192.168.15.6:3001 ...")
    async with connect("wss://192.168.15.6:3001", ssl=ssl_ctx,
                       open_timeout=15, ping_interval=None) as ws:
        print("Conectado! Enviando register (pairingType=PROMPT)...")
        reg = {"type": "register", "id": str(uuid.uuid4()),
               "payload": {**REGISTRATION_PAYLOAD, "pairingType": "PROMPT", "forcePairing": True}}
        await ws.send(json.dumps(reg))
        # espera a resposta PROMPT da TV (mostra o codigo na tela)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 120:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
            except asyncio.TimeoutError:
                print("aguardando aceitacao na TV... (ainda sem resposta)")
                continue
            resp = json.loads(raw)
            resp_type = resp.get("type", "")
            payload = resp.get("payload", {})
            print("RESP:", resp_type, payload)
            if resp_type == "registered" or "client-key" in payload:
                key = payload.get("client-key")
                if key:
                    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
                    data = {"ip": "192.168.15.6", "model": "50UT8050PSA.BWZJLJZ", "client_key": key}
                    with open(KEY_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("PAREADO! client-key salvo em", KEY_FILE)
                    return key
            elif payload.get("pairingType") == "PROMPT":
                print("TV mostrou o prompt de pareamento. Confirme PERMITIR na tela do TV.")
            elif payload.get("pairingType") == "PIN":
                print("TV exibiu um PIN — favor informe o PIN exibido na tela do TV.")
        print("timeout aguardando aceitacao.")


if __name__ == "__main__":
    k = asyncio.run(main())
    print("KEY:", k)
