#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edge — widget flutuante do EcoSystemUmGrau (pywebview).

Bolinhas de status refletem serviços reais:
  narr   -> narrador_desktop rodando (psutil)
  tts    -> tts_service rodando (psutil)
  bridge -> porta 8765 escutando

Controles:
  Volume  -> grava "volume" em runtime/widget_state.json (lido por tts_service/jarvis_bridge)
  Sono    -> desliga o modo voz após N minutos
  Voz     -> liga/desliga dialogo.py --modo vad (padrão do ecossistema)
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
RUNTIME = BASE / "runtime"
UI = BASE / "www" / "index.html"
STATE_FILE = RUNTIME / "widget_state.json"
PID_FILE = RUNTIME / "widget.pid"
STOP_FLAG = RUNTIME / "parar_fala.flag"
BRIDGE_PORT = 8765


def ler_estado():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def salvar_estado(update):
    estado = ler_estado()
    estado.update(update)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, STATE_FILE)


def servico_no_ar(frag, excluir=None):
    """Verdadeiro se algum processo tem FRAG como script na cmdline.
    Casamento por token terminando em FRAG (evita falsos positivos com
    wrappers tipo `python -c "...widget_edge..."`)."""
    import psutil

    alvo = frag.lower()
    if not alvo.endswith(".py"):
        alvo += ".py"
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            if excluir is not None and p.info["pid"] == excluir:
                continue
            for tok in p.info["cmdline"] or []:
                if tok.lower().strip('"').endswith(alvo):
                    return True
        except Exception:
            pass
    return False


def bridge_no_ar():
    s = socket.socket()
    s.settimeout(0.4)
    try:
        return s.connect_ex(("127.0.0.1", BRIDGE_PORT)) == 0
    except Exception:
        return False
    finally:
        s.close()


def ler_estado_voz():
    """(ativo, pausado) — fonte única: runtime/narracao_estado.json."""
    try:
        d = json.loads((RUNTIME / "narracao_estado.json").read_text(encoding="utf-8"))
        return bool(d.get("ativo", False)), bool(d.get("pausado", False))
    except Exception:
        return False, False


def ultima_fala():
    """Última frase falada, se registrada em widget_state.json ('ultima_fala')."""
    return ler_estado().get("ultima_fala") or None


def ler_tts_estado():
    """(falando, texto_atual) — fonte única: runtime/tts_estado.json."""
    try:
        d = json.loads((RUNTIME / "tts_estado.json").read_text(encoding="utf-8"))
        return bool(d.get("falando", False)), str(d.get("texto_atual", "") or "")
    except Exception:
        return False, ""


def ler_retrato():
    """Retrato vivo do diálogo ({estado, voce, rms, erro, quando}).
    Voz desligada ou retrato velho (>12s) = parado."""
    try:
        return json.loads(
            (RUNTIME / "dialogo_vivo.json").read_text(encoding="utf-8")
        )
    except Exception:
        return {}


class EdgeApi:
    """API exposta ao JavaScript via pywebview (window.pywebview.api)."""

    def __init__(self):
        self._voz_proc = None
        self._sono_timer = None
        self._lock = threading.Lock()

    def voz_ligada(self):
        with self._lock:
            return self._voz_proc is not None and self._voz_proc.poll() is None

    def status(self):
        with self._lock:
            voz = self._voz_proc is not None and self._voz_proc.poll() is None
        est = ler_estado()
        falando, texto = ler_tts_estado()
        vivo = ler_retrato()
        if not voz or (time.time() - float(vivo.get("quando", 0)) > 12):
            vivo = {"estado": "parado"}
        else:
            vivo.pop("quando", None)
        return {
            "narr": servico_no_ar("narrador_desktop"),
            "tts": servico_no_ar("tts_service"),
            "bridge": bridge_no_ar(),
            "voz": voz,
            "volume": int(est.get("volume", 80)),
            "sleep": int(est.get("sleep", 0)),
            "falando": falando,
            "texto": texto,
            "ultima_fala": est.get("ultima_fala") or "",
            "vivo": vivo,
        }

    def parar(self):
        """Interrompe a fala corrente: grava a bandeira direto (o serviço de
        voz checa durante a síntese, mesmo com a fila ocupada)."""
        try:
            STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        return True

    def set_volume(self, valor):
        salvar_estado({"volume": max(0, min(100, int(valor)))})
        return True

    def set_sleep(self, minutos):
        minutos = int(minutos)
        salvar_estado({"sleep": minutos})
        if self._sono_timer is not None:
            self._sono_timer.cancel()
            self._sono_timer = None
        if minutos > 0:
            t = threading.Timer(minutos * 60, self._expirar_sono)
            t.daemon = True
            t.start()
            self._sono_timer = t
        return True

    def _expirar_sono(self):
        self.voice_off()

    def voice_on(self):
        with self._lock:
            if self._voz_proc and self._voz_proc.poll() is None:
                return True
            exe = sys.executable
            alvo = exe.replace("python.exe", "pythonw.exe")
            if os.path.exists(alvo):
                exe = alvo
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            log_f = open(RUNTIME / "dialogo_widget.log", "a", buffering=1,
                         encoding="utf-8")
            try:
                log_f.write(time.strftime("[%Y-%m-%d %H:%M:%S] spawn dialogo\n"))
            except Exception:
                pass
            self._voz_proc = subprocess.Popen(
                [exe, "-u", str(SCRIPTS / "dialogo.py"), "--modo", "vad"],
                cwd=str(SCRIPTS),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
        return True

    def voice_off(self):
        with self._lock:
            if self._voz_proc and self._voz_proc.poll() is None:
                try:
                    self._voz_proc.terminate()
                except Exception:
                    pass
            self._voz_proc = None
        return True

    def voice_toggle(self):
        with self._lock:
            ligada = self._voz_proc is not None and self._voz_proc.poll() is None
        if ligada:
            self.voice_off()
            return {"voz": False}
        self.voice_on()
        return {"voz": True}

    def minimize(self):
        import webview

        if webview.windows:
            webview.windows[0].minimize()
        return True

    def close(self):
        import webview

        if webview.windows:
            webview.windows[0].destroy()
        return True


def instancia_unica():
    """Trava atômica: o próprio widget.pid é criado com O_EXCL.

    Só um processo consegue criá-lo. Se já existe, verifica se o dono
    está vivo e é o widget; se não, o arquivo está obsoleto e pode ser
    reciclado (uma única retentativa).
    """
    import psutil

    me = str(os.getpid())
    for _ in range(2):
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Defesa extra: se outro widget_edge VIVO existe mesmo sem arquivo
            # (trava apagada por agente externo), não somos o dono verdadeiro.
            try:
                for p in psutil.process_iter(["pid", "cmdline"]):
                    if p.info["pid"] == os.getpid():
                        continue
                    if any(
                        t.lower().strip('"').endswith("widget_edge.py")
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
                if any(t.lower().endswith("widget_edge.py") for t in p.cmdline()):
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


def poller(api):
    import webview

    ultima = None
    while True:
        # voz ligada pede ritmo maior (barra de mic e estados ao vivo)
        time.sleep(1 if api.voz_ligada() else 2)
        try:
            st = api.status()
            chave = json.dumps(st, sort_keys=True)
            if chave != ultima and webview.windows:
                ultima = chave
                webview.windows[0].evaluate_js(
                    "window.edgeAtualizar && edgeAtualizar(" + json.dumps(st) + ")"
                )
        except Exception:
            pass


def _posicao_inferior_esquerda(largura, altura):
    """(x, y) para nascer no canto inferior esquerdo da área útil
    (respeita a barra de tarefas via SPI_GETWORKAREA)."""
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        rc = RECT()
        ok = ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rc), 0)
        if ok:
            x = rc.left + 8
            y = max(rc.top, rc.bottom - altura - 8)
            return int(x), int(y)
    except Exception:
        pass
    try:
        import ctypes

        u = ctypes.windll.user32
        return 8, max(0, u.GetSystemMetrics(1) - altura - 56)
    except Exception:
        return 8, 8


def main():
    # Telemetria: sob pythonw as streams sao None; qualquer print interno
    # de biblioteca derruba o processo. Redireciona e habilita faulthandler.
    if sys.stdout is None or sys.stderr is None:
        f = open(RUNTIME / "widget_edge.log", "a", buffering=1, encoding="utf-8")
        sys.stdout = f
        sys.stderr = f

    import faulthandler

    faulthandler.enable(file=sys.stderr)
    print(time.strftime("[%Y-%m-%d %H:%M:%S] boot"), flush=True)

    if not instancia_unica():
        print("Edge ja esta rodando.", flush=True)
        return
    print("trava ok", flush=True)

    import webview

    api = EdgeApi()
    px, py = _posicao_inferior_esquerda(360, 300)
    print(f"posicao inicial: {px},{py}", flush=True)
    webview.create_window(
        "Edge",
        str(UI),
        js_api=api,
        x=px,
        y=py,
        width=360,
        height=300,
        frameless=True,
        easy_drag=True,
        on_top=True,
        focus=False,
        background_color="#1e1e2e",
    )
    print("janela criada", flush=True)

    threading.Thread(target=poller, args=(api,), daemon=True).start()
    try:
        webview.start()
    finally:
        api.voice_off()
        try:
            if PID_FILE.read_text().strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass
    print("encerrado", flush=True)


if __name__ == "__main__":
    main()
