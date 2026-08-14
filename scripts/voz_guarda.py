"""
Voz Guarda — guardião de resiliência do pipeline de voz.

Detecta e limpa restos do bug [WinError 32] (paths temporarios fixos e
compartilhados entre processos concorrentes de audio).

Uso:
  python scripts/voz_guarda.py             # roda como daemon (loop periodico)
  python scripts/voz_guarda.py --check     # escaneia uma vez, JSON na saida
  python scripts/voz_guarda.py --fix       # --check + limpa orfaos do TEMP
  python scripts/voz_guarda.py --stop      # para o daemon rodando

Padroes seguros aceitos (NAO sinalizam):
  - tempfile.mkstemp(...)  e  tempfile.NamedTemporaryFile(...)
  - nomes de arquivo dinamicos (f-string com chave, + str(, timestamp, etc.)

Padroes sinalizados (violacoes):
  - tempfile.gettempdir() + literal ".mp3/.wav/.m4a" fixo
  - caminho literal para o diretorio Temp com nome de arquivo de audio fixo

NUNCA modifica codigo-fonte: apenas sinaliza violacoes e limpa orfaos
(arquivos de audio antigos esquecidos no diretorio temporario).
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ECO_DIR = SCRIPTS_DIR.parent

AUDIO_EXT = (".mp3", ".wav", ".m4a")
SCAN_DIRS = ("scripts", "tts", "bridge", "mcp")
SKIP_DIRS = {"_legado", "legado", "node_modules", ".git", "__pycache__", "temp", "tmp"}
SELF = "scripts/voz_guarda.py"

GUARDA_INTERVAL = int(os.environ.get("VOZ_GUARDA_INTERVAL", "3600"))
ORPHAN_MIN_AGE_SECONDS = int(os.environ.get("VOZ_GUARDA_ORPHAN_AGE", "300"))
ORPHAN_PREFIXES = ("speech_pipeline_", "vox_fala", "vox_dialogo", "vox_narrator_")

LOG_FILE = SCRIPTS_DIR / "voz_guarda.log"
PID_FILE = SCRIPTS_DIR / "voz_guarda.pid"
SPEECH_PIPELINE = ECO_DIR / "tts" / "speech_pipeline.py"

RE_TEMP_AUDIO = re.compile(
    r"""['"]([^'"]*[Tt]emp[\\/][^'"]+\.(?:mp3|wav|m4a))['"]"""
)
RE_GETTEMP_AUDIO = re.compile(
    r"""gettempdir\(\).*?['"]([^'"]+\.(?:mp3|wav|m4a))['"]"""
)


def _basename_static(texto):
    """True se o basename do caminho e literal (sem chave/interpolacao)."""
    base = texto.replace("\\", "/").rsplit("/", 1)[-1]
    if "{" in base or "}" in base or "{" in texto or "}" in texto:
        return False
    return bool(base)


def _linha_e_violacao(line):
    """Heuristica: linha contem path fixo de audio no diretorio temp?"""
    low = line.lower()
    if "mkstemp" in low or "namedtemporaryfile" in low:
        return None
    for m in RE_GETTEMP_AUDIO.finditer(line):
        lit = m.group(1)
        if _basename_static(lit):
            return lit
    for m in RE_TEMP_AUDIO.finditer(line):
        lit = m.group(1)
        if _basename_static(lit):
            return lit
    return None


def _scan():
    """Escaneia os diretorios de codigo e retorna lista de violacoes."""
    violacoes = []
    arquivos = 0
    for sub in SCAN_DIRS:
        raiz = ECO_DIR / sub
        if not raiz.is_dir():
            continue
        for path in sorted(raiz.rglob("*.py")):
            rel = str(path.relative_to(ECO_DIR)).replace("\\", "/")
            if rel == SELF:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            arquivos += 1
            for idx, line in enumerate(lines, start=1):
                lit = _linha_e_violacao(line)
                if lit:
                    violacoes.append({
                        "arquivo": rel,
                        "linha": idx,
                        "trecho": line.strip()[:160],
                        "fixado": lit,
                    })
    return arquivos, violacoes


def _check_mkstemp_speech_pipeline():
    """O speech_pipeline deve usar mkstemp (correcao aplicada)."""
    try:
        content = SPEECH_PIPELINE.read_text(encoding="utf-8")
        return "mkstemp" in content
    except (OSError, UnicodeDecodeError):
        return False


def _temp_dir():
    try:
        import tempfile
        return Path(tempfile.gettempdir())
    except Exception:
        return Path(os.environ.get("TEMP", os.environ.get("TMP", str(Path.home()))))


def _clean_orphans():
    """Remove orfaos de audio antigos do diretorio temporario."""
    tmp = _temp_dir()
    removidos = []
    pendentes = []
    agora = time.time()
    try:
        for ext in AUDIO_EXT:
            for f in tmp.glob(f"*{ext}"):
                nome = f.name.lower()
                if not nome.startswith(ORPHAN_PREFIXES):
                    continue
                try:
                    idade = agora - f.stat().st_mtime
                except OSError:
                    pendentes.append(str(f))
                    continue
                if idade >= ORPHAN_MIN_AGE_SECONDS:
                    try:
                        f.unlink()
                        removidos.append(str(f))
                    except OSError:
                        pendentes.append(str(f))
                else:
                    pendentes.append(str(f))
    except OSError:
        pass
    return removidos, pendentes


def check_once(fix=False):
    """Escaneia uma vez e imprime JSON. Exit 0 limpo, 1 com violacoes."""
    arquivos, violacoes = _scan()
    speech_ok = _check_mkstemp_speech_pipeline()
    removidos, pendentes = [], []
    if fix:
        removidos, pendentes = _clean_orphans()

    if violacoes:
        speech_ok = speech_ok and all(
            v["arquivo"] != "tts/speech_pipeline.py" for v in violacoes
        )

    resultado = {
        "ok": not violacoes and speech_ok,
        "arquivos_escaneados": arquivos,
        "violacoes": violacoes,
        "speech_pipeline_mkstemp": speech_ok,
        "orphans_removidos": removidos,
        "orphans_pendentes": pendentes,
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return resultado["ok"]


def run_guard():
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)
            print(f"voz_guarda ja esta rodando (pid={old_pid})")
            return
        except (OSError, ValueError):
            pass
    PID_FILE.write_text(str(os.getpid()))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    )
    logger = logging.getLogger("voz_guarda")
    try:
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(fh)
    except PermissionError:
        pass

    logger.info("voz_guarda iniciado (intervalo=%ss)", GUARDA_INTERVAL)
    try:
        while True:
            time.sleep(GUARDA_INTERVAL)
            arquivos, violacoes = _scan()
            removidos, pendentes = _clean_orphans()
            if violacoes:
                logger.warning("violacoes de path fixo detectadas: %d", len(violacoes))
                for v in violacoes[:5]:
                    logger.warning(
                        "%s:%s %s", v["arquivo"], v["linha"], v["trecho"]
                    )
            if removidos:
                logger.info("orfaos removidos: %d", len(removidos))
            if pendentes:
                logger.warning("orfaos pendentes (em uso): %d", len(pendentes))
            if not violacoes:
                logger.info("scan limpo (%d arquivos, %d orfaos pendentes)",
                            arquivos, len(pendentes))
    except KeyboardInterrupt:
        logger.info("voz_guarda interrompido")
    finally:
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def stop_guard():
    if not PID_FILE.exists():
        print("voz_guarda nao esta rodando")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 9)
        PID_FILE.unlink()
        print(f"voz_guarda (pid={pid}) parado")
    except Exception as e:
        print(f"erro ao parar voz_guarda: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Guardiao de resiliencia do pipeline de voz")
    ap.add_argument("--check", action="store_true", help="escaneia uma vez e sai (JSON)")
    ap.add_argument("--fix", action="store_true", help="--check + limpa orfaos do TEMP")
    ap.add_argument("--stop", action="store_true", help="para o daemon rodando")
    args = ap.parse_args()
    if args.stop:
        stop_guard()
    elif args.check or args.fix:
        ok = check_once(fix=args.fix)
        sys.exit(0 if ok else 1)
    else:
        run_guard()
