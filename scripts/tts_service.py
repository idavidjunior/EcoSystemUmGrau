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
ESTADO_FILE = RUNTIME / "tts_estado.json"
TELEMETRIA_FILE = RUNTIME / "tts_telemetria.jsonl"
NARRACAO_CONTROLE = RUNTIME / "narracao_estado.json"

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


def _pausa_total():
    """True se a pausa total (botão Pausar) estiver ativa — silencia este
    serviço até o usuário retomar, independentemente de `pausado`."""
    try:
        if NARRACAO_CONTROLE.exists():
            data = json.loads(NARRACAO_CONTROLE.read_text(encoding="utf-8"))
            return bool(data.get("pausa_total", False))
    except Exception:
        return False
    return False


def _log(msg):
    line = f"[tts_service] {msg}"
    print(line, flush=True)
    try:
        log_file = RUNTIME / "tts_service.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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


def _cleanup_old_responses(max_age_sec: int = 600):
    """Remove arquivos tts_resp_*.json mais velhos que max_age_sec (padrão 10 min)."""
    try:
        now = time.time()
        for f in RUNTIME.glob("tts_resp_*.json"):
            try:
                age = now - f.stat().st_mtime
                if age > max_age_sec:
                    f.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass


def _write_resp(req_id, status, msg=""):
    resp_file = RUNTIME / f"tts_resp_{req_id}.json"
    _atomic_write(resp_file, {"status": status, "request_id": req_id, "msg": msg})


def _telemetrizar(reg: dict):
    """Append de uma linha JSONL com dados da fala (evidência contra truncamento).

    Campos: ts, request_id, texto_chars, palavras, chunks, cache_hit,
    mp3_bytes, duracao_s, status, erro. Rotação simples aos 5 MB.
    """
    try:
        if TELEMETRIA_FILE.exists() and TELEMETRIA_FILE.stat().st_size > 5_000_000:
            TELEMETRIA_FILE.replace(TELEMETRIA_FILE.with_suffix(".jsonl.old"))
        with open(TELEMETRIA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except Exception as e:
        _log(f"telemetria falhou: {e}")


def _cache_info(texto: str):
    """(existe_antes, bytes_depois) do MP3 em cache para este texto."""
    try:
        import hashlib
        from tts.config import TTS_DIR
        cache_dir = TTS_DIR.parent / "runtime" / "tts_cache"
        cache_file = cache_dir / f"{hashlib.md5(texto.encode('utf-8')).hexdigest()[:12]}.mp3"
        antes = cache_file.exists()
        return cache_file, antes
    except Exception:
        return None, None


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


def _escrever_estado(falando: bool, texto_atual: str = ""):
    """Publica estado de fala (tts_estado.json) e registra a última frase
    no contrato do widget (widget_state.json['ultima_fala'])."""
    try:
        _atomic_write(
            ESTADO_FILE,
            {
                "falando": bool(falando),
                "texto_atual": (texto_atual or "")[:300],
                "quando": time.time(),
            },
        )
    except Exception:
        pass
    if texto_atual:
        try:
            ws = RUNTIME / "widget_state.json"
            est = {}
            if ws.exists():
                est = json.loads(ws.read_text(encoding="utf-8"))
            est["ultima_fala"] = texto_atual[:500]
            tmp = ws.with_suffix(".tmp")
            tmp.write_text(json.dumps(est, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, ws)
        except Exception:
            pass


def _speak_text(texto: str, stop_flag: Path, req_id: str) -> bool:
    global _current_req_id, _processing
    _current_req_id = req_id
    _processing = True
    volume = _ler_volume()
    t0 = time.time()
    reg = {"request_id": req_id, "texto_chars": len(texto),
           "palavras": len(texto.split()), "chunks": None,
           "cache_hit": None, "mp3_bytes": None, "duracao_s": None,
           "status": None, "erro": None}
    cache_file, cache_antes = (None, None)
    if SPEECH_AVAILABLE and _speech:
        try:
            reg["chunks"] = len(_speech._partes_para_sintese(texto))
        except Exception:
            pass
        cache_file, cache_antes = _cache_info(texto)
    try:
        ok = False
        if SPEECH_AVAILABLE and _speech:
            ok = bool(_speech.speak(texto, block=True, stop_flag=stop_flag,
                                    volume=volume))
        else:
            import subprocess
            subprocess.run(
                [sys.executable, str(VOX), "falar", texto],
                cwd=str(ROOT),
                timeout=90,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            ok = True
        reg["status"] = "ok" if ok else "interrompida"
        return ok
    except Exception as e:
        reg["status"] = "erro"
        reg["erro"] = str(e)[:200]
        _log(f"erro fala: {e}")
        return False
    finally:
        try:
            reg["duracao_s"] = round(time.time() - t0, 2)
            if cache_file is not None:
                reg["cache_hit"] = bool(cache_antes)
                if cache_file.exists():
                    reg["mp3_bytes"] = cache_file.stat().st_size
            elif reg["status"] == "ok":
                pass
        except Exception:
            pass
        _telemetrizar(reg)
        _current_req_id = None
        _processing = False


def _instancia_unica():
    """Garante apenas uma instância do tts_service rodando."""
    import psutil
    PID_FILE = RUNTIME / "tts_service.pid"
    me = str(os.getpid())
    for _ in range(2):
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Verifica se outro tts_service vivo existe
            try:
                for p in psutil.process_iter(["pid", "cmdline"]):
                    if p.info["pid"] == os.getpid():
                        continue
                    if any(
                        t.lower().strip('"').endswith("tts_service.py")
                        for t in (p.info["cmdline"] or [])
                    ):
                        os.close(fd)
                        PID_FILE.unlink()
                        return False
            except Exception:
                pass
            os.write(fd, me.encode())
            os.close(fd)
            return True
        except FileExistsError:
            dono_vivo = False
            try:
                dono = int(PID_FILE.read_text().strip())
                p = psutil.Process(dono)
                if any(t.lower().endswith("tts_service.py") for t in p.cmdline()):
                    dono_vivo = True
            except Exception:
                pass
            if dono_vivo:
                return False
            try:
                PID_FILE.unlink()
            except FileNotFoundError:
                pass
    return False


def main():
    global _paused
    # Instância única
    if not _instancia_unica():
        _log("tts_service ja esta rodando.")
        return
    # Escreve PID file para proteção contra RAM cleanup
    PID_FILE = RUNTIME / "tts_service.pid"
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    
    _log("TTS Service iniciado (singleton SpeechPipeline)")
    _log(f"  SpeechPipeline: {'OK' if SPEECH_AVAILABLE else 'fallback vox_audio'}")
    _log(f"  Comando: {CMD_FILE}")
    _log(f"  Stop flag: {STOP_FLAG}")
    _escrever_estado(False)

    last_mtime = 0
    try:
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
                                if texto and not _paused and not _pausa_total():
                                    _log(f"fala req={req_id}: {texto[:60]}...")
                                    _escrever_estado(True, texto)
                                    ok = False
                                    try:
                                        ok = _speak_text(texto, STOP_FLAG, req_id)
                                        _log(f"_speak_text returned ok={ok}")
                                    except Exception as e:
                                        _log(f"_speak_text EXCEPTION: {e}")
                                        import traceback
                                        traceback.print_exc()
                                    finally:
                                        _escrever_estado(False)
                                    _write_resp(req_id, "ok" if ok else "error")
                                    _log(f"_write_resp done for {req_id}")
                                elif _paused or _pausa_total():
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

                        if STOP_FLAG.exists():
                            try:
                                ts = float(STOP_FLAG.read_text(encoding="utf-8").strip())
                                if time.time() - ts > 2:
                                    STOP_FLAG.unlink(missing_ok=True)
                            except Exception:
                                pass

                        # Limpeza periódica de respostas TTS antigas (a cada ~60 iterações = ~3s)
                        if int(time.time()) % 3 == 0:
                            _cleanup_old_responses()

                        time.sleep(0.05)
            except KeyboardInterrupt:
                _log("Encerrando...")
                break
            except Exception as e:
                _log(f"loop error: {e}")
                time.sleep(0.5)
    finally:
        try:
            PID_FILE = RUNTIME / "tts_service.pid"
            if PID_FILE.exists() and PID_FILE.read_text().strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())