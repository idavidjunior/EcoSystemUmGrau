"""narrador_desktop.py — dá voz ao Jarvis no opencode desktop.

Vigia o banco SQLite do opencode (opencode.db) e narra em áudio (TTS via
tts_service.py) as respostas do assistente conforme elas são gravadas.
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
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ECOSSISTEMA_DIR = ROOT
if str(ECOSSISTEMA_DIR) not in sys.path:
    sys.path.insert(0, str(ECOSSISTEMA_DIR))

# Detecção automática de palavras em inglês para pronúncia correta
try:
    from detect_english_words import pipeline_completo_tts
    ENGLISH_DETECT_AVAILABLE = True
except ImportError as e:
    print(f"[warning] detect_english_words não disponível: {e}")
    ENGLISH_DETECT_AVAILABLE = False
    def pipeline_completo_tts(texto):
        return texto

# Validação de idioma — narrador só fala português
try:
    from validar_idioma import validar_idioma
    IDIOMA_AVAILABLE = True
except ImportError as e:
    print(f"[warning] validar_idioma não disponível: {e}")
    IDIOMA_AVAILABLE = False
    def validar_idioma(texto, threshold=30.0):
        return {"ok": True, "score": 100, "idioma": "pt-BR"}

# Perfil do usuário para formatação de resposta
try:
    from scripts.profile_hook import format_response_for_profile, get_response_config
    _profile_config = get_response_config()
    PROFILE_HOOK_AVAILABLE = True
except ImportError as e:
    print(f"[warning] profile_hook não disponível: {e}")
    _profile_config = {}
    PROFILE_HOOK_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}

DB = Path(os.environ.get("OPENCODE_DB", r"C:\Users\David Jr\.local\share\opencode\opencode.db"))
POSICAO = ROOT / "runtime" / "narrador_posicao.json"
CONTROLE = ROOT / "runtime" / "narracao_estado.json"
VOX = ROOT / "scripts" / "vox_audio.py"
LOG = ROOT / "scripts" / "narrador_desktop_log.txt"
PARAR_FALA = ROOT / "runtime" / "parar_fala.flag"
TTS_CMD = ROOT / "runtime" / "tts_cmd.json"
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


def _enviar_tts_cmd(cmd: dict):
    """Envia comando de voz ao tts_service com escrita atômica resiliente a lock (WinError 5)."""
    TTS_CMD.parent.mkdir(parents=True, exist_ok=True)
    tmp = TTS_CMD.with_suffix(".tmp")
    tmp.write_text(json.dumps(cmd, ensure_ascii=False), encoding="utf-8")
    for _ in range(6):
        try:
            tmp.replace(TTS_CMD)
            return
        except OSError:
            time.sleep(0.15)
    try:
        tmp.replace(TTS_CMD)
    except OSError as e:
        log(f"falha de voz: {e}")


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
    import time
    for tentativa in range(3):
        try:
            POSICAO.parent.mkdir(parents=True, exist_ok=True)
            tmp = POSICAO.with_suffix(".tmp")
            tmp.write_text(json.dumps(pos, ensure_ascii=False), encoding="utf-8")
            tmp.replace(POSICAO)
            return
        except PermissionError:
            if tentativa < 2:
                time.sleep(0.1)
            else:
                log(f"posição não salva após 3 tentativas")
        except Exception as e:
            log(f"posição não salva: {e}")
            return


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
    """Retorna lista (ts, session_id, titulo, texto) de partes de texto novas.

    Apenas texto final de mensagens COMPLETAS (com step-finish).
    Ignora reasoning, tool calls, updates intermediários e pensamento interno.
    """
    if not DB.exists():
        return []
    try:
        cur = conn.cursor()
        # Busca apenas text parts de mensagens que já foram FINALIZADAS (step-finish)
        cur.execute(
            """SELECT p.id, p.time_created, p.data, m.data, s.title, s.id
               FROM part p
               JOIN message m ON m.id = p.message_id
               JOIN session s ON s.id = p.session_id
               WHERE p.time_created > ? AND p.data LIKE '%"type":"text"%'
               AND EXISTS (
                   SELECT 1 FROM part pf
                   WHERE pf.message_id = m.id AND pf.data LIKE '%"type":"step-finish"%'
               )
               ORDER BY p.time_created ASC LIMIT 800""",
            (ultimo_ts,),
        )
        saida = []
        # Agrupa por mensagem para pegar só o ÚLTIMO texto de cada uma
        por_msg = {}
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
            texto = (p.get("text") or "").strip()
            if not texto:
                continue
            msg_id = m.get("id", pid)
            # Guarda apenas o último texto por mensagem
            por_msg[msg_id] = (ts or 0, sid, titulo or "", texto)

        # Filtra por exclusão e monta saída
        for ts, sid, titulo, texto in por_msg.values():
            if titulo and any(x.lower() in titulo.lower() for x in excluir):
                continue
            saida.append((ts, sid, titulo, texto))
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
        # Bloqueia texto em inglês — narrador só fala português
        if IDIOMA_AVAILABLE and len(texto) > 30:
            resultado = validar_idioma(texto, threshold=5.0)
            if not resultado["ok"]:
                log(f"BLOQUEADO (idioma={resultado['idioma']}, score={resultado['score']}): {texto[:60]}...")
                return
        # Verifica parar_fala.flag — se ativo, não fala
        if PARAR_FALA.exists():
            log("pulando fala (parar_fala.flag ativo)")
            return
        # Pré-processa: detecta palavras em inglês e aplica SSML para pronúncia correta
        texto = pipeline_completo_tts(texto)
        # Aplica preferências do perfil do usuário (remove markdown, tabelas, etc.)
        if PROFILE_HOOK_AVAILABLE:
            texto = format_response_for_profile(texto, _profile_config)
        if len(texto) < 15:
            return
        with self.falando:
            log(f"falando ({len(texto)} chars): {texto[:70]}...")
            try:
                # Envia para tts_service.py (único processo de TTS)
                req_id = str(uuid.uuid4())[:8]
                cmd = {"cmd": "speak", "texto": texto, "request_id": req_id, "priority": 0}
                _enviar_tts_cmd(cmd)
                # Aguarda resposta (polling simples) — checa parar_fala a cada tick
                resp_file = ROOT / "runtime" / f"tts_resp_{req_id}.json"
                try:
                    for _ in range(1800):  # timeout ~90s
                        if PARAR_FALA.exists():
                            log("interrompido (parar_fala.flag detectado durante fala)")
                            break
                        if resp_file.exists():
                            content = resp_file.read_text(encoding="utf-8")
                            if content and content.strip():
                                try:
                                    resp = json.loads(content)
                                    if resp.get("status") != "ok":
                                        log(f"TTS service erro: {resp.get('msg')}")
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            break
                        time.sleep(0.05)
                finally:
                    resp_file.unlink(missing_ok=True)
            except Exception as e:
                log(f"falha de voz: {e}")

    def parar(self):
        if self.timer:
            self.timer.cancel()


def teste_audio():
    log("teste de audio")
    texto_teste = "Teste de voz do Jarvis. Estou ouvindo."
    # Aplica pipeline de pronúncia no teste também
    texto_teste = pipeline_completo_tts(texto_teste)
    # Aplica preferências do perfil
    if PROFILE_HOOK_AVAILABLE:
        texto_teste = format_response_for_profile(texto_teste, _profile_config)
    try:
        # Envia para tts_service.py
        req_id = "teste"
        cmd = {"cmd": "speak", "texto": texto_teste, "request_id": req_id, "priority": 0}
        _enviar_tts_cmd(cmd)
        # Aguarda resposta
        resp_file = ROOT / "runtime" / f"tts_resp_{req_id}.json"
        try:
            for _ in range(1800):
                if resp_file.exists():
                    content = resp_file.read_text(encoding="utf-8")
                    if content and content.strip():
                        try:
                            resp = json.loads(content)
                            if resp.get("status") == "ok":
                                print("OK: audio reproduzido via TTS Service.")
                            else:
                                print(f"ERRO: {resp.get('msg')}")
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return 0
                time.sleep(0.05)
            print("TIMEOUT: TTS Service não respondeu")
        finally:
            resp_file.unlink(missing_ok=True)
    except Exception as e:
        print(f"ERRO no teste de audio: {e}")
    return 0


def main():
    # Previne instâncias múltiplas
    pid_file = ROOT / "runtime" / "narrador.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            import psutil
            if psutil.pid_exists(old_pid):
                # Não sair se for o próprio PID (race condition guardian -> narrador)
                if old_pid == os.getpid():
                    log(f"PID file já contém nosso PID ({old_pid}) - continuando")
                else:
                    p = psutil.Process(old_pid)
                    cmd = " ".join(p.cmdline()).lower()
                    if "narrador_desktop" in cmd:
                        log(f"instância duplicada detectada (PID {old_pid}) - saindo")
                        return
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    pid_file.write_text(str(os.getpid()))

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
                # Se parar_fala.flag ativo, descarta buffer e não fala
                if PARAR_FALA.exists():
                    narrador.parar()
                    log("buffer descartado (parar_fala.flag ativo)")
                elif ativo:
                    narrador.alimentar(textos)
                ultimo_ts = max(x[0] for x in novas)
                salvar_posicao({"ultimo_ts": ultimo_ts})
            # Re-lê posição do disco periodicamente (widget pode ter resetado)
            try:
                pos_now = ler_posicao()
                ts_now = pos_now.get("ultimo_ts", 0)
                if ts_now > ultimo_ts:
                    ultimo_ts = ts_now
                    narrador.parar()  # descarta buffer obsoleto
                    narrador = Narrador(args.voz)
            except Exception:
                pass
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        log("narrador encerrado")
    finally:
        narrador.parar()
        try:
            conn.close()
        except Exception:
            pass
        # Limpa PID file
        try:
            pid_file = ROOT / "runtime" / "narrador.pid"
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
