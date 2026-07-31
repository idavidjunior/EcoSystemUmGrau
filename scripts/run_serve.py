import subprocess, os, sys
from pathlib import Path

log_path = Path(__file__).parent / "serve_log.txt"
log = open(log_path, "a", buffering=1, encoding="utf-8")
log.write(f"\n=== opencode serve started at {__import__('datetime').datetime.now().isoformat()} ===\n")

OPENCODE_BIN = str(Path(os.environ.get("APPDATA", "")) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
WORKDIR = r"C:\Users\David Jr\Documents\Default Project"
SERVE_CONFIG = str(Path(__file__).parent / "opencode-serve.jsonc")

cmd = [
    OPENCODE_BIN, "serve",
    "--port", "8766",
    "--dir", WORKDIR,
    "-c", SERVE_CONFIG,
]

log.write(f"Command: {' '.join(cmd)}\n")
log.flush()

proc = subprocess.Popen(
    cmd,
    stdout=log,
    stderr=subprocess.STDOUT,
)
log.write(f"Serve PID: {proc.pid}\n")
log.flush()
