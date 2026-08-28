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
import hashlib
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

# Dedup COMPARTILHADO em disco (evita que narrador_desktop e widget_edge
# falem a mesma resposta 2x — cada processo tinha seu _FALADOS em memória).
try:
    from narrador_dedup import ja_falado
except ImportError:
    def ja_falado(texto_hash):
        return False

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
# Dedup: textos falados recentemente (hash -> timestamp) para evitar falar o mesmo texto duas vezes
_FALADOS: dict = {}  # hash -> time.time()
_FALADOS_TTL = 120  # segundos — textos idênticos são ignorados por 2 min


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


# Termos técnicos que poluem a fala — removidos ou substituídos
# Foco: extensões de arquivo e caminhos, NÃO palavras normais do português
_EXTensoes = re.compile(
    r"\.(?:py|js|ts|json|jsonc|md|html|css|yaml|yml|toml|cfg|ini|sh|ps1|bat|cmd|"
    r"exe|dll|so|jar|apk|aab|zip|tar|gz|bak|tmp|log|db|sqlite|csv|xml|env|"
    r"mp3|wav|ogg|mp4|mkv|avi|mov|pdf|png|jpg|jpeg|gif|svg|ico|webp|"
    r"pyc|pyo|whl|egg|cab|msi|deb|rpm|dmg|iso|img|bin|dat|old|new|orig|"
    r"save|swp|swo|swn|temp|cache)\b",
    re.IGNORECASE,
)

# Caminhos do Windows/Linux (ex: C:\Users\..., /scripts/, ~/...)
_Caminhos = re.compile(
    r"[A-Z]:\\[\w\\. -]+"
    r"|(?:/scripts|/usr|/etc|/var|/tmp|/home|/root|~/)[\w/._ -]*",
    re.IGNORECASE,
)

# Nomes de arquivos com extensão (ex: narrator_desktop.py, tts_service.py)
_Arquivos = re.compile(r"\b\w+\.(?:py|js|ts|json|jsonc|md|html|css|ps1|bat|sh)\b", re.IGNORECASE)


def simplificar_para_fala(texto):
    """Remove termos técnicos e simplifica texto para fala natural."""
    if not texto:
        return ""
    # Remove extensões de arquivo isoladas (ex: ".py" no final de palavras)
    texto = _EXTensoes.sub("", texto)
    # Remove caminhos completos
    texto = _Caminhos.sub(" ", texto)
    # Remove nomes de arquivos técnicos (ex: "narrador_desktop")
    texto = _Arquivos.sub(" ", texto)
    # Limpa pontuação solta e espaços extras
    texto = re.sub(r"[,;:]\s*[)\]]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = texto.strip()
    # Se muito longo, pega só as primeiras 2 frases
    if len(texto) > 200:
        frases = re.split(r"(?<=[.!?])\s+", texto)
        texto = " ".join(frases[:2])
    return texto


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
        texto = simplificar_para_fala(texto)
        # Bloqueia texto em inglês — narrador só fala português
        if IDIOMA_AVAILABLE and len(texto) > 30:
            resultado = validar_idioma(texto, threshold=5.0)
            if not resultado["ok"]:
                log(f"BLOQUEADO (idioma={resultado['idioma']}, score={resultado['score']}): {texto[:60]}...")
                return
        # Dedup: ignora texto idêntico falado nos últimos _FALADOS_TTL segundos
        texto_hash = hashlib.md5(texto.encode("utf-8")).hexdigest()[:16]
        agora = time.time()
        # Limpa hashes expirados
        expirados = [k for k, t in _FALADOS.items() if agora - t > _FALADOS_TTL]
        for k in expirados:
            _FALADOS.pop(k, None)
        if texto_hash in _FALADOS:
            log(f"DEDUP pulando texto repetido: {texto[:60]}...")
            return
        _FALADOS[texto_hash] = agora
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


def _widget_rodando():
    """True se o widget_edge (fonte única do narrador) está rodando."""
    import psutil
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(p.cmdline() or []).lower()
            if "widget_edge.py" in cmd:
                return True
        except Exception:
            pass
    return False


def _iniciar_widget():
    """Inicia o widget_edge silenciosamente (pythonw, sem janela)."""
    import subprocess
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    try:
        proc = subprocess.Popen(
            [pyw, str(ROOT / "scripts" / "widget_edge.py")],
            cwd=str(ROOT),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        return True
    except Exception as e:
        log(f"falha ao iniciar widget: {e}")
        return False


def main():
    """Fonte única do narrador: o widget_edge.py (thread _narrador_loop).

    Este script NUNCA narra em paralelo. Ele apenas garante que o widget
    esteja rodando (com o narrador integrado). Se o widget já está ativo,
    apenas atualiza o controle de narração e sai. Sem duplicidade.
    """
    ap = argparse.ArgumentParser(description="Guarantees o narrador único (widget_edge) do opencode desktop")
    ap.add_argument("--teste", action="store_true", help="fala uma frase de teste e sai")
    args = ap.parse_args()
    if args.teste:
        return teste_audio()
    if _widget_rodando():
        log("narrador único já ativo (widget_edge) - nada a fazer")
        return 0
    log("widget_edge ausente - iniciando narrador único")
    return 0 if _iniciar_widget() else 1


if __name__ == "__main__":
    sys.exit(main())
