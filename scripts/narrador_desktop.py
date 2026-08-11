"""narrador_desktop.py — dá voz ao Jarvis no opencode desktop.

Vigia o banco SQLite do opencode (opencode.db) e narra em áudio (TTS via
SpeechPipeline) as respostas do assistente conforme elas são gravadas.
Roda em background; basta executar este arquivo no computador.

Recursos:
  - Lê apenas (mode=ro), não interfere no desktop.
  - Debounce: acumula texto e fala após 1,5s de pausa (evita narrar meio texto).
  - Sessões com título em --excluir não são narradas (ex.: watchdog-health).
  - Posição salva em runtime/narrador_posicao.json (continua de onde parou).
  - Controle on/off por runtime/narracao_estado.json ({"ativo": bool}); acesse
    via scripts/jarvis_audio.py on|off|status. Palavra-gatilho: "Eco" liga,
    "D Eco"/"Desativar Eco" pausa.

Uso:
  python scripts/narrador_desktop.py [--teste] [--intervalo 2] [--voz assistant]
  --teste: fala uma frase para confirmar que o áudio está funcionando e sai.
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ECOSSISTEMA_DIR = ROOT
if str(ECOSSISTEMA_DIR) not in sys.path:
    sys.path.insert(0, str(ECOSSISTEMA_DIR))

# Speech Pipeline — pipeline central de TTS
try:
    from tts import SpeechPipeline
    _speech_pipeline = SpeechPipeline()
    SPEECH_PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"[warning] SpeechPipeline não disponível: {e}")
    SPEECH_PIPELINE_AVAILABLE = False
    _speech_pipeline = None

DB = Path(os.environ.get("OPENCODE_DB", r"C:\Users\David Jr\.local\share\opencode\opencode.db"))
POSICAO = ROOT / "runtime" / "narrador_posicao.json"
CONTROLE = ROOT / "runtime" / "narracao_estado.json"
VOX = ROOT / "scripts" / "vox_audio.py"
LOG = ROOT / "scripts" / "narrador_desktop_log.txt"
EXCLUIR_PADRAO = ["watchdog-health"]
DEBOUNCE_S = 0.5
FALAR_TIMEOUT = 90


def log(msg):
    linha = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(linha, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def conectar():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    c.execute("PRAGMA query_only=ON")
    return c


def ler_posicao():
    try:
        if POSICAO.exists():
            return json.loads(POSICAO.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ultimo_ts": 0}


def salvar_posicao(pos):
    try:
        POSICAO.parent.mkdir(parents=True, exist_ok=True)
        tmp = POSICAO.with_suffix(".tmp")
        tmp.write_text(json.dumps(pos, ensure_ascii=False), encoding="utf-8")
        tmp.replace(POSICAO)
    except Exception as e:
        log(f"posicao nao salva: {e}")


def estado_ativo():
    """True se a narracao estiver ativa E não pausada.
    Formato: {"ativo": bool, "pausado": bool}. Default: ativo=true, pausado=false."""
    try:
        if CONTROLE.exists():
            estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            ativo = estado.get("ativo", True)
            pausado = estado.get("pausado", False)
            return ativo and not pausado
    except Exception:
        pass
    return True


def limpar_texto(texto):
    """Remove Markdown, emojis e simbolos especiais; fica so o texto puro para TTS."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"```.*?```", " ", texto, flags=re.DOTALL)
    texto = re.sub(r"`([^`]+)`", r"\1", texto)
    texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"(\*\*|__|~~)", "", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*\d+[.)]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"<[^>]+>", " ", texto)

    def _limpar_simbolos(c):
        if c.isspace():
            return " "
        cat = unicodedata.category(c)
        if cat in ("Cc", "Cf", "Cs", "Co", "Mn") or cat.startswith("S"):
            return " "
        return c

    texto = "".join(_limpar_simbolos(c) for c in texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def partes_novas(conn, ultimo_ts, excluir):
    """Retorna lista (ts, session_id, titulo, texto) de partes de texto novas."""
    if not DB.exists():
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT p.id, p.time_created, p.data, m.data, s.title, s.id
               FROM part p
               JOIN message m ON m.id = p.message_id
               JOIN session s ON s.id = p.session_id
               WHERE p.time_created > ? AND p.data LIKE '%"type":"text"%'
               ORDER BY p.time_created ASC LIMIT 800""",
            (ultimo_ts,),
        )
        saida = []
        for pid, ts, pdata, mdata, titulo, sid in cur.fetchall():
            try:
                p = json.loads(pdata)
                m = json.loads(mdata)
            except Exception:
                continue
            if p.get("type") != "text":
                continue
            if m.get("role") != "assistant":
                continue
            if titulo and any(x.lower() in titulo.lower() for x in excluir):
                continue
            texto = (p.get("text") or "").strip()
            if not texto:
                continue
            saida.append((ts or 0, sid, titulo or "", texto))
        return saida
    except Exception as e:
        log(f"erro lendo banco: {e}")
        return []


class Narrador:
    def __init__(self, voz):
        self.voz = voz
        self.buffer = []
        self.timer = None
        self.lock = threading.Lock()
        self.falando = threading.Lock()
        self.buffer_lock = threading.Lock()

    def alimentar(self, textos):
        with self.buffer_lock:
            self.buffer.extend(textos)
        if self.timer is None:
            self.timer = threading.Timer(DEBOUNCE_S, self._flush)
            self.timer.daemon = True
            self.timer.start()

    def _flush(self):
        with self.buffer_lock:
            textos = self.buffer
            self.buffer = []
        self.timer = None
        texto = " ".join(textos).strip()
        texto = limpar_texto(texto)
        if len(texto) < 15:
            return
        with self.falando:
            log(f"falando ({len(texto)} chars): {texto[:70]}...")
            try:
                # Tenta usar SpeechPipeline primeiro
                if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
                    try:
                        _speech_pipeline.speak(texto, block=True)
                        return
                    except Exception as e:
                        log(f"SpeechPipeline falhou: {e}")

                # Fallback: usa vox_audio.py
                subprocess.run([sys.executable, str(VOX), "falar", texto],
                               cwd=str(ROOT), timeout=FALAR_TIMEOUT, check=False,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception as e:
                log(f"falha de voz: {e}")

    def parar(self):
        if self.timer:
            self.timer.cancel()


def teste_audio():
    log("teste de audio")
    texto_teste = "Teste de voz do Jarvis. Estou ouvindo."
    try:
        # Tenta usar SpeechPipeline primeiro
        if SPEECH_PIPELINE_AVAILABLE and _speech_pipeline:
            try:
                _speech_pipeline.speak(texto_teste, block=True)
                print("OK: audio reproduzido via SpeechPipeline.")
                return 0
            except Exception as e:
                log(f"SpeechPipeline falhou: {e}")

        # Fallback: usa vox_audio.py
        subprocess.run([sys.executable, str(VOX), "falar", texto_teste],
                       cwd=str(ROOT), timeout=FALAR_TIMEOUT, check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        print("OK: audio reproduzido. Se voce nao ouviu, verifique o som do PC.")
    except Exception as e:
        print(f"ERRO no teste de audio: {e}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Narrador de voz do Jarvis no opencode desktop")
    ap.add_argument("--teste", action="store_true", help="fala uma frase de teste e sai")
    ap.add_argument("--intervalo", type=float, default=0.5, help="segundos entre leituras do banco")
    ap.add_argument("--voz", choices=["assistant", "user", "ambos"], default="assistant",
                    help="quem narrar (padrao: assistant)")
    ap.add_argument("--excluir", default=",".join(EXCLUIR_PADRAO),
                    help="substrings de titulos de sessao a ignorar (separadas por virgula)")
    args = ap.parse_args()
    if args.teste:
        return teste_audio()
    excluir = [x.strip().lower() for x in args.excluir.split(",") if x.strip()]
    pos = ler_posicao()
    narrador = Narrador(args.voz)
    log(f"narrador iniciado (banco={DB.name}, intervalo={args.intervalo}s, voz={args.voz}, exclui={excluir})")
    ultimo_ts = pos.get("ultimo_ts", 0)
    conn = conectar()
    estado_logado = None
    try:
        while True:
            ativo = estado_ativo()
            if ativo != estado_logado:
                estado_logado = ativo
                if ativo:
                    log("narracao ATIVADA (AT ECO)")
                else:
                    # Distingue entre pausado e desativado lendo o estado completo
                    try:
                        if CONTROLE.exists():
                            estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                            if estado.get("ativo", True) and estado.get("pausado", False):
                                log("narracao PAUSADA (PS ECO)")
                            else:
                                log("narracao DESATIVADA (DT ECO)")
                        else:
                            log("narracao DESATIVADA (DT ECO)")
                    except Exception:
                        log("narracao PAUSADA (PS ECO)")
            novas = partes_novas(conn, ultimo_ts, excluir)
            if novas:
                textos = [t for _, _, _, t in novas]
                if ativo:
                    narrador.alimentar(textos)
                ultimo_ts = max(x[0] for x in novas)
                salvar_posicao({"ultimo_ts": ultimo_ts})
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        log("narrador encerrado")
    finally:
        narrador.parar()
        try:
            conn.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
