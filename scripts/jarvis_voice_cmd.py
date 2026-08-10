#!/usr/bin/env python3
"""jarvis_voice_cmd.py — Ponte voz → automação OS.

Escuta comandos de voz (via vox_audio STT), executa via os-automation,
e responde em áudio (via vox_audio TTS). Roda em background quando
a narração está ATIVA (Eco).
"""

import json
import os
import re
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mcp" / "os" / "habilidades" / "os-automation"))
sys.path.insert(0, str(ROOT / "scripts"))

import vox_audio
from server import automation as os_auto

CONTROLE = ROOT / "runtime" / "narracao_estado.json"
LOG = ROOT / "scripts" / "jarvis_voice_cmd_log.txt"


def log(msg):
    linha = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    print(linha, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def narracao_ativa():
    try:
        if CONTROLE.exists():
            return bool(json.loads(CONTROLE.read_text(encoding="utf-8")).get("ativo", True))
    except Exception:
        pass
    return True


def falar(texto):
    """Fala via vox_audio (interruptível)."""
    vox_audio.cmd_falar(texto, interruptivel=True)


def parse_comando(texto: str):
    """Converte linguagem natural em ação os-automation.
    Retorna (acao, params) ou (None, None) se não reconhecido."""
    t = texto.lower().strip()
    
    # Normaliza acentos básicos para robustez
    t = t.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
    
    # Web: navegar
    m = re.search(r'(?:abra|va para|acesse|navegue para|va)\s+(https?://\S+|www\.\S+|\S+\.\w+)', t)
    if m:
        url = m.group(1)
        if not url.startswith('http'):
            url = 'https://' + url
        return "web_navigate", {"url": url}
    
    # Web: clicar
    m = re.search(r'clique\s+(?:no|em)\s+(.+)', t)
    if m:
        return "web_click", {"selector": m.group(1).strip()}
    
    # Web: digitar
    m = re.search(r'(?:digite|escreva|preencha)\s+"([^"]+)"\s*(?:em|no)?\s*(.*)', t)
    if m:
        texto_dig = m.group(1)
        seletor = m.group(2).strip() or "input, textarea"
        return "web_type", {"selector": seletor, "text": texto_dig}
    
    # Web: extrair
    m = re.search(r'(?:leia|extraia|pegue|obtenha)\s+(?:o|a)?\s*(.+)', t)
    if m:
        return "web_extract", {"selector": m.group(1).strip(), "attribute": "text"}
    
    # Web: screenshot
    if any(k in t for k in ["print", "captura", "screenshot", "tire print"]):
        return "web_screenshot", {}
    
    # Desktop: encontrar janela
    m = re.search(r'(?:encontre|ache|foque|va para)\s+(?:a\s+)?janela\s+(.+)', t)
    if m:
        return "desktop_find_window", {"title_regex": m.group(1).strip()}
    
    # Desktop: clicar
    m = re.search(r'clique\s+(?:na|no)\s+janela\s+(.+)', t)
    if m:
        return "desktop_click", {"control_path": m.group(1).strip()}
    
    # Desktop: digitar
    m = re.search(r'(?:digite|escreva)\s+"([^"]+)"\s+na\s+janela\s+(.+)', t)
    if m:
        return "desktop_type", {"text": m.group(1), "control_path": m.group(2).strip()}
    
    # Desktop: screenshot
    if "print da janela" in t or "captura a janela" in t:
        return "desktop_screenshot", {}
    
    # Espera
    m = re.search(r'espere\s+(\d+(?:\.\d+)?)\s*segundos?', t)
    if m:
        return "sleep", {"seconds": float(m.group(1))}
    
    return None, None
    
    return None, None


async def executar_acao(acao, params):
    try:
        if acao == "web_navigate":
            r = await os_auto.web_navigate(**params)
            return f"Naveguei para {params.get('url')}"
        elif acao == "web_click":
            await os_auto.web_click(**params)
            return f"Cliquei em {params.get('selector')}"
        elif acao == "web_type":
            await os_auto.web_type(**params)
            return f"Digitei '{params.get('text')}' em {params.get('selector')}"
        elif acao == "web_extract":
            r = await os_auto.web_extract(**params)
            dado = r.get("data", "")
            return f"Extraí: {dado[:200]}"
        elif acao == "web_screenshot":
            r = await os_auto.web_screenshot()
            return f"Print salvo em {r.get('path')}"
        elif acao == "desktop_find_window":
            r = os_auto.desktop_find_window(**params)
            return f"Janela encontrada: {r.get('title')} (PID {r.get('process_id')})"
        elif acao == "desktop_click":
            # precisa do handle - simplificado: usa último find_window
            return "Use 'encontre janela X' primeiro, depois 'clique na janela...'"
        elif acao == "desktop_type":
            return "Use 'encontre janela X' primeiro."
        elif acao == "desktop_screenshot":
            return "Use 'encontre janela X' primeiro."
        elif acao == "sleep":
            os_auto.sleep(**params)
            return f"Esperei {params.get('seconds')} segundos"
    except Exception as e:
        return f"Erro: {e}"
    return "Ação não implementada"


async def loop_voz():
    log("Loop de comandos de voz iniciado")
    ultima_atividade = time.time()
    
    while True:
        try:
            if not narracao_ativa():
                time.sleep(2)
                continue
            
            # Escuta comando (7 segundos)
            log("Ouvindo comando...")
            texto = vox_audio.cmd_ouvir()
            
            if not texto or len(texto.strip()) < 3:
                continue
            
            log(f"Comando: {texto}")
            
            # Verifica comandos de controle
            tl = texto.lower()
            if any(k in tl for k in ["para", "cala", "chega", "pare"]):
                falar("Parando.")
                # Escreve controle off
                CONTROLE.parent.mkdir(parents=True, exist_ok=True)
                tmp = CONTROLE.with_suffix(".tmp")
                tmp.write_text(json.dumps({"ativo": False}), encoding="utf-8")
                tmp.replace(CONTROLE)
                continue
            if any(k in tl for k in ["eco", "ativar"]):
                falar("Já estou ativo.")
                continue
            
            # Parse e executa
            acao, params = parse_comando(texto)
            if acao:
                falar("Executando.")
                resultado = await executar_acao(acao, params)
                falar(resultado)
            else:
                falar("Não entendi. Tente: abra site.com, clique no botão, digite 'texto' no campo, encontre janela Chrome.")
            
            ultima_atividade = time.time()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Erro no loop: {e}")
            time.sleep(1)
    
    log("Loop de voz encerrado")


def main():
    import asyncio
    try:
        asyncio.run(loop_voz())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()