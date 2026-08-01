import subprocess, os, sys
from pathlib import Path

log_path = Path(__file__).parent / "serve_log.txt"
log = open(log_path, "a", buffering=1, encoding="utf-8")
log.write(f"\n=== opencode serve started at {__import__('datetime').datetime.now().isoformat()} ===\n")

OPENCODE_BIN = str(Path(os.environ.get("APPDATA", "")) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
WORKDIR = r"C:\Users\David Jr\Documents\Default Project"

cmd = [
    OPENCODE_BIN, "serve",
    "--port", "8767",
]

log.write(f"Command: {' '.join(cmd)}\n")
log.flush()

proc = subprocess.Popen(
    cmd,
    cwd=WORKDIR,
    stdout=log,
    stderr=subprocess.STDOUT,
)
log.write(f"Serve PID: {proc.pid}\n")
log.flush()
