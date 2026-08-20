#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tts_service.py — Serviço único de TTS (SpeechPipeline singleton).

Todos os componentes (narrador, widget, bridge) enviam requisições para este
processo via arquivo de comando em runtime/tts_cmd.json. O serviço roda em
background, consome a fila sequencialmente e respeita PARAR_FALA global.

Uso:
    python scripts/tts_service.py        # inicia daemon (console)
    pythonw scripts/tts_service.py       # sem console

Protocolo de comando (runtime/tts_cmd.json):
    {"cmd": "speak", "texto": "...", "request_id": 123, "priority": 0}
    {"cmd": "stop", "request_id": 123}
    {"cmd": "pause"}
    {"cmd": "resume"}

Resposta (runtime/tts_resp_<request_id>.json):
    {"status": "ok|error", "request_id": 123, "msg": "..."}
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
CMD_FILE = RUNTIME / "tts_cmd.json"
STOP_FLAG = RUNTIME / "parar_fala.flag"

RUNTIME.mkdir(parents=True, exist_ok=True)

# SpeechPipeline singleton
try:
    sys.path.insert(0, str(ROOT))
    from tts import SpeechPipeline
    _speech = SpeechPipeline()
    SPEECH_AVAILABLE = True
except Exception as e:
    print(f"[tts_service] SpeechPipeline indisponível: {e}", flush=True)
    SPEECH_AVAILABLE = False
    _speech = None

# Fallback vox_audio
VOX = ROOT / "scripts" / "vox_audio.py"

# Estado
_paused = False
_current_req_id = None
_processing = False


def _log(msg):
    print(f"[tts_service] {msg}", flush=True)


def _atomic_write(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        import os as _os
        _os.replace(tmp, path)


def _read_cmd():
    try:
        if CMD_FILE.exists():
            return json.loads(CMD_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        pass
    return None


def _clear_cmd():
    try:
        CMD_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _write_resp(req_id, status, msg=""):
    resp_file = RUNTIME / f"tts_resp_{req_id}.json"
    _atomic_write(resp_file, {"status": status, "request_id": req_id, "msg": msg})


def _ler_volume() -> int:
    """ Lê volume (0-100) do widget_state.json. """
    try:
        ws = RUNTIME / "widget_state.json"
        if ws.exists():
            d = json.loads(ws.read_text(encoding="utf-8"))
            return max(0, min(100, int(d.get("volume", 80))))
    except Exception:
        pass
    return 80


def _speak_text(texto: str, stop_flag: Path, req_id: str) -> bool:
    global _current_req_id, _processing
    _current_req_id = req_id
    _processing = True
    volume = _ler_volume()
    try:
        if SPEECH_AVAILABLE and _speech:
            _speech.speak(texto, block=True, stop_flag=stop_flag, volume=volume)
            return True
        # Fallback
        import subprocess
        subprocess.run(
            [sys.executable, str(VOX), "falar", texto],
            cwd=str(ROOT),
            timeout=90,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception as e:
        _log(f"erro fala: {e}")
        return False
    finally:
        _current_req_id = None
        _processing = False


def main():
    global _paused
    _log("TTS Service iniciado (singleton SpeechPipeline)")
    _log(f"  SpeechPipeline: {'OK' if SPEECH_AVAILABLE else 'fallback vox_audio'}")
    _log(f"  Comando: {CMD_FILE}")
    _log(f"  Stop flag: {STOP_FLAG}")

    last_mtime = 0
    while True:
        try:
            # Checa comando novo
            if CMD_FILE.exists():
                try:
                    mtime = CMD_FILE.stat().st_mtime
                except OSError:
                    continue
                if mtime != last_mtime:
                    last_mtime = mtime
                    cmd = _read_cmd()
                    if cmd:
                        _clear_cmd()
                        c = cmd.get("cmd")
                        req_id = cmd.get("request_id", str(uuid.uuid4())[:8])

                        if c == "speak":
                            texto = cmd.get("texto", "").strip()
                            if texto and not _paused:
                                _log(f"fala req={req_id}: {texto[:60]}...")
                                ok = _speak_text(texto, STOP_FLAG, req_id)
                                _write_resp(req_id, "ok" if ok else "error")
                            elif _paused:
                                _write_resp(req_id, "ignored", "pausado")
                            else:
                                _write_resp(req_id, "ignored", "texto vazio")

                        elif c == "stop":
                            _log(f"STOP req={req_id}")
                            try:
                                STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
                            except Exception:
                                pass
                            _write_resp(req_id, "ok")

                        elif c == "pause":
                            _paused = True
                            _log("PAUSADO")
                            _write_resp(req_id, "ok")

                        elif c == "resume":
                            _paused = False
                            _log("RESUMIDO")
                            _write_resp(req_id, "ok")

            # Limpa flag de parada após 2s se não consumida
            if STOP_FLAG.exists():
                try:
                    ts = float(STOP_FLAG.read_text(encoding="utf-8").strip())
                    if time.time() - ts > 2:
                        STOP_FLAG.unlink(missing_ok=True)
                except Exception:
                    pass

            time.sleep(0.05)
        except KeyboardInterrupt:
            _log("Encerrando...")
            break
        except Exception as e:
            _log(f"loop error: {e}")
            time.sleep(0.5)

    return 0


if __name__ == "__main__":
    sys.exit(main())