import json, uuid, time
from pathlib import Path
ROOT = Path(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau")
TTS_CMD = ROOT / "runtime" / "tts_cmd.json"
req_id = str(uuid.uuid4())[:8]
cmd = {"cmd": "speak", "texto": "Eco ativado", "request_id": req_id, "priority": 1}
TTS_CMD.parent.mkdir(parents=True, exist_ok=True)
tmp = TTS_CMD.with_suffix(".tmp")
tmp.write_text(json.dumps(cmd, ensure_ascii=False), encoding="utf-8")
tmp.replace(TTS_CMD)
print("Enviado:", req_id)
resp_file = ROOT / "runtime" / f"tts_resp_{req_id}.json"
for _ in range(180):
    if resp_file.exists():
        resp = json.loads(resp_file.read_text(encoding="utf-8"))
        resp_file.unlink(missing_ok=True)
        print("Resposta:", resp)
        break
    time.sleep(0.05)
else:
    print("TIMEOUT")