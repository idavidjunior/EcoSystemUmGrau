#!/usr/bin/env python3
"""Monitor Autônomo de Compromissos — executa promessas do Jarvis e avisa o usuário.

Funciona como daemon (eco_agenda intervalo=60s) ou standalone.
Executa compromissos vencidos: pesquisa web, execução de script, verificação.
Empurra resultado pro Vox via WebSocket (push proativo).
"""

import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import urllib.request
import urllib.parse
import re
import html
from datetime import datetime, timedelta
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, "scripts")
RUNTIME = os.path.join(BASE, "runtime")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from runtime_state import (
    load_state, save_state, compromissos_vencidos,
    concluir_compromisso, falhar_compromisso
)

# Config
LOG_FILE = os.path.join(RUNTIME, "compromissos_monitor.log")
PORTA_WS = 8765  # jarvis_bridge WebSocket
CHECK_INTERVAL_S = 60

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("compromissos_monitor")

# ---- Busca Web Determinística (DDG/Bing) ----
_BUSCA_WEB_DDG = "https://lite.duckduckgo.com/lite/?q="
_BUSCA_WEB_BING = "https://www.bing.com/search?q="
_BUSCA_WEB_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def _query_web_enxuta(query: str) -> str:
    stop = {"qual","quais","quanto","quanta","quantos","quantas","como",
            "estao","estava","estavam","onde","quando","porque","para","pra",
            "da","de","do","dos","das","o","a","os","as","em","no","na",
            "nos","nas","hoje","agora","tem","ter","ver","sobre","voce","vc",
            "me","um","uma","uns","umas","isso","aquele","aquilo","e","ou",
            "se","mas","ja","ai","ser","esta","ha","com"}
    toks = [t for t in re.findall(r"[\wáàâãéèêíìîóòôõúùûç]+", query.lower())
            if t not in stop and len(t) >= 3]
    vistos, unicos = set(), []
    for t in toks:
        if t not in vistos:
            vistos.add(t)
            unicos.append(t)
    return " ".join(unicos[:8])

def _parse_ddg_lite(pag: str, max_n: int = 6) -> list:
    links = re.findall(r'<a rel="nofollow" href="([^"]+)"[^>]*>(.*?)</a>', pag, re.S)
    trechos = re.findall(r"<td class=['\"]result-snippet['\"][^>]*>(.*?)</td>", pag, re.S)
    saida = []
    for i, (href, titulo) in enumerate(links[:max_n]):
        t = re.sub(r"<[^>]+>", "", titulo).strip()
        t = html.unescape(t)
        if not t:
            continue
        u = href
        mo = re.search(r"uddg=([^&]+)", href)
        if mo:
            u = urllib.parse.unquote(mo.group(1))
        s = ""
        if i < len(trechos):
            s = re.sub(r"<[^>]+>", "", trechos[i]).strip().replace("\xa0", " ")
            s = html.unescape(s)
        saida.append(f"- {t} — {u}" + (f"\n  {s[:180]}" if s else ""))
    return saida

def _parse_bing(pag: str, max_n: int = 6) -> list:
    blocos = re.split(r'<li class="b_algo', pag)[1:]
    saida = []
    for bloco in blocos:
        if len(saida) >= max_n:
            break
        m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', bloco, re.S)
        if not m:
            continue
        href, tit = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        tit = html.unescape(tit)
        if not tit:
            continue
        u = href
        if "bing.com/ck/" in href:
            um = re.search(r"[?&](?:amp;)?u=([^&]+)", href)
            if um:
                import base64
                cand = um.group(1)
                for i in range(4):
                    c = cand + "=" * i
                    if len(c) % 4:
                        continue
                    try:
                        b = base64.urlsafe_b64decode(c)
                        s = b.decode("utf-8")
                    except Exception:
                        continue
                    if re.match(r"^https?://", s, re.I):
                        u = s
                        break
        sn = re.search(r'<p[^>]*>(.*?)</p>', bloco, re.S)
        s = ""
        if sn:
            s = html.unescape(re.sub(r"<[^>]+>", "", sn.group(1)).strip())
        saida.append(f"- {tit} — {u}" + (f"\n  {s[:180]}" if s else ""))
    return saida

def buscar_web(query: str, max_n: int = 6) -> str:
    """Busca na web e devolve bloco formatado."""
    if not query:
        return ""
    consultas = []
    for qq in (_query_web_enxuta(query), query):
        qq = re.sub(r"\s+", " ", qq).strip()
        if qq and qq not in consultas:
            consultas.append(qq)
    if not consultas:
        consultas = [query]
    for motor in ("ddg", "bing"):
        parser = _parse_ddg_lite if motor == "ddg" else _parse_bing
        base = _BUSCA_WEB_DDG if motor == "ddg" else _BUSCA_WEB_BING
        for qq in consultas:
            try:
                url = base + urllib.parse.quote(qq)
                req = urllib.request.Request(url, headers={"User-Agent": _BUSCA_WEB_UA})
                with urllib.request.urlopen(req, timeout=15) as r:
                    pag = r.read().decode("utf-8", "ignore")
                saida = parser(pag, max_n)
                if saida:
                    bloco = "\n".join(saida) + "\n"
                    logger.info(f"busca web [{motor}]: {len(saida)} resultados para '{query[:50]}'")
                    return bloco
            except Exception as e:
                logger.warning(f"busca web [{motor}] falhou ({qq[:60]}): {e}")
            time.sleep(1.5)
    return ""

# ---- Execução de Compromisso ----
async def executar_compromisso(compromisso: dict) -> tuple[bool, str]:
    """Executa um compromisso conforme seu tipo. Retorna (sucesso, resultado/erro)."""
    cid = compromisso["id"]
    tipo = compromisso.get("tipo", "pesquisa")
    pedido = compromisso.get("pedido_original", "")
    promessa = compromisso.get("promessa", "")

    logger.info(f"Executando compromisso #{cid} [{tipo}]: {pedido[:80]}")

    try:
        if tipo == "pesquisa":
            # Busca web baseada no pedido original
            resultado = buscar_web(pedido)
            if not resultado:
                return False, "Busca web não retornou resultados"
            # Resumo simples: pegar primeiros 3 resultados
            linhas = resultado.strip().split("\n")
            resumo = "\n".join(linhas[:6])  # 3 resultados com trechos
            return True, f"Resultado da pesquisa para '{pedido}':\n{resumo}"

        elif tipo == "execucao":
            # Executar script Python permitido
            # Pedido deve conter caminho do script nos params
            state = load_state()
            # Por enquanto, usar eco_agenda action=script
            return False, "Execução de script não implementada no monitor (use eco_agenda)"

        elif tipo == "verificacao":
            # Verificação genérica (ex: status de serviço, versão)
            # Usa busca web se for algo verificável online
            resultado = buscar_web(f"verificar {pedido}")
            if not resultado:
                return False, "Verificação não retornou dados"
            return True, f"Verificação: {resultado[:500]}"

        elif tipo == "monitoramento":
            # Monitoramento contínuo - apenas reporta status atual
            resultado = buscar_web(f"status {pedido}")
            if not resultado:
                return False, "Monitoramento não retornou dados"
            return True, f"Monitoramento: {resultado[:500]}"

        else:
            # Fallback: busca web genérica
            resultado = buscar_web(pedido)
            if not resultado:
                return False, "Nenhum resultado"
            return True, resultado[:800]

    except Exception as e:
        logger.exception(f"Erro executando compromisso #{cid}")
        return False, f"Erro: {e}"

# ---- Push WebSocket pro Vox ----
async def push_para_vox(mensagem: str, tipo: str = "compromisso_resultado"):
    """Envia mensagem proativa pro Vox via WebSocket da bridge."""
    try:
        import websockets
        uri = f"ws://127.0.0.1:{PORTA_WS}"
        async with websockets.connect(uri, ping_timeout=None) as ws:
            payload = {
                "tipo": "push",
                "push_tipo": tipo,
                "texto": mensagem,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            }
            await ws.send(json.dumps(payload))
            logger.info(f"Push enviado pro Vox: {tipo} ({len(mensagem)} chars)")
            return True
    except Exception as e:
        logger.warning(f"Falha push Vox: {e}")
        return False

# ---- Loop Principal ----
async def processar_compromissos():
    """Processa todos os compromissos vencidos."""
    vencidos = compromissos_vencidos()
    if not vencidos:
        return 0

    logger.info(f"{len(vencidos)} compromisso(s) vencido(s) para processar")
    processados = 0

    for c in vencidos:
        cid = c["id"]
        # Marca como executando
        atualizar_compromisso(cid, status="executando")

        ok, resultado = await executar_compromisso(c)

        if ok:
            concluir_compromisso(cid, resultado)
            # Push pro Vox
            msg = f"✅ Compromisso cumprido: {c.get('promessa', 'pesquisa')}\n{resultado[:800]}"
            await push_para_vox(msg, "compromisso_concluido")
            logger.info(f"Compromisso #{cid} concluído com sucesso")
        else:
            falhar_compromisso(cid, resultado)
            msg = f"⚠️ Compromisso falhou: {c.get('promessa', 'pesquisa')}\n{resultado}"
            await push_para_vox(msg, "compromisso_falhou")
            logger.warning(f"Compromisso #{cid} falhou: {resultado}")

        processados += 1

    return processados

def atualizar_compromisso(cid, **campos):
    state = load_state()
    for c in state.get("compromissos", []):
        if c["id"] == cid:
            c.update(campos)
            save_state(state)
            return True
    return False

async def main_loop(once=False):
    """Loop principal do monitor."""
    logger.info("=== Monitor de Compromissos iniciado ===")
    while True:
        try:
            n = await processar_compromissos()
            if n > 0:
                logger.info(f"Processados {n} compromisso(s)")
        except Exception as e:
            logger.exception(f"Erro no loop principal: {e}")
        if once:
            break
        await asyncio.sleep(CHECK_INTERVAL_S)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Monitor Autônomo de Compromissos")
    parser.add_argument("--once", action="store_true", help="Executa uma vez e sai")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL_S, help="Intervalo em segundos")
    args = parser.parse_args()

    CHECK_INTERVAL_S = args.interval
    try:
        asyncio.run(main_loop(once=args.once))
    except KeyboardInterrupt:
        logger.info("Monitor interrompido pelo usuário")