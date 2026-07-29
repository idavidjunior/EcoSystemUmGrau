import subprocess
import os
import sys

log = open(r"C:\Users\Playtec-bancada\Desktop\Codigos\bridge_log.txt", "a", buffering=1)
log.write("\n\n=== Bridge started at " + __import__("datetime").datetime.now().isoformat() + " ===\n")

env = os.environ.copy()

cmd = [
    os.path.join(env.get("APPDATA", ""), r"npm\node_modules\opencode-ai\bin\opencode.exe"),
    "serve", "--port", "18765",
    "--dir", r"C:\Users\Playtec-bancada\Desktop\Codigos",
]

proc = subprocess.Popen(
    cmd,
    stdout=log,
    stderr=subprocess.STDOUT,
    env=env,
)
log.write(f"Serve PID: {proc.pid}\n")
