#!/usr/bin/env python3
"""tv_control.py — Controle nativo da TV LG webOS via SSAP (wss://192.168.15.6:3001).

Comandos (CLI):
  python tv_control.py status               -> volume, poder, canal
  python tv_control.py volume_up|volume_down
  python tv_control.py volume <1-100>
  python tv_control.py mute
  python tv_control.py power_on             -> Wake-on-LAN (MAC 00:a1:59:82:bb:08)
  python tv_control.py power_off
  python tv_control.py list_apps            -> aplicativos instalados
  python tv_control.py launch_app <appId>
  python tv_control.py screen_on|screen_off
  python tv_control.py play|pause|stop|rewind|ff
  python tv_control.py input_hdmi <n>
  python tv_control.py key <NOME>           -> tecla remota (UP/DOWN/LEFT/RIGHT/OK/BACK/HOME...)
"""
import sys, os, json, ssl, asyncio, time, socket, struct, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "192.168.15.6"
PORT = 3001
MAC = "00:a1:59:82:bb:08"
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys", "lgtv_50UT8050PSA.json")

KEYS = {
    "ok": "OK", "enter": "OK", "back": "BACK", "home": "HOME", "exit": "EXIT",
    "up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT",
    "volume_up": "VOLUMEUP", "volume_down": "VOLUMEDOWN", "mute": "MUTE",
    "power": "POWER", "red": "RED", "green": "GREEN", "yellow": "YELLOW", "blue": "BLUE",
    "play": "PLAY", "pause": "PAUSE", "stop": "STOP", "rewind": "REWIND", "ff": "FASTFORWARD",
    "channel_up": "CHANNELUP", "channel_down": "CHANNELDOWN",
    "input": "INPUT", "info": "INFO", "menu": "MENU", "settings": "SETTINGS",
    "netflix": "NEXUS", "prime": "AMAZON", "youtube": "YOUTUBE",
}

MANIFEST = {"manifest": {"manifestVersion": 1, "appVersion": "1.1",
    "signed": {"created": "20140509", "appId": "com.lge.test", "vendorId": "com.lge",
        "permissions": ["TEST_SECURE", "CONTROL_INPUT_TEXT", "CONTROL_MOUSE_AND_KEYBOARD",
            "READ_INSTALLED_APPS", "READ_LGE_SDX", "READ_NOTIFICATIONS", "SEARCH", "WRITE_SETTINGS",
            "WRITE_NOTIFICATION_ALERT", "CONTROL_POWER", "READ_CURRENT_CHANNEL", "READ_RUNNING_APPS",
            "READ_UPDATE_INFO", "UPDATE_FROM_REMOTE_APP", "READ_LGE_TV_INPUT_EVENTS",
            "READ_TV_CURRENT_TIME"]},
    "permissions": ["LAUNCH", "LAUNCH_WEBAPP", "APP_TO_APP", "CLOSE", "TEST_OPEN", "TEST_PROTECTED",
        "CONTROL_AUDIO", "CONTROL_DISPLAY", "CONTROL_INPUT_JOYSTICK", "CONTROL_INPUT_MEDIA_RECORDING",
        "CONTROL_INPUT_MEDIA_PLAYBACK", "CONTROL_INPUT_TV", "CONTROL_MOUSE_AND_KEYBOARD",
        "CONTROL_INPUT_TEXT", "CONTROL_POWER", "READ_APP_STATUS", "READ_CURRENT_CHANNEL",
        "READ_INPUT_DEVICE_LIST", "READ_NETWORK_STATE", "READ_RUNNING_APPS", "READ_TV_CHANNEL_LIST",
        "WRITE_NOTIFICATION_TOAST", "READ_POWER_STATE", "READ_COUNTRY_INFO", "READ_SETTINGS",
        "CONTROL_TV_SCREEN", "CONTROL_TV_STANDBY", "CONTROL_FAVORITE_GROUP", "CONTROL_USER_INFO",
        "CHECK_BLUETOOTH_DEVICE", "CONTROL_BLUETOOTH", "CONTROL_TIMER_INFO", "STB_INTERNAL_CONNECTION",
        "CONTROL_RECORDING", "READ_RECORDING_STATE", "WRITE_RECORDING_LIST", "READ_RECORDING_LIST",
        "READ_RECORDING_SCHEDULE", "WRITE_RECORDING_SCHEDULE"]}}


def load_key():
    try:
        return json.load(open(KEY_FILE, encoding="utf-8")).get("client_key")
    except Exception:
        return None


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class TvSap:
    def __init__(self, host=HOST, port=PORT, client_key=None):
        self.host = host
        self.port = port
        self.client_key = client_key or load_key() or str(uuid.uuid4())
        self.ws = None
        self._id = 0

    async def connect(self):
        import websockets
        from websockets.asyncio.client import connect
        self.ws = await connect(f"wss://{self.host}:{self.port}", ssl=_ssl_ctx(),
                                ping_interval=None, open_timeout=12)
        reg = {"id": str(uuid.uuid4()), "type": "register",
               "payload": {**MANIFEST, "client-key": self.client_key,
                           "forcePairing": False, "pairingType": "PROMPT"}}
        await self.ws.send(json.dumps(reg))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=15)
            resp = json.loads(raw)
            if resp.get("type") == "registered":
                new_key = resp.get("payload", {}).get("client-key")
                if new_key:
                    self.client_key = new_key
                    store = {**json.load(open(KEY_FILE, encoding="utf-8")),
                             "client_key": new_key}
                    json.dump(store, open(KEY_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                return True
            if resp.get("payload", {}).get("pairingType") == "PROMPT":
                print("TV pediu pareamento — aceite na tela.")
        return False

    async def request(self, uri, payload=None):
        self._id += 1
        msg = {"id": str(self._id), "type": "request",
               "uri": uri, "payload": payload or {}}
        await self.ws.send(json.dumps(msg))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=8)
            resp = json.loads(raw)
            if resp.get("id") == str(self._id):
                return resp.get("payload", {})
        return {}

    async def get_power_state(self):
        return await self.request("ssap://com.webos.service.tvpower/power/getPowerState")

    async def get_volume(self):
        return await self.request("ssap://audio/getVolume")

    async def set_volume(self, level):
        return await self.request("ssap://audio/setVolume", {"volume": int(level)})

    async def volume_step(self, up=True):
        return await self.request("ssap://audio/volumeUp" if up else "ssap://audio/volumeDown")

    async def set_mute(self, on):
        return await self.request("ssap://audio/setMute", {"mute": bool(on)})

    async def power_off(self):
        return await self.request("ssap://system/turnOff")

    async def list_apps(self):
        return await self.request("ssap://com.webos.applicationManager/listApps")

    async def launch_app(self, app_id, params=None):
        return await self.request("ssap://com.webos.applicationManager/launch",
                                  {"id": app_id, **(params or {})})

    async def get_foreground_app(self):
        return await self.request("ssap://com.webos.applicationManager/getForegroundAppInfo")

    async def set_screen_state(self, on):
        return await self.request("ssap://com.webos.service.tv.display/setScreenState",
                                  {"on": bool(on), "reason": "Control"})

    async def get_input_list(self):
        return await self.request("ssap://tv/getExternalInputList")

    async def switch_input(self, input_id):
        return await self.request("ssap://tv/switchInput", {"inputId": input_id})

    async def media_control(self, action):
        return await self.request(f"ssap://media.controls/{action}")

    async def pointer_socket(self):
        pl = await self.request("ssap://com.webos.service.networkinput/getPointerInputSocket")
        return pl.get("socketPath")

    async def send_button(self, key_name):
        import websockets
        from websockets.asyncio.client import connect
        sock = await self.pointer_socket()
        if not sock:
            return {"error": "no pointer socket"}
        async with connect(f"wss://{self.host}:{self.port}", ssl=_ssl_ctx(),
                           ping_interval=None, open_timeout=12) as ws:
            await ws.send(json.dumps({"type": "hello", "payload": {"socketPath": sock}}))
            await asyncio.sleep(0.3)
            for down in (True, False):
                await ws.send(json.dumps({"type": "button",
                                          "payload": {"key": key_name, "down": down}}))
                await asyncio.sleep(0.08)
        return {"sent": key_name}

    async def close(self):
        if self.ws:
            await self.ws.close()


def wake_on_lan(mac, ip=HOST):
    mac_clean = mac.replace(":", "").replace("-", "")
    mac_bytes = bytes.fromhex(mac_clean)
    magic = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic, (ip, 9))
    return True


async def cli_run(args):
    tv = TvSap()
    cmd = args[1] if len(args) > 1 else "status"
    rest = args[2:] if len(args) > 2 else []

    if cmd == "power_on":
        wake_on_lan(MAC)
        print("WoL enviado")
        return

    if cmd == "list_apps":
        await tv.connect()
        pl = await tv.list_apps()
        for app in pl.get("apps", []):
            print(f"{app.get('id')}  {app.get('title')}")
        await tv.close()
        return

    if cmd == "input_hdmi":
        await tv.connect()
        pl = await tv.get_input_list()
        for inp in pl.get("devices", []):
            label = inp.get("label", "")
            if f"HDMI{rest[0] if rest else '1'}" in label:
                print("troca:", await tv.switch_input(inp.get("id")))
                break
        await tv.close()
        return

    if cmd == "key":
        key = KEYS.get(rest[0].lower()) if rest else None
        if not key:
            print("tecla desconhecida")
            return
        await tv.connect()
        print(await tv.send_button(key))
        await tv.close()
        return

    if cmd == "volume":
        await tv.connect()
        print(await tv.set_volume(int(rest[0])))
        await tv.close()
        return

    if cmd == "mute":
        await tv.connect()
        print(await tv.set_mute(True))
        await tv.close()
        return

    actions = {
        "volume_up": lambda: tv.volume_step(True),
        "volume_down": lambda: tv.volume_step(False),
        "power_off": tv.power_off,
        "screen_on": lambda: tv.set_screen_state(True),
        "screen_off": lambda: tv.set_screen_state(False),
        "play": lambda: tv.media_control("play"),
        "pause": lambda: tv.media_control("pause"),
        "stop": lambda: tv.media_control("stop"),
        "rewind": lambda: tv.media_control("rewind"),
        "ff": lambda: tv.media_control("fastForward"),
        "launch_app": lambda: tv.launch_app(rest[0]),
    }
    if cmd == "status":
        await tv.connect()
        power = await tv.get_power_state()
        vol = await tv.get_volume()
        print(f"poder={power} volume={vol}")
        await tv.close()
        return
    if cmd in actions:
        await tv.connect()
        res = await actions[cmd]()
        print(res)
        await tv.close()
        return

    print(f"comando desconhecido: {cmd}")


if __name__ == "__main__":
    asyncio.run(cli_run(sys.argv))
