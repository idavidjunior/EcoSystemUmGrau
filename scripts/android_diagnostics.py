import subprocess, json, sys, re, asyncio
from pathlib import Path

ADB = r"C:\Users\David Jr\AppData\Local\Android\Sdk\platform-tools\adb.exe"
PKG = "com.voxumgrau.app"
DEVICE = "192.168.15.4:5555"
BRIDGE_HOST = "100.91.141.101"
BRIDGE_PORT = 8765

def adb(*args):
    try:
        r = subprocess.run([ADB, "-s", DEVICE] + list(args), capture_output=True, text=True, timeout=15)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", f"ADB nao encontrado em {ADB}", 1
    except subprocess.TimeoutExpired:
        return "", "Comando ADB excedeu 15s", 1

def adb_shell(cmd):
    return adb("shell", cmd)

async def testar_websocket_async():
    try:
        import websockets
        async with websockets.connect(f"ws://{BRIDGE_HOST}:{BRIDGE_PORT}", ping_interval=None, open_timeout=5) as ws:
            await ws.send(json.dumps({"tipo": "ping", "origem": "diagnostico"}))
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            if resp:
                return "conectado e respondendo"
            return "conectado sem resposta"
    except asyncio.TimeoutError:
        return "conectado sem resposta"
    except Exception as e:
        s = str(e)
        if "Connection refused" in s or "ConnectionRefusedError" in s:
            return "bridge nao esta rodando na porta " + str(BRIDGE_PORT)
        if "OSError" in s or "timed out" in s:
            return "sem conectividade com o host " + BRIDGE_HOST
        return f"falha: {s}"

def testar_websocket():
    return asyncio.run(testar_websocket_async())

def analisar_crashes(logs):
    crashes = []
    for l in logs:
        if "FATAL EXCEPTION" in l or "AndroidRuntime" in l:
            crashes.append(l)
        if "ANR" in l or "anr_" in l:
            crashes.append("[ANR] " + l)
        if "NullPointerException" in l or "RuntimeException" in l:
            crashes.append("[EXCEPTION] " + l)
        if "Native crash" in l or "SIGSEGV" in l:
            crashes.append("[NATIVE] " + l)
    return crashes

def verificar_audio():
    out, err, code = adb_shell("dumpsys audio | grep -E 'audioConfig|routing|device' | head -5")
    config = out[:300] if out else ""
    out2, err2, code2 = adb_shell("dumpsys media_session | grep -E 'PlaybackState|package=com.voxumgrau' | head -5")
    sessao = out2[:200] if out2 else ""
    estado = "nao verificado"
    if "PlaybackState" in sessao:
        if "state=3" in sessao: estado = "tocando"
        elif "state=2" in sessao: estado = "pausado"
        elif "state=1" in sessao: estado = "parado"
        elif "state=6" in sessao: estado = "pulando"
    if "IMediaPlayer" in config: estado = "midia ativo"
    return {"config": config, "sessao": sessao, "estado": estado}

def checar_adb():
    try:
        r = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=5)
        if DEVICE in r.stdout:
            return "ok"
        if "device" in r.stdout and DEVICE not in r.stdout:
            return f"dispositivo {DEVICE} nao encontrado. Dispositivos: " + r.stdout.replace("\n", "; ")
        return "nenhum dispositivo conectado"
    except FileNotFoundError:
        return f"ADB nao encontrado"
    except Exception as e:
        return f"erro: {e}"

def formatar_resumo(r):
    saida = f"Modelo: {r['dispositivo']['modelo']} | Android: {r['dispositivo']['android']} (SDK {r['dispositivo']['sdk']}) | PID: {r['aplicativo']['pid']} | Memoria: {r['aplicativo']['memoria_kb'] // 1024} MB | Versao: {r['aplicativo']['version_name']} (codigo {r['aplicativo']['version_code']}) | Bateria: {r['bateria']['nivel']}% {r['bateria']['status']} {r['bateria']['temperatura']} | Rede: {r['rede']['tipo']} | WebSocket bridge: {r['rede']['websocket_porta_8765']} | Audio: {r['audio']['player']} | Processo: {r['aplicativo']['processo']} | Erros: {len(r['erros'])} | Logs: {len(r['logs'])}"
    return saida

def run():
    result = {
        "status": "ok", "dispositivo": {}, "aplicativo": {},
        "bateria": {}, "rede": {}, "audio": {}, "crash_analysis": {},
        "logs": [], "erros": []
    }

    out, err, code = adb_shell("getprop ro.product.model")
    if not code: result["dispositivo"]["modelo"] = out.strip()
    else: result["erros"].append(f"modelo: {err}")

    out, err, code = adb_shell("getprop ro.build.version.release")
    if not code: result["dispositivo"]["android"] = out.strip()
    else: result["erros"].append(f"android: {err}")

    out, err, code = adb_shell("getprop ro.build.version.sdk")
    if not code: result["dispositivo"]["sdk"] = out.strip()

    out, err, code = adb_shell("getprop persist.sys.timezone")
    if not code: result["dispositivo"]["timezone"] = out.strip()

    out, err, code = adb_shell("dumpsys battery")
    if not code:
        for line in out.splitlines():
            l = line.strip()
            if l.startswith("level:"): result["bateria"]["nivel"] = l.split()[-1]
            if l.startswith("temperature:"):
                t = int(l.split()[-1]); result["bateria"]["temperatura"] = f"{t/10:.1f}C"
            if l.startswith("status:"):
                s = int(l.split()[-1])
                m = {1:"descarregando",2:"carregando",3:"cheia",4:"desconhecido",5:"em espera"}
                result["bateria"]["status"] = m.get(s, "desconhecido")
    else: result["erros"].append(f"bateria: {err}")

    out, err, code = adb_shell("dumpsys meminfo " + PKG)
    if not code:
        for line in out.splitlines():
            if line.strip().startswith("TOTAL PSS"):
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit():
                        result["aplicativo"]["memoria_kb"] = int(p)
                        break
                break

    out, err, code = adb_shell("dumpsys package " + PKG + " | grep -E 'versionCode|versionName|firstInstallTime|lastUpdateTime'")
    if not code:
        for line in out.splitlines():
            l = line.strip()
            if "versionCode=" in l:
                m = re.search(r"versionCode=(\d+)", l)
                if m: result["aplicativo"]["version_code"] = int(m.group(1))
            if "versionName=" in l:
                m = re.search(r"versionName=([\d.]+)", l)
                if m: result["aplicativo"]["version_name"] = m.group(1)
            if "firstInstallTime=" in l:
                result["aplicativo"]["instalado"] = l.split("=", 1)[1]
            if "lastUpdateTime=" in l:
                result["aplicativo"]["atualizado"] = l.split("=", 1)[1]
    else: result["erros"].append(f"package: {err}")

    out, err, code = adb_shell("ps -A | grep " + PKG)
    if code or not out.strip():
        result["aplicativo"]["processo"] = "parado"
    else:
        result["aplicativo"]["processo"] = "rodando"
        pid = None
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                pid = parts[1]; break
        if pid: result["aplicativo"]["pid"] = int(pid)

    pid = result["aplicativo"].get("pid")
    if pid:
        out, err, code = adb_shell(f"logcat -d --pid={pid} -s VoxUmGrau:* *:E *:W")
    else:
        out, err, code = adb_shell("logcat -d -s VoxUmGrau:* *:E *:W")
    if out:
        lines = [l for l in out.splitlines() if l.strip() and "---------" not in l]
        result["logs"] = lines[-20:]

    result["crash_analysis"]["crashes_detectados"] = analisar_crashes(out.splitlines() if out else [])

    out, err, code = adb_shell("dumpsys connectivity | grep -E 'ActiveNetwork|WIFI|mobile|NetworkAgentInfo'")
    if "WIFI" in out: result["rede"]["tipo"] = "Wi-Fi"
    elif "mobile" in out: result["rede"]["tipo"] = "dados moveis"
    else: result["rede"]["tipo"] = "nao verificado"

    result["audio"] = verificar_audio()
    logs_str = str(result["logs"])
    if "IMediaPlayer" in logs_str or "MediaPlayer" in logs_str:
        result["audio"]["player"] = "ativo (referencias no log)"
    elif "SoundPool" in result["audio"]["config"]:
        result["audio"]["player"] = "SoundPool detectado"
    else:
        result["audio"]["player"] = "nao verificado"

    ws = testar_websocket()
    result["rede"]["websocket_porta_8765"] = ws

    erros_count = len(result["erros"]) + (1 if result["crash_analysis"]["crashes_detectados"] else 0)
    result["status"] = "ok" if erros_count == 0 else "parcial" if erros_count < 3 else "falha"

    return result

if __name__ == "__main__":
    args = set(sys.argv[1:])
    if "--self-test" in args or "--check" in args:
        print("ADB:", checar_adb())
        print("WebSocket:", testar_websocket())
        sys.exit(0)
    r = run()
    if "--resumo" in args or "--summary" in args:
        print(formatar_resumo(r))
    elif "--json" in args:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["status"] != "falha" else 1)
