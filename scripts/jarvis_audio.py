"""jarvis_audio.py — controle padrão de narração do ecossistema.

Palavras-gatilho OFICIAIS (padrão único do ecossistema):
  AT ECO    -> on   (ativa narração)
  DT ECO    -> off  (desativa narração)
  PS ECO    -> pause (pausa narração - mantém processo, só para de falar)
  STOP ECO  -> stop  (interrompe fala atual + pausa)

Legados (ainda funcionam, mas depreciados):
  "Eco" / "ativar"      -> on
  "D Eco" / "desativar" -> off
  "Para" / "Cala"       -> stop

Mecanismo: grava runtime/narracao_estado.json ({"ativo": bool, "pausado": bool}).
O narrador (scripts/narrador_desktop.py) lê esse arquivo a cada loop.
"on" garante que o processo do narrador esteja rodando.
"stop" mata o subprocesso TTS ativo (vox_audio.py falar) imediatamente.

Uso:
  python scripts/jarvis_audio.py on|off|pause|stop|status
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROLE = ROOT / "runtime" / "narracao_estado.json"
PID_FILE = ROOT / "runtime" / "narrador.pid"
NARRADOR = ROOT / "scripts" / "narrador_desktop.py"
VOX = ROOT / "scripts" / "vox_audio.py"


def gravar(ativo=None, pausado=None):
    """Grava estado de narração. ativo=True/False, pausado=True/False.
    Se ambos None, não altera. Mantém compatibilidade: gravar(True) -> ativo=True, pausado=False."""
    try:
        estado = {"ativo": True, "pausado": False}
        if CONTROLE.exists():
            try:
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            except Exception:
                pass
        if ativo is not None:
            estado["ativo"] = bool(ativo)
        if pausado is not None:
            estado["pausado"] = bool(pausado)
        # Compat: se ativo=False, pausado=True implícito
        if ativo is False and pausado is None:
            estado["pausado"] = True
        CONTROLE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTROLE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado), encoding="utf-8")
        tmp.replace(CONTROLE)
    except Exception as e:
        print(f"ERRO ao gravar controle: {e}")
        return False
    return True


def estado_atual():
    """Retorna (ativo, pausado) do controle."""
    try:
        if CONTROLE.exists():
            d = json.loads(CONTROLE.read_text(encoding="utf-8"))
            return d.get("ativo", True), d.get("pausado", False)
    except Exception:
        pass
    return True, False


def _widget_rodando():
    """Fonte única do narrador: o widget_edge.py (narrador integrado)."""
    try:
        saida = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"name='python.exe' or name='pythonw.exe'\" | "
             "Where-Object { $_.CommandLine -match 'widget_edge' } | Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, timeout=20,
        ).stdout.strip()
        return saida.isdigit() and int(saida) > 0
    except Exception:
        pass
    return False


def narrador_rodando():
    """Narrador ativo = widget_edge rodando (fonte única) OU PID file válido."""
    if _widget_rodando():
        return True
    try:
        if PID_FILE.exists():
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            saida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                   capture_output=True, text=True, timeout=20).stdout
            if str(pid) in saida:
                return True
            else:
                # PID stale: processo morreu, limpar arquivo
                PID_FILE.unlink(missing_ok=True)
        return False
    except (ValueError, FileNotFoundError):
        # PID inválido no arquivo: limpar e tratar como não-rodando
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def iniciar_narrador():
    """Garante o narrador único. narrador_desktop.py é agora um guard:
    se o widget (fonte única) já roda, não faz nada; se não, inicia o widget."""
    if narrador_rodando():
        return True
    try:
        DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0)
        # pythonw.exe para não abrir janela de terminal
        pyw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pyw):
            pyw = sys.executable
        proc = subprocess.Popen(
            [pyw, str(NARRADOR)],
            cwd=str(ROOT), creationflags=DETACHED | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        PID_FILE.write_text(str(proc.pid), encoding="utf-8")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"ERRO ao iniciar narrador: {e}")
        return False


def cmd_on():
    if not gravar(ativo=True, pausado=False):
        return 1
    ok = iniciar_narrador()
    print("Narracao ATIVADA (AT ECO)." + ("" if ok else " (processo nao confirmado)"))
    return 0


def cmd_off():
    if not gravar(ativo=False, pausado=True):
        return 1
    print("Narracao DESATIVADA (DT ECO).")
    return 0


def cmd_pause():
    """Pausa narração (mantém processo vivo, só para de falar)."""
    if not gravar(pausado=True):
        return 1
    print("Narracao PAUSADA (PS ECO).")
    return 0


def cmd_status():
    ativo, pausado = estado_atual()
    if ativo and not pausado:
        estado = "ATIVA"
    elif ativo and pausado:
        estado = "PAUSADA"
    else:
        estado = "DESATIVADA"
    print(f"narracao: {estado} | processo narrador: {'rodando' if narrador_rodando() else 'parado'}")
    return 0


def matar_tts_ativo():
    """Mata qualquer processo python rodando vox_audio.py falar."""
    try:
        saida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/NH"],
                               capture_output=True, text=True, timeout=20).stdout
        pids = []
        for linha in saida.splitlines():
            if "vox_audio.py" in linha and "falar" in linha:
                partes = linha.split()
                if len(partes) >= 2 and partes[1].isdigit():
                    pids.append(int(partes[1]))
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
                print(f"TTS interrompido (PID {pid})")
            except Exception:
                pass
        if not pids:
            print("Nenhum TTS ativo encontrado")
    except Exception as e:
        print(f"Erro ao interromper TTS: {e}")


def cmd_stop():
    """Interrompe fala atual SEM desativar o narrador.
    Escreve parar_fala.flag (narrador/tts_service checam durante fala)
    e mata qualquer subprocesso TTS ativo. NÃO altera narracao_estado.json."""
    stop_flag = ROOT / "runtime" / "parar_fala.flag"
    try:
        stop_flag.write_text(str(int(time.time())), encoding="utf-8")
    except Exception:
        pass
    matar_tts_ativo()
    print("Fala interrompida. Narrador continua ativo.")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("on", "off", "pause", "status", "stop"):
        print(__doc__)
        return 1
    return {"on": cmd_on, "off": cmd_off, "pause": cmd_pause, "status": cmd_status, "stop": cmd_stop}[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
