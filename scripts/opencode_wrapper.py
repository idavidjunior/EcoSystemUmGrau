#!/usr/bin/env python3
"""
Wrapper obrigatório de narração em áudio para opencode.
Intercepta toda saída do agente e narra via TTS (edge-tts + MCI).
"""

import sys
import os
import asyncio
import subprocess
import re
import threading
import queue
import time
import tempfile
import base64

# Adiciona scripts ao path
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from jarvis_bridge import gerar_audio
from vox_audio import _tocar_mci

# Flag global de parada (mesmo arquivo do widget/servicos)
STOP_FLAG = os.path.join(BASE, "..", "runtime", "parar_fala.flag")

# Remove códigos ANSI
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text)

# Linhas de ruído do opencode que não devem ser narradas
NOISE_RE = re.compile(
    r'^>\s|^\.{3}|^build\s|^Problema|^Resultado da exec', re.IGNORECASE
)

def is_noise(line: str) -> bool:
    """True se a linha é ruído do terminal (banner, modelo, spinners)."""
    if not line.strip():
        return True
    if NOISE_RE.search(line):
        return True
    return False

def chunk_text(text: str, max_chars: int = 3500) -> list:
    """Divide texto longo em pedaços para o edge-tts (limite ~4095 chars)."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    sentencas = re.split(r'(?<=[.!?])\s+', text)
    atual = ''
    for sent in sentencas:
        if len(atual) + len(sent) + 1 > max_chars:
            if atual.strip():
                chunks.append(atual.strip())
            atual = sent
        else:
            atual = (atual + ' ' + sent).strip()
    if atual.strip():
        chunks.append(atual.strip())
    return chunks

class AudioNarrator:
    """Narra texto via TTS em thread separada para não bloquear."""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.running = True
        self.current_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=False)
        self.thread.start()
    
    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            try:
                item = self.queue.get(timeout=0.5)
                if item is None:
                    break
                text, done_event = item
                if text.strip():
                    self._speak(text, loop)
                done_event.set()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[narrator] erro: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
    
    def _speak(self, text: str, loop):
        try:
            for pedaco in chunk_text(text):
                if not pedaco.strip():
                    continue
                print(f"[narrator] narrando: {pedaco[:60]}...", file=sys.stderr)
                audio_b64 = loop.run_until_complete(gerar_audio(pedaco))
                print(f"[narrator] audio gerado: {len(audio_b64)} bytes", file=sys.stderr)
                
                # Salva em arquivo temporário único
                mp3_path = os.path.join(tempfile.gettempdir(), f"vox_narrator_{int(time.time()*1000)}.mp3")
                with open(mp3_path, 'wb') as f:
                    f.write(base64.b64decode(audio_b64))
                
                # Toca via MCI (bloqueia até terminar)
                _tocar_mci(mp3_path, stop_flag=STOP_FLAG)
                
                # Remove temp file
                try:
                    os.remove(mp3_path)
                except:
                    pass
            print(f"[narrator] reproduzido", file=sys.stderr)
        except Exception as e:
            print(f"[narrator] TTS falhou: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def narrate(self, text: str):
        if not text.strip():
            return None
        done = threading.Event()
        self.queue.put((text, done))
        return done
    
    def narrate_and_wait(self, text: str):
        done = self.narrate(text)
        if done:
            done.wait(timeout=30)
    
    def stop(self):
        self.running = False
        self.queue.put(None)
        self.thread.join(timeout=5)

def run_opencode_with_narration(args):
    """Roda opencode com narração automática de cada resposta."""
    
    # Comando opencode (usa o exe do npm)
    opencode_exe = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Roaming", "npm", "node_modules",
        "opencode-ai", "bin", "opencode.exe"
    )
    if not os.path.exists(opencode_exe):
        opencode_exe = "npx"
        cmd = ["npx", "opencode-ai"] + args
    else:
        cmd = [opencode_exe] + args
    
    narrator = AudioNarrator()
    buffer = []
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
        )
        
        # Lê linha a linha
        for line in proc.stdout:
            clean = strip_ansi(line.rstrip('\n\r'))
            if not clean:
                continue
            
            buffer.append(clean)
            sys.stdout.write(line)
            sys.stdout.flush()
        
        proc.wait()
        
        # Filtra ruído e narra apenas o conteúdo relevante
        meaningful = [l for l in buffer if not is_noise(l)]
        full_response = '\n'.join(meaningful).strip()
        if full_response:
            print(f"[wrapper] narrando resposta completa ({len(full_response)} chars)", file=sys.stderr)
            narrator.narrate_and_wait(full_response)
        
        narrator.stop()
        return proc.returncode
    
    except KeyboardInterrupt:
        narrator.stop()
        proc.terminate()
        return 130
    except Exception as e:
        print(f"[wrapper] erro: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        narrator.stop()
        return 1

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["run", "Olá, teste de narração"]
    return run_opencode_with_narration(args)

if __name__ == '__main__':
    sys.exit(main())