import subprocess, os, sys
from pathlib import Path

log_path = r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_log.txt"
log = open(log_path, "a", buffering=1, encoding="utf-8")
log.write(f"\n=== Bridge started at {__import__('datetime').datetime.now().isoformat()} ===\n")

BIN = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"
BRIDGE_SCRIPT = r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\scripts\jarvis_bridge.py"

log.write(f"Starting jarvis_bridge.py\n")
log.flush()

proc = subprocess.Popen(
    [sys.executable, "-u", BRIDGE_SCRIPT],
    stdout=log,
    stderr=subprocess.STDOUT,
)
log.write(f"Bridge PID: {proc.pid}\n")
log.flush()
