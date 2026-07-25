import sys, json, os, socket, re, subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def _run_hidden(args, **kw):
    """Run subprocess with no console window on Windows."""
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 5)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    kw["startupinfo"] = si
    return subprocess.run(args, **kw)

cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
result = {}

if cmd in ("providers", "all"):
    try:
        from provider_manager.manager import ProviderManager
        pm = ProviderManager(BASE_DIR)
        pm.initialize()
        from provider_manager.status import status_as_dict
        result["providers"] = status_as_dict(pm)
    except Exception as e:
        result["providers"] = {"error": str(e)}

if cmd in ("servers", "all"):
    try:
        from provider_manager.server_manager import ServerManager
        sm = ServerManager()
        sm.initialize()
        servers_list = []
        for name, inst in sm._servers.items():
            servers_list.append({
                "name": name,
                "host": inst.host,
                "port": inst.port,
                "status": inst.status,
                "pid": inst.pid
            })
        result["servers"] = servers_list
    except Exception as e:
        result["servers"] = {"error": str(e)}

if cmd in ("ports", "all"):
    ports = {}
    for p in [50136, 50137]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", p))
            ports[str(p)] = "LISTENING"
        except:
            ports[str(p)] = "CLOSED"
        finally:
            s.close()
    result["ports"] = ports

if cmd in ("services", "all"):
    svc = {}

    # RustDesk
    try:
        r = _run_hidden(["cmd", "/c", "sc", "query", "RustDesk", "|", "findstr", "RUNNING"])
        svc["rustdesk"] = "RUNNING" if "RUNNING" in r.stdout else "STOPPED"
    except:
        svc["rustdesk"] = "ERROR"

    # ADB
    try:
        r = _run_hidden(["cmd", "/c", "adb", "devices"])
        svc["adb"] = "CONNECTED" if "100.64.71.9:5555" in r.stdout and "device" in r.stdout else "DISCONNECTED"
    except:
        svc["adb"] = "ERROR"

    # MCP (provider_mcp_server process)
    try:
        r = _run_hidden(["cmd", "/c", "wmic", "process", "where", "name='python.exe'", "get", "CommandLine"])
        svc["mcp"] = "RUNNING" if "provider_mcp_server" in r.stdout else "STOPPED"
    except:
        svc["mcp"] = "ERROR"

    result["services"] = svc

print(json.dumps(result))
