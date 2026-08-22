#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cerebro Vivo — grafo flutuante do conhecimento em 3D real.

Evolucao do extinto widget_grafo (vis-network): agora o motor e proprio,
com rotacao verdadeira em torno do proprio eixo, profundidade com parallax
e pulsos de sinapse viajando pelas ligacoes (como impulso nervoso).

Pipeline:
  vault -> extrair_nos() (reaproveitado de generate-graph-html.py)
        -> layout de forcas 3D em numpy
        -> runtime/cerebro_dados.json
        -> janela frameless www/cerebro.html (canvas proprio)

Vigia: thread compara assinatura do vault (contagem + mtime maximo) a cada
12s; mudou, recalcula preservando posicoes antigas e empurra para o canvas.
"""

import importlib.util
import json
import math
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np

if getattr(sys, 'frozen', False):
    exe_dir = Path(sys.executable).resolve().parent
    # Se o exe est� em dist/, a raiz � o pai
    if exe_dir.name == "dist":
        BASE = exe_dir.parent
    else:
        BASE = exe_dir
else:
    BASE = Path(__file__).resolve().parent.parent

SCRIPTS = BASE / "scripts"
RUNTIME = BASE / "runtime"
UI = BASE / "www" / "cerebro.html"
PID_FILE = RUNTIME / "grafo.pid"
DADOS_FILE = RUNTIME / "cerebro_dados.json"
AJUSTES_FILE = RUNTIME / "cerebro_ajustes.json"
ATIV_FILE = RUNTIME / "cerebro_atividade.json"
JANELA_FILE = RUNTIME / "cerebro_janela.json"
VAULT = BASE / "conhecimento" / "notas"

LARG, ALT = 430, 570


def carregar_gerador():
    spec = importlib.util.spec_from_file_location(
        "gerador_grafo", str(SCRIPTS / "generate-graph-html.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def layout_3d(nos, arestas, pos_antigas=None, iteracoes=None):
    """Layout forcado em 3D (repulsao vetorial + atracao nas arestas).
    Preserva posicoes antigas de nos existentes (transicao suave no widget);
    nos novos nascem perto do centroide dos vizinhos."""
    rng = np.random.default_rng(42)
    ids = [n["id"] for n in nos]
    idx = {nid: i for i, nid in enumerate(ids)}
    n = len(ids)
    pos = np.zeros((n, 3))
    herdados = 0
    for nid, i in idx.items():
        p = (pos_antigas or {}).get(nid)
        if p is not None:
            pos[i] = p
            herdados += 1
        else:
            pos[i] = rng.uniform(-10, 10, 3)
    ia = np.array([idx[a] for a, b in arestas], dtype=np.int64)
    ib = np.array([idx[b] for a, b in arestas], dtype=np.int64)
    grau = np.zeros(n)
    np.add.at(grau, ia, 1)
    np.add.at(grau, ib, 1)

    # Mudanca pequena no vault (quase tudo herdado) so precisa refinar;
    # layout do zero pede o ciclo completo.
    cobertura = herdados / max(n, 1)
    iteracoes = 320 if cobertura < 0.9 else 70

    k_rep = 26000.0
    k_att = 0.045
    for it in range(iteracoes):
        prog = it / max(1, iteracoes - 1)
        lr = 2.2 * (1 - prog) ** 2 + 0.03
        diff = pos[:, None, :] - pos[None, :, :]
        d2 = (diff ** 2).sum(-1) + 4.0
        forca = (diff / d2[..., None]).sum(axis=1) * k_rep / max(n, 1) ** 0.5
        delta = pos[ib] - pos[ia]
        contrib = delta * k_att
        np.add.at(forca, ia, contrib)
        np.add.at(forca, ib, -contrib)
        forca -= pos * 0.018          # gravidade leve ao centro
        passo = forca * lr
        norma = np.linalg.norm(passo, axis=1, keepdims=True)
        passo = passo / np.maximum(norma, 1e-9) * np.minimum(norma, 30.0)
        pos += passo
    pos -= pos.mean(axis=0)
    raio = np.linalg.norm(pos, axis=1)
    alvo = 150.0
    esc = alvo / max(np.median(raio), 1e-6)
    pos *= min(esc, 6.0)
    return {nid: [round(float(v), 2) for v in pos[idx[nid]]] for nid in ids}, herdados


def montar_payload(mod, pos_antigas=None):
    nos_brutos, arestas_brutas = mod.extrair_nos()
    arestas = sorted(tuple(a) for a in arestas_brutas)
    grau_por_id = {}
    for a, b in arestas:
        grau_por_id[a] = grau_por_id.get(a, 0) + 1
        grau_por_id[b] = grau_por_id.get(b, 0) + 1
    pos, herdados = layout_3d(nos_brutos, arestas, pos_antigas)
    nos = []
    for n in nos_brutos:
        nid = n["id"]
        nos.append({
            "id": nid,
            "l": n.get("label") or nid,
            "cl": n.get("cl", "geral"),
            "g": int(grau_por_id.get(nid, 0)),
            "a": round(float(n.get("atv", 0.5)), 2),
            "x": pos[nid][0],
            "y": pos[nid][1],
            "z": pos[nid][2],
        })
    global ULTIMA_POS
    ULTIMA_POS = pos
    return {"nos": nos, "ar": [[a, b] for a, b in arestas]}, herdados


def mapa_mtimes():
    """{slug da nota: mtime} de todo o vault. Fonte do diff de eventos."""
    m = {}
    for f in VAULT.rglob("*.md"):
        try:
            m[f.stem] = f.stat().st_mtime
        except OSError:
            continue
    return m


def assinatura_de_mapa(mapa):
    """Mesma assinatura de antes, derivada do mapa sem segundo scan."""
    if not mapa:
        return 0, 0.0
    return len(mapa), max(mapa.values())


MTIMES_ANTIGOS = None  # baseline persistida em cerebro_dados.json (_mtimes)


def instancia_unica():
    import psutil

    me = str(os.getpid())
    for _ in range(2):
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                for p in psutil.process_iter(["pid", "cmdline"]):
                    if p.info["pid"] == os.getpid():
                        continue
                    if any(t.lower().strip('"').endswith("widget_grafo.py")
                           for t in (p.info["cmdline"] or [])):
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
                if any(t.lower().endswith("widget_grafo.py") for t in p.cmdline()):
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


class Api:
    def __init__(self):
        self.payload = None

    def fechar(self):
        import webview
        if webview.windows:
            webview.windows[0].destroy()
        return True

    def minimizar(self):
        import webview
        if webview.windows:
            webview.windows[0].minimize()
        return True

    def salvar_ajustes(self, s):
        """Espelho duravel dos ajustes do painel (foco/vivacidade/pulsos)."""
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                AJUSTES_FILE.write_text(json.dumps(obj), encoding="utf-8")
                print("ajustes salvos: " + json.dumps(obj, ensure_ascii=False),
                      flush=True)
        except Exception as e:
            print(f"salvar_ajustes: {type(e).__name__}: {e}", flush=True)
        return True

    def topo(self):
        """Alterna sempre-no-topo <-> fundo do desktop (persistente)."""
        try:
            self._frente = not getattr(self, "_frente", True)
            globals()["JANELA_FRENTE"] = self._frente
            camada_aplicar(self._frente)
            JANELA_FILE.write_text(
                json.dumps({"frente": self._frente}), encoding="utf-8")
            print("janela: " + ("frente" if self._frente else "fundo"),
                  flush=True)
            return self._frente
        except Exception as e:
            print(f"topo: {type(e).__name__}: {e}", flush=True)
            return getattr(self, "_frente", True)


def hwnd_cerebro():
    """Identificador nativo da janela: handle real ou busca pelo titulo."""
    import ctypes
    try:
        import webview
        if webview.windows:
            return int(webview.windows[0].native.Handle)
    except Exception:
        pass
    return int(ctypes.windll.user32.FindWindowW(None, "Cerebro Vivo"))


def janela_frente_desejada():
    """Fonte da verdade da camada: o arquivo que todo clique atualiza."""
    try:
        return bool(json.loads(
            JANELA_FILE.read_text(encoding="utf-8")).get("frente", True))
    except Exception:
        return bool(globals().get("JANELA_FRENTE", True))


def camada_bit(hwnd):
    import ctypes
    return bool(ctypes.windll.user32.GetWindowLongW(hwnd, -20) & 0x8)


def camada_aplicar(frente):
    """TOPMOST na frente; ao fundo, tira o privilegio E afunda na fila ja.
    Verifica o bit real apos aplicar; se nao grudar, escala metodos:
    ctypes de novo -> Form.TopMost (.NET, thread da janela)."""
    import ctypes
    hwnd = hwnd_cerebro()
    if not hwnd:
        print("camada: janela nao encontrada", flush=True)
        return False
    u32 = ctypes.windll.user32
    flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE|NOMOVE|NOACTIVATE
    if not frente:
        u32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, flags)   # HWND_NOTOPMOST
        u32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, flags)    # HWND_BOTTOM
        return True
    for tentativa in range(4):
        if tentativa == 1:
            # segundo empurrao: sobe antes de topizar
            u32.SetWindowPos(hwnd, -1, 0, 0, 0, 0,
                             flags | 0x0040)             # SWP_SHOWWINDOW
        if tentativa == 2 or tentativa == 3:
            try:
                import webview
                webview.windows[0].native.TopMost = True
            except Exception as e:
                print(f"camada native: {type(e).__name__}: {e}", flush=True)
        else:
            u32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, flags)
        if camada_bit(hwnd) == frente:
            if tentativa:
                print(f"camada frente ok (tentativa {tentativa + 1})",
                      flush=True)
            return True
        time.sleep(0.25)
    print("camada: TOPMOST recusado pelo sistema", flush=True)
    return False


def vigia(api):
    import webview

    global POS_ANTIGAS, MTIMES_ANTIGOS
    ult_sig = None
    enviada = False

    def js(expr):
        try:
            webview.windows[0].evaluate_js(expr)
        except Exception:
            pass

    def enviar(payload):
        js("window.cerebroCarregar && cerebroCarregar("
           + json.dumps(payload) + ")")

    while True:
        try:
            mapa = mapa_mtimes()
            sig = assinatura_de_mapa(mapa)

            # cura de deriva: camada desejada vs bit real da janela
            try:
                hwnd = hwnd_cerebro()
                if hwnd:
                    desejada = janela_frente_desejada()
                    if camada_bit(hwnd) != desejada:
                        if camada_aplicar(desejada):
                            print("camada reafirmada: " +
                                  ("frente" if desejada else "fundo"),
                                  flush=True)
            except Exception as e:
                print(f"camada vigia: {type(e).__name__}: {e}", flush=True)

            # eventos reais: notas novas ou editadas desde o ciclo anterior
            if MTIMES_ANTIGOS and webview.windows:
                alteradas = [k for k, v in mapa.items()
                             if MTIMES_ANTIGOS.get(k) != v]
                if alteradas:
                    alteradas.sort(key=lambda k: -mapa[k])
                    eventos = alteradas[:20]
                    js("window.cerebroEvento && cerebroEvento("
                       + json.dumps(eventos) + ")")
                    print(f"eventos: {len(eventos)} nota(s): "
                          + ", ".join(eventos[:4]), flush=True)
                    ult_sig = None  # forca rebuild no mesmo ciclo
            MTIMES_ANTIGOS = mapa

            precisa = (sig != ult_sig) or not enviada
            if precisa and webview.windows:
                pronta = False
                try:
                    pronta = bool(webview.windows[0].evaluate_js(
                        "!!window.cerebroPronto"))
                except Exception:
                    pronta = False
                if pronta:
                    # reaplica ajustes salvos antes do primeiro payload
                    if AJUSTES_SALVOS and not enviada:
                        js("window.cerebroAjustesAplicar && "
                           "cerebroAjustesAplicar("
                           + json.dumps(AJUSTES_SALVOS) + ")")
                    # restaura a camada salva e sincroniza o rotulo do botao
                    if not globals().get("CAMADA_OK"):
                        try:
                            frente = janela_frente_desejada()
                            camada_aplicar(frente)
                            rotulo_bt = "Fundo" if frente else "Frente"
                            js("var b=document.getElementById('btTopo');"
                               "if(b) b.textContent='" + rotulo_bt + "';")
                            globals()["CAMADA_OK"] = True
                            print("camada restaurada: " +
                                  ("frente" if frente else "fundo"), flush=True)
                        except Exception as e:
                            print(f"camada boot: {e}", flush=True)
                    # boot com cache e vault intocado: instantaneo
                    if (not enviada and CACHE and tuple(CACHE["sig"]) == sig
                            and CACHE.get("payload")):
                        enviar(CACHE["payload"])
                        ult_sig = sig
                        enviada = True
                        print(f"cache enviado: {len(CACHE['payload']['nos'])} nos",
                              flush=True)
                        continue
                    print(f"montando payload (assinatura {sig})...", flush=True)
                    payload, _h = montar_payload(GEN, POS_ANTIGAS)
                    POS_ANTIGAS = dict(ULTIMA_POS)
                    api.payload = payload
                    DADOS_FILE.write_text(json.dumps(
                        {"sig": list(sig), "_pos": ULTIMA_POS,
                         "_mtimes": mapa, "payload": payload},
                        ensure_ascii=False),
                        encoding="utf-8")
                    enviar(payload)
                    ult_sig = sig
                    enviada = True
                    print(f"payload enviado: {len(payload['nos'])} nos, "
                          f"{len(payload['ar'])} arestas", flush=True)
        except Exception as e:
            print(f"vigia: {type(e).__name__}: {e}", flush=True)
        time.sleep(12)


def eco_sentinela():
    """Le o retrato do dialogo (dialogo_vivo.json) a cada 1s e empurra o
    estado para o canvas quando muda: hubs se excitam com Eco falando."""
    import webview
    ult_estado = None
    while True:
        try:
            est = ""
            if VIVO_FILE.exists():
                retrato = json.loads(VIVO_FILE.read_text(encoding="utf-8"))
                idade = time.time() - float(retrato.get("quando") or 0)
                # estado obsoleto (sessao morta) nao excita os hubs
                if idade < 15:
                    est = retrato.get("estado") or ""
            if est != ult_estado and webview.windows:
                webview.windows[0].evaluate_js(
                    "window.cerebroEco && cerebroEco(" + json.dumps(est) + ")")
                ult_estado = est
        except Exception:
            pass
        time.sleep(1)


VIVO_FILE = RUNTIME / "dialogo_vivo.json"

ATIV_DIR = RUNTIME / "atividade"
ATIV_TTL = {"fala": 25.0, "memoria": 6.0, "busca": 6.0,
            "ferramenta": 10.0, "resposta": 8.0}


def jarvis_sentinela():
    """Telemetria Jarvis: le runtime/atividade/*.json e empurra ao cerebro.

    Cada emissor escreve <tipo>.json com {quando, intensidade}. Uma atividade
    vale enquanto o arquivo for fresco (TTL por tipo) e com intensidade > 0;
    expirar ou zerar empurra {"tipo":{"i":0}} uma unica vez para o fade-out.
    """
    import webview
    ultimo = {}
    while True:
        agora = time.time()
        atual = {}
        try:
            if ATIV_DIR.is_dir():
                for f in ATIV_DIR.glob("*.json"):
                    tipo = f.stem
                    try:
                        d = json.loads(f.read_text(encoding="utf-8"))
                        q = float(d.get("quando") or 0)
                        i = float(d.get("intensidade") or 0)
                    except Exception:
                        continue
                    ttl = ATIV_TTL.get(tipo, 8.0)
                    if i > 0.01 and (agora - q) <= ttl:
                        atual[tipo] = round(min(1.0, i), 2)
                    elif tipo in ultimo and ultimo.get(tipo, 0) > 0:
                        atual[tipo] = 0.0
        except Exception as e:
            print(f"jarvis_sentinela: {type(e).__name__}: {e}", flush=True)
            atual = dict(ultimo)
        if atual != ultimo:
            if webview.windows:
                payload = {t: {"i": v} for t, v in atual.items()}
                webview.windows[0].evaluate_js(
                    "window.brainSet && brainSet(" +
                    json.dumps(payload) + ")")
            ultimo = {t: v for t, v in atual.items() if v > 0}
        time.sleep(0.7)


def atividade_sentinela():
    """Le cerebro_atividade.json a cada 0.5s e dispara o anel de cognicao.
    Escrito por scripts/cerebro_toque.py quando o agente acessa notas."""
    import webview
    ult = None  # (tipo, tuple(notas)) ja sinalizado
    while True:
        try:
            if webview.windows and ATIV_FILE.exists():
                atv = json.loads(ATIV_FILE.read_text(encoding="utf-8"))
                idade = time.time() - float(atv.get("quando") or 0)
                if idade < 20:
                    chave = (atv.get("tipo") or "",
                             tuple(atv.get("notas") or []))
                    if chave != ult and chave[1]:
                        webview.windows[0].evaluate_js(
                            "window.cerebroAtividade && cerebroAtividade("
                            + json.dumps(chave[0]) + ", "
                            + json.dumps(list(chave[1])) + ")")
                        print("atividade: " + chave[0] + ": "
                              + ", ".join(chave[1][:4]), flush=True)
                        ult = chave
        except Exception:
            pass
        time.sleep(0.5)


POS_ANTIGAS = {}
ULTIMA_POS = {}
CACHE = None  # {"sig": [cnt, mtime], "payload": {...}}
AJUSTES_SALVOS = ""  # texto json do painel Ajustes, reaplicado no boot
GEN = None


def main():
    global GEN, POS_ANTIGAS

    if sys.stdout is None or sys.stderr is None:
        f = open(RUNTIME / "widget_grafo.log", "a", buffering=1,
                 encoding="utf-8")
        sys.stdout = f
        sys.stderr = f

    import faulthandler
    faulthandler.enable(file=sys.stderr)
    print(time.strftime("[%Y-%m-%d %H:%M:%S] boot cerebro"), flush=True)

    if not instancia_unica():
        print("Cerebro Vivo ja esta rodando.", flush=True)
        return

    try:
        dados_salvos = json.loads(DADOS_FILE.read_text(encoding="utf-8"))
        POS_ANTIGAS = dados_salvos.get("_pos", {})
        globals()["MTIMES_ANTIGOS"] = dados_salvos.get("_mtimes") or None
        if dados_salvos.get("payload") and dados_salvos.get("sig"):
            globals()["CACHE"] = {
                "sig": list(dados_salvos["sig"]),
                "payload": dados_salvos["payload"],
            }
    except Exception:
        POS_ANTIGAS = {}

    try:
        globals()["AJUSTES_SALVOS"] = AJUSTES_FILE.read_text(encoding="utf-8")
    except Exception:
        pass

    try:
        globals()["JANELA_FRENTE"] = bool(json.loads(
            JANELA_FILE.read_text(encoding="utf-8")).get("frente", True))
    except Exception:
        pass

    GEN = carregar_gerador()

    import webview

    api = Api()
    api._frente = bool(globals().get("JANELA_FRENTE", True))
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
        rc = RECT()
        ok = ctypes.windll.user32.SystemParametersInfoW(
            0x0030, 0, ctypes.byref(rc), 0)
        px = rc.right - LARG - 10 if ok else 900
        py = rc.bottom - ALT - 10 if ok else 100
    except Exception:
        px, py = 900, 100

    webview.create_window(
        "Cerebro Vivo",
        str(UI),
        js_api=api,
        x=int(px),
        y=int(py),
        width=LARG,
        height=ALT,
        frameless=True,
        easy_drag=False,
        on_top=True,
        background_color="#0b0e14",
        transparent=False,
    )

    threading.Thread(target=vigia, args=(api,), daemon=True).start()
    threading.Thread(target=eco_sentinela, daemon=True).start()
    threading.Thread(target=atividade_sentinela, daemon=True).start()
    threading.Thread(target=jarvis_sentinela, daemon=True).start()
    try:
        webview.start()
    finally:
        # preserva sig/_mtimes/payload: so atualiza _pos (antes apagava o cache)
        try:
            salvo = {}
            if DADOS_FILE.exists():
                salvo = json.loads(DADOS_FILE.read_text(encoding="utf-8"))
            if ULTIMA_POS:
                salvo["_pos"] = ULTIMA_POS
            DADOS_FILE.write_text(json.dumps(salvo, ensure_ascii=False),
                                  encoding="utf-8")
        except Exception:
            pass
        try:
            if PID_FILE.read_text().strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass
    print("encerrado", flush=True)


if __name__ == "__main__":
    main()
