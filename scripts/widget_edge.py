#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edge — widget flutuante do EcoSystemUmGrau (pywebview).

Bolinhas de status refletem serviços reais:
  narr   -> narrador integrado ativo (narracao_estado.json)
  tts    -> tts_service rodando (psutil)
  bridge -> porta 8765 escutando

Controles:
  Volume  -> grava "volume" em runtime/widget_state.json (lido por tts_service/jarvis_bridge)
  Sono    -> desliga o modo voz após N minutos
  Voz     -> liga/desliga dialogo.py --modo vad (padrão do ecossistema)
"""

import hashlib
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
RUNTIME = BASE / "runtime"
UI = BASE / "www" / "index.html"
STATE_FILE = RUNTIME / "widget_state.json"
PID_FILE = RUNTIME / "widget.pid"
STOP_FLAG = RUNTIME / "parar_fala.flag"
BRIDGE_PORT = 8765
NARRACAO_CONTROLE = RUNTIME / "narracao_estado.json"

# --- Narrador integrado ---
DB_NARRADOR = Path(os.environ.get("OPENCODE_DB", r"C:\Users\David Jr\.local\share\opencode\opencode.db"))
POSICAO_NARRADOR = RUNTIME / "narrador_posicao.json"
TTS_CMD = RUNTIME / "tts_cmd.json"
NARR_LOG = SCRIPTS / "narrador_desktop_log.txt"
EXCLUIR_PADRAO = ["watchdog-health"]
DEBOUNCE_S = 0.5
_FALADOS: dict = {}
_FALADOS_TTL = 120

# Detecção de palavras em inglês para pronúncia correta
try:
    from detect_english_words import pipeline_completo_tts
    ENGLISH_DETECT_AVAILABLE = True
except ImportError:
    ENGLISH_DETECT_AVAILABLE = False
    def pipeline_completo_tts(texto):
        return texto

# Validação de idioma — narrador só fala português
try:
    from validar_idioma import validar_idioma
    IDIOMA_AVAILABLE = True
except ImportError:
    IDIOMA_AVAILABLE = False
    def validar_idioma(texto, threshold=30.0):
        return {"ok": True, "score": 100, "idioma": "pt-BR"}

# Perfil do usuário para formatação de resposta
try:
    from scripts.profile_hook import format_response_for_profile, get_response_config
    _profile_config = get_response_config()
    PROFILE_HOOK_AVAILABLE = True
except ImportError:
    _profile_config = {}
    PROFILE_HOOK_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}

# Regex para limpeza de texto para fala
_EXTensoes = re.compile(
    r"\.(?:py|js|ts|json|jsonc|md|html|css|yaml|yml|toml|cfg|ini|sh|ps1|bat|cmd|"
    r"exe|dll|so|jar|apk|aab|zip|tar|gz|bak|tmp|log|db|sqlite|csv|xml|env|"
    r"mp3|wav|ogg|mp4|mkv|avi|mov|pdf|png|jpg|jpeg|gif|svg|ico|webp|"
    r"pyc|pyo|whl|egg|cab|msi|deb|rpm|dmg|iso|img|bin|dat|old|new|orig|"
    r"save|swp|swo|swn|temp|cache)\b",
    re.IGNORECASE,
)
_Caminhos = re.compile(
    r"[A-Z]:\\[\w\\. -]+"
    r"|(?:/scripts|/usr|/etc|/var|/tmp|/home|/root|~/)[\w/._ -]*",
    re.IGNORECASE,
)
_Arquivos = re.compile(r"\b\w+\.(?:py|js|ts|json|jsonc|md|html|css|ps1|bat|sh)\b", re.IGNORECASE)


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


# ---------------------------------------------------------------------------
# Narrador integrado — funções transplantadas de narrador_desktop.py
# ---------------------------------------------------------------------------

def _log_narr(msg):
    linha = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    try:
        with open(NARR_LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def _enviar_tts_cmd(cmd: dict):
    """Envia comando de voz ao tts_service com escrita atômica resiliente a lock."""
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
        _log_narr(f"falha de voz: {e}")


def _conectar_narrador():
    c = sqlite3.connect(f"file:{DB_NARRADOR}?mode=ro", uri=True, timeout=10)
    c.execute("PRAGMA query_only=ON")
    return c


def _ler_posicao_narrador():
    try:
        if POSICAO_NARRADOR.exists():
            return json.loads(POSICAO_NARRADOR.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ultimo_ts": 0}


def _salvar_posicao_narrador(pos):
    for tentativa in range(3):
        try:
            POSICAO_NARRADOR.parent.mkdir(parents=True, exist_ok=True)
            tmp = POSICAO_NARRADOR.with_suffix(".tmp")
            tmp.write_text(json.dumps(pos, ensure_ascii=False), encoding="utf-8")
            tmp.replace(POSICAO_NARRADOR)
            return
        except PermissionError:
            if tentativa < 2:
                time.sleep(0.1)
        except Exception:
            return


def _estado_narrador_ativo():
    """True se narracao ativa e não pausada."""
    try:
        if NARRACAO_CONTROLE.exists():
            estado = json.loads(NARRACAO_CONTROLE.read_text(encoding="utf-8"))
            return bool(estado.get("ativo", True)) and not bool(estado.get("pausado", False))
    except Exception:
        pass
    return True


def _limpar_texto(texto):
    """Remove Markdown, emojis e símbolos; fica só o texto puro para TTS."""
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


def _simplificar_para_fala(texto):
    """Remove termos técnicos e simplifica texto para fala natural."""
    if not texto:
        return ""
    texto = _EXTensoes.sub("", texto)
    texto = _Caminhos.sub(" ", texto)
    texto = _Arquivos.sub(" ", texto)
    texto = re.sub(r"[,;:]\s*[)\]]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = texto.strip()
    if len(texto) > 200:
        frases = re.split(r"(?<=[.!?])\s+", texto)
        texto = " ".join(frases[:2])
    return texto


# --- Filtros de inteligência do narrador ---

# Padrões de frases de processo/etapa intermediária — NÃO devem ser narrados
_PADROES_PROCESSO = re.compile(
    r"^\s*(?:"
    r"[Vv]ou\s+[\wá-úÁ-Ú]+"
    r"|[Aa]gora (?:vou|continuo|prossigo|preciso)"
    r"|[Cc]ontinuando a"
    r"|[Pp]asso \d+"
    r"|[Ee]tapas do"
    r"|[Pp]roximos passos"
    r"|[Ss]eguindo para"
    r"|[Pp]rocurando"
    r"|[Cc]hecando"
    r"|[Vv]erificando"
    r"|[Ii]dentificando"
    r"|[Mm]apeando"
    r"|[Cc]lassificando"
    r"|[Dd]efinindo"
    r"|[Cc]ompletando"
    r"|[Rr]egistrando"
    r"|[Tt]este(?:i|ndo)"
    r"|[Ii]nstalando"
    r"|[Bb]aixando"
    r"|[Ss]incronizando"
    r"|[Rr]einiciando"
    r"|[Aa]tualizando"
    r"|[Ee]nviando"
    r"|[Rr]ecebendo"
    r"|[Cc]onectando"
    r"|[Dd]esconectando"
    r"|[Ee]ncerrando"
    r"|[Ii]niciando"
    r"|[Ss]alvando"
    r"|[Ll]impando"
    r"|[Oo]timizando"
    r"|[Gg]erando"
    r"|[Cc]onstruindo"
    r"|[Cc]ompilando"
    r"|[Pp]reparando"
    r"|[Ff]iltrando"
    r"|[Ss]intetizando"
    r"|[Rr]esumindo"
    r"|[Vv]alidando"
    r")\b",
    re.IGNORECASE,
)

# Termos técnicos que indicam conteúdo interno (não para narrar)
_TERMO_TECNICO = re.compile(
    r"(?:"
    r"PID|CMD|SQL|API|JSON|XML|HTML|CSS|JS|TS|PY|PS1|BAT|SH"
    r"|GET|POST|PUT|DELETE|PATCH"
    r"|SELECT|INSERT|UPDATE|FROM|WHERE|JOIN"
    r"|\b\w+\.(?:py|js|ts|json|md|html|css|ps1|bat|sh)\b"
    r"|\b\d+\.\d+\.\d+\b"
    r"|\b(?:MB|GB|TB|KB|ms)\b"
    r"|https?://\S+"
    r")\b",
    re.IGNORECASE,
)

# Termos de conclusão/importância — indicam conteúdo para narrar
_CONCLUSAO = re.compile(
    r"(?:"
    r"resumo|diagnostico|conclusao|resultado|status|atualizacao|novidade"
    r"|importante|atencao|erro|sucesso|falha|problema|solucao|correcao"
    r"|melhoria|evolucao|descoberta|achado|finalizado|concluido|pronto"
    r"|completo|aprovado|reprovado|bloqueado|desbloqueado|recuperado"
    r"|restaurado|sincronizado|deployado|configurado|criado|deletado"
    r"|removido|movido|copiado|renomeado|salvo|carregado|enviado"
    r"|recebido|conectado|desconectado|encerrado|iniciado|limpo"
    r"|optimizado|resolvido|tratado|validado|testado|executado"
    r")\b",
    re.IGNORECASE,
)


def _deve_narrar(texto):
    """Decide se um texto deve ser narrado. Retorna (deve_narrar, motivo)."""
    if not texto or not texto.strip():
        return False, "vazio"

    texto = texto.strip()

    # 1. Muito curto para ser útil
    if len(texto) < 30:
        return False, "muito curto"

    # 2. Verifica se é frase de processo/etapa intermediária
    #    considera as 3 primeiras frases: "Confirmado: X. Vou matar e subir..." também bloqueia
    frases = re.split(r"(?<=[.!?])\s+", texto)[:3]
    for frase in frases:
        if _PADROES_PROCESSO.match(frase.strip()):
            return False, "frase de processo"

    # 3. Verifica densidade de termos técnicos
    palavras = re.findall(r"\b\w+\b", texto)
    if len(palavras) > 5:
        tecnicos = sum(1 for p in palavras if _TERMO_TECNICO.match(p))
        ratio_tecnico = tecnicos / len(palavras)
        if ratio_tecnico > 0.3:
            return False, f"muito tecnico ({ratio_tecnico:.0%})"

    # 4. Texto majoritariamente código (muitas linhas com indentação)
    linhas = texto.split("\n")
    linhas_codigo = sum(1 for l in linhas if l.startswith("    ") or l.startswith("\t") or l.startswith("```"))
    if len(linhas) > 3 and linhas_codigo / len(linhas) > 0.4:
        return False, "maioria codigo"

    # 5. É uma conclusão/resumo/importante? → sempre narrar
    if _CONCLUSAO.search(texto[:200]):
        return True, "conclusao"

    # 6. Texto longo o suficiente e não é processo → narrar
    return True, "conteudo"


def _partes_novas(conn, ultimo_ts, excluir):
    """Retorna lista (ts, session_id, titulo, texto) de partes novas."""
    if not DB_NARRADOR.exists():
        return []
    try:
        cur = conn.cursor()
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
            por_msg[msg_id] = (ts or 0, sid, titulo or "", texto)
        saida = []
        for ts, sid, titulo, texto in por_msg.values():
            if titulo and any(x.lower() in titulo.lower() for x in excluir):
                continue
            saida.append((ts, sid, titulo, texto))
        return saida
    except Exception as e:
        _log_narr(f"erro lendo banco: {e}")
        return []


class _Narrador:
    """Buffer com debounce que acumula texto e fala após pausa."""

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
        texto = _limpar_texto(texto)
        texto = _simplificar_para_fala(texto)
        # Filtro inteligente: deve narrar?
        deve, motivo = _deve_narrar(texto)
        if not deve:
            _log_narr(f"PULANDO ({motivo}): {texto[:60]}...")
            return
        if IDIOMA_AVAILABLE and len(texto) > 30:
            resultado = validar_idioma(texto, threshold=5.0)
            if not resultado["ok"]:
                _log_narr(f"BLOQUEADO (idioma={resultado['idioma']}): {texto[:60]}...")
                return
        texto_hash = hashlib.md5(texto.encode("utf-8")).hexdigest()[:16]
        agora = time.time()
        expirados = [k for k, t in _FALADOS.items() if agora - t > _FALADOS_TTL]
        for k in expirados:
            _FALADOS.pop(k, None)
        if texto_hash in _FALADOS:
            _log_narr(f"DEDUP pulando: {texto[:60]}...")
            return
        _FALADOS[texto_hash] = agora
        if STOP_FLAG.exists():
            _log_narr("pulando (parar_fala.flag ativo)")
            return
        texto = pipeline_completo_tts(texto)
        if PROFILE_HOOK_AVAILABLE:
            texto = format_response_for_profile(texto, _profile_config)
        if len(texto) < 15:
            return
        with self.falando:
            _log_narr(f"falando ({len(texto)} chars): {texto[:70]}...")
            try:
                req_id = str(uuid.uuid4())[:8]
                cmd = {"cmd": "speak", "texto": texto, "request_id": req_id, "priority": 0}
                _enviar_tts_cmd(cmd)
                resp_file = RUNTIME / f"tts_resp_{req_id}.json"
                try:
                    for _ in range(1800):
                        if STOP_FLAG.exists():
                            _log_narr("interrompido (parar_fala.flag)")
                            break
                        if resp_file.exists():
                            content = resp_file.read_text(encoding="utf-8")
                            if content and content.strip():
                                try:
                                    resp = json.loads(content)
                                    if resp.get("status") != "ok":
                                        _log_narr(f"TTS service erro: {resp.get('msg')}")
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            break
                        time.sleep(0.05)
                finally:
                    resp_file.unlink(missing_ok=True)
            except Exception as e:
                _log_narr(f"falha de voz: {e}")

    def parar(self):
        if self.timer:
            self.timer.cancel()


def _narrador_loop():
    """Thread interna: lê SQLite, alimenta narrador, envia TTS."""
    pos = _ler_posicao_narrador()
    narrador = _Narrador("assistant")
    _log_narr("narrador integrado ao widget")
    ultimo_ts = pos.get("ultimo_ts", 0)
    try:
        conn = _conectar_narrador()
    except Exception as e:
        _log_narr(f"falha ao conectar banco: {e}")
        return
    try:
        while True:
            ativo = _estado_narrador_ativo()
            novas = _partes_novas(conn, ultimo_ts, EXCLUIR_PADRAO)
            if novas:
                # Filtro inteligente por mensagem: só entra no buffer o que vale narrar
                textos = []
                for ts, sid, titulo, t in novas:
                    deve, motivo = _deve_narrar(t)
                    if deve:
                        textos.append(t)
                    else:
                        _log_narr(f"PULANDO ({motivo}): {t[:60]}...")
                if STOP_FLAG.exists():
                    narrador.parar()
                    _log_narr("buffer descartado (parar_fala.flag)")
                elif ativo and textos:
                    narrador.alimentar(textos)
                ultimo_ts = max(x[0] for x in novas)
                _salvar_posicao_narrador({"ultimo_ts": ultimo_ts})
            try:
                ts_now = _ler_posicao_narrador().get("ultimo_ts", 0)
                if ts_now > ultimo_ts:
                    ultimo_ts = ts_now
                    narrador.parar()
                    narrador = _Narrador("assistant")
            except Exception:
                pass
            time.sleep(0.5)
    except Exception:
        _log_narr("narrador thread encerrada")


# ---------------------------------------------------------------------------


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
            "narr": _estado_narrador_ativo(),
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

    def _narrador_desativar(self):
        """Desliga o narrador completamente (ativo=false, pausado=true)."""
        try:
            estado = {"ativo": False, "pausado": True}
            if NARRACAO_CONTROLE.exists():
                try:
                    estado = json.loads(NARRACAO_CONTROLE.read_text(encoding="utf-8"))
                except Exception:
                    pass
            estado["ativo"] = False
            estado["pausado"] = True
            # Para fala atual via flag
            try:
                STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
            except Exception:
                pass
            tmp = NARRACAO_CONTROLE.with_suffix(".tmp")
            tmp.write_text(json.dumps(estado), encoding="utf-8")
            tmp.replace(NARRACAO_CONTROLE)
        except Exception:
            pass

    def _narrador_pausar(self, pausar: bool):
        """Pausa/retoma o narrador (mantém ativo=true). Usado quando widget fala."""
        try:
            estado = {"ativo": True, "pausado": False}
            if NARRACAO_CONTROLE.exists():
                try:
                    estado = json.loads(NARRACAO_CONTROLE.read_text(encoding="utf-8"))
                except Exception:
                    pass
            estado["pausado"] = bool(pausar)
            if pausar:
                try:
                    STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
                except Exception:
                    pass
            tmp = NARRACAO_CONTROLE.with_suffix(".tmp")
            tmp.write_text(json.dumps(estado), encoding="utf-8")
            tmp.replace(NARRACAO_CONTROLE)
        except Exception:
            pass

    def voice_on(self):
        # Pausa narrador enquanto widget está falando (evita dupla fala)
        self._narrador_pausar(True)
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
        # Pausa narrador (mantém ativo=true, pausado=true) — NÃO desativa
        self._narrador_pausar(True)
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


def _area_util():
    """(left, top, right, bottom) da área útil via SPI_GETWORKAREA."""
    import ctypes

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    try:
        rc = RECT()
        ok = ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rc), 0)
        if ok:
            return int(rc.left), int(rc.top), int(rc.right), int(rc.bottom)
    except Exception:
        pass
    try:
        import ctypes
        u = ctypes.windll.user32
        w = u.GetSystemMetrics(0)
        h = u.GetSystemMetrics(1)
        return 0, 0, int(w), int(h) - 56
    except Exception:
        return 0, 0, 1024, 700


def _posicao_restaurada(largura, altura):
    """Posição salva em widget_state.json se ainda couber na área útil
    atual (monitor mudou, resolução diferente, etc)."""
    try:
        x = int(ler_estado().get("win_x"))
        y = int(ler_estado().get("win_y"))
    except (TypeError, ValueError):
        return None
    l, t, r, b = _area_util()
    # precisa caber inteira e ao menos parcialmente visível
    if not (l <= x < r and t <= y < b and x + largura <= r + 8 and y + altura <= b + 8):
        return None
    return x, y


def _posicao_inferior_esquerda(largura, altura):
    """(x, y) para nascer no canto inferior esquerdo da área útil
    (respeita a barra de tarefas via SPI_GETWORKAREA)."""
    l, t, r, b = _area_util()
    return int(l) + 8, max(int(t), int(b) - altura - 8)


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
    px, py = _posicao_restaurada(360, 300) or _posicao_inferior_esquerda(360, 300)
    print(f"posicao inicial: {px},{py}", flush=True)
    window = webview.create_window(
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

    # Persiste a posição quando o usuário arrasta a janela (easy_drag).
    try:
        window.events.moved += lambda: salvar_estado(
            {"win_x": window.x, "win_y": window.y}
        )
    except Exception as e:
        print(f"moved handler indisponivel: {e}", flush=True)

    threading.Thread(target=poller, args=(api,), daemon=True).start()
    threading.Thread(target=_narrador_loop, daemon=True).start()
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
