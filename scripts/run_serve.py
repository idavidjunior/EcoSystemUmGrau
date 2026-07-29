import subprocess
import os
import sys

log_path = r"C:\Users\Playtec-bancada\Desktop\Codigos\serve_log.txt"
log = open(log_path, "a", buffering=1)
log.write(f"\n=== opencode serve started at {__import__('datetime').datetime.now().isoformat()} ===\n")

OPENCODE_BIN = os.path.join(
    os.environ.get("APPDATA", ""),
    r"npm\node_modules\opencode-ai\bin\opencode.exe"
)
WORKDIR = r"C:\Users\Playtec-bancada\Desktop\Codigos"

cmd = [
    OPENCODE_BIN, "serve",
    "--port", "18765",
    "--dir", WORKDIR,
    "--model", "opencode/deepseek-v4-flash-free",
]

env = os.environ.copy()
log.write(f"Command: {' '.join(cmd)}\n")
log.flush()

proc = subprocess.Popen(
    cmd,
    stdout=log,
    stderr=subprocess.STDOUT,
    env=env,
)
log.write(f"PID: {proc.pid}\n")
log.flush()
# Don't wait - keep serve running in background
