import subprocess, json, sys, re
from pathlib import Path

ADB = r"C:\Users\Playtec-bancada\AppData\Local\Android\Sdk\platform-tools\adb.exe"
PKG = "com.voxumgrau.app"
DEVICE = "100.64.71.9:5555"

def adb(*args):
    try:
        r = subprocess.run([ADB, "-s", DEVICE] + list(args), capture_output=True, text=True, timeout=15)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", f"ADB não encontrado em {ADB}", 1
    except subprocess.TimeoutExpired:
        return "", "Comando ADB excedeu 15s", 1

def adb_shell(cmd):
    return adb("shell", cmd)

def run():
    result = {
        "status": "ok", "dispositivo": {}, "aplicativo": {},
        "bateria": {}, "rede": {}, "audio": {}, "logs": [], "erros": []
    }
    # device info
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
    # battery
    out, err, code = adb_shell("dumpsys battery")
    if not code:
        for line in out.splitlines():
            l = line.strip()
            if l.startswith("level:"): result["bateria"]["nivel"] = l.split()[1]
            if l.startswith("temperature:"):
                t = int(l.split()[1]); result["bateria"]["temperatura"] = f"{t/10:.1f}C"
            if l.startswith("status:"):
                s = int(l.split()[1])
                m = {1:"descarregando",2:"carregando",3:"cheia",4:"desconhecido",5:"em espera"}
                result["bateria"]["status"] = m.get(s, "desconhecido")
    else: result["erros"].append(f"bateria: {err}")
    # memory
    out, err, code = adb_shell("dumpsys meminfo " + PKG)
    if not code:
        for line in out.splitlines():
            if line.strip().startswith("TOTAL") and not "PSS" in line:
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    result["aplicativo"]["memoria_kb"] = int(parts[1])
    # package info
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
    # process
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
    # recent logs
    pid = result["aplicativo"].get("pid")
    if pid:
        out, err, code = adb_shell(f"logcat -d --pid={pid} -s VoxUmGrau:* *:E *:W")
    else:
        out, err, code = adb_shell("logcat -d -s VoxUmGrau:* *:E *:W")
    if out:
        lines = [l for l in out.splitlines() if l.strip() and "---------" not in l]
        result["logs"] = lines[-15:]
    # network
    out, err, code = adb_shell("dumpsys connectivity | grep -E 'ActiveNetwork|WIFI|mobile|NetworkAgentInfo'")
    if "WIFI" in out: result["rede"]["tipo"] = "Wi-Fi"
    elif "mobile" in out: result["rede"]["tipo"] = "dados moveis"
    else: result["rede"]["tipo"] = "nao verificado"
    # audio
    out, err, code = adb_shell("dumpsys audio | grep -E 'audioConfig|routing|device' | head -5")
    if out: result["audio"]["config"] = out[:200]
    # check WebSocket by looking for active connections to port 8765
    out, err, code = adb_shell("ss -t 2>/dev/null | grep -E '8765|ESTAB' || netstat -an 2>/dev/null | grep 8765 || echo 'indisponivel'")
    if "8765" in out and "ESTAB" in out: result["rede"]["websocket_porta_8765"] = "conectado"
    elif "8765" in out: result["rede"]["websocket_porta_8765"] = "conexao presente"
    else: result["rede"]["websocket_porta_8765"] = "desconectado"
    result["audio"]["player"] = "ativo" if "IMediaPlayer" in str(result["logs"]) else "nao verificado"

    # overall status
    erros_count = len(result["erros"])
    result["status"] = "ok" if erros_count == 0 else "parcial" if erros_count < 3 else "falha"

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] != "falha" else 1

if __name__ == "__main__":
    sys.exit(run())
