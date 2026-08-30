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
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np

# HTTP API para memórias reais (jarvis_bridge.py:8766)
MEMORIES_API = "http://localhost:8766"

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


# HTTP API para memórias reais (jarvis_bridge.py:8766)
MEMORIES_API = "http://localhost:8766"

# Fonte de dados: "vault" (notas), "memories" (memórias reais), "combined"
DATA_SOURCE = os.environ.get("CEREBRO_DATA_SOURCE", "combined")


def fetch_memories_api(limit=300, kind=None, max_days=None):
    """Busca memórias reais do jarvis_bridge.py /api/memories."""
    try:
        import urllib.request
        params = [f"limit={limit}"]
        if kind:
            params.append(f"kind={kind}")
        if max_days:
            params.append(f"max_days={max_days}")
        url = f"{MEMORIES_API}/api/memories?" + "&".join(params)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("nodes", []), data.get("links", [])
    except Exception as e:
        print(f"fetch_memories_api: {type(e).__name__}: {e}", flush=True)
        return [], []


def memories_to_widget(nodes, links, pos_antigas=None):
    """Converte formato /api/memories para formato do widget (nos/ar)."""
    # Mapeia kind -> cluster visual
    kind_to_cluster = {
        "erro": "bugs",
        "decisao": "decisoes",
        "padrao": "padroes",
        "episodio": "cognitivo",
        "preferencia": "heuristicas",
        "experiencia": "frameworks",
        "melhoria": "missoes"
    }
    
    # Filtra nós válidos
    valid_nodes = [n for n in nodes if n.get("id") is not None]
    id_to_idx = {n["id"]: i for i, n in enumerate(valid_nodes)}
    
    # Converte arestas (links usam índices no array original)
    widget_links = []
    for link in links:
        src = link.get("source")
        tgt = link.get("target")
        if src in id_to_idx and tgt in id_to_idx:
            widget_links.append([valid_nodes[id_to_idx[src]]["id"],
                                 valid_nodes[id_to_idx[tgt]]["id"]])
    
    # Layout 3D reusa posições antigas
    nos_brutos = []
    for n in valid_nodes:
        kind = n.get("kind", "episodio")
        cluster = kind_to_cluster.get(kind, "geral")
        # decayScore como "atividade" visual (0.5 base + decayScore * 0.5)
        atv = 0.5 + (n.get("decayScore", 0.5) * 0.5)
        no = {
            "id": str(n["id"]),
            "label": n.get("title", "")[:60] or n.get("summary", "")[:60] or "memoria",
            "cl": cluster,
            "atv": round(atv, 2),
            "kind": kind,
            "decayScore": n.get("decayScore", 0.5),
            "filePath": n.get("filePath", ""),
            "summary": n.get("summary", ""),
            "tags": n.get("tags", []),
            "project": n.get("project", "")
        }
        # tm = timestamp de criação (para sinapses novas)
        if n.get("created_at"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(n["created_at"].replace("Z", "+00:00"))
                no["tm"] = dt.timestamp()
            except Exception:
                pass
        elif n.get("last_accessed"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(n["last_accessed"].replace("Z", "+00:00"))
                no["tm"] = dt.timestamp()
            except Exception:
                pass
        nos_brutos.append(no)
    
    # Aplica layout 3D
    pos, _ = layout_3d(nos_brutos, widget_links, pos_antigas)
    
    # Monta payload final
    nos = []
    for n in nos_brutos:
        no = {
            "id": n["id"],
            "l": n["label"],
            "cl": n["cl"],
            "g": 1,  # grau será recalculado
            "a": n["atv"],
            "x": pos[n["id"]][0],
            "y": pos[n["id"]][1],
            "z": pos[n["id"]][2],
        }
        if n.get("tm"):
            no["tm"] = n["tm"]
        # Campos extras para o frontend
        no["_kind"] = n.get("kind", "episodio")
        no["_decayScore"] = n.get("decayScore", 0.5)
        no["_filePath"] = n.get("filePath", "")
        no["_summary"] = n.get("summary", "")
        no["_tags"] = n.get("tags", [])
        no["_project"] = n.get("project", "")
        nos.append(no)
    
    # Recalcula graus baseados nas arestas
    grau = {}
    for a, b in widget_links:
        grau[a] = grau.get(a, 0) + 1
        grau[b] = grau.get(b, 0) + 1
    for no in nos:
        no["g"] = grau.get(no["id"], 1)
    
    return {"nos": nos, "ar": [[a, b] for a, b in widget_links]}


def montar_payload_combined(mod, pos_antigas=None):
    """Combina vault + memórias reais."""
    # 1. Payload do vault (existente)
    payload_vault, _ = montar_payload(mod, pos_antigas)
    
    # 2. Payload das memórias reais
    mem_nodes, mem_links = fetch_memories_api(limit=200)
    if mem_nodes:
        payload_mem = memories_to_widget(mem_nodes, mem_links, pos_antigas)
        
        # Merge: evita duplicatas por ID
        nos_map = {n["id"]: n for n in payload_vault["nos"]}
        for n in payload_mem["nos"]:
            # Prefere memória real se já existe (dados mais ricos)
            if n["id"] in nos_map:
                # Mescla: mantém posição do vault, adiciona campos da memória
                existing = nos_map[n["id"]]
                existing["_kind"] = n.get("_kind", existing.get("_kind"))
                existing["_decayScore"] = n.get("_decayScore", existing.get("_decayScore"))
                existing["_filePath"] = n.get("_filePath", existing.get("_filePath"))
                existing["_summary"] = n.get("_summary", existing.get("_summary"))
                existing["_tags"] = n.get("_tags", existing.get("_tags"))
                existing["_project"] = n.get("_project", existing.get("_project"))
                # Atualiza atv com decayScore
                existing["a"] = max(existing["a"], n["a"])
            else:
                nos_map[n["id"]] = n
        
        # Merge arestas
        ar_set = set(tuple(a) for a in payload_vault["ar"])
        for a, b in payload_mem["ar"]:
            ar_set.add((a, b))
        
        nos_final = list(nos_map.values())
        ar_final = [list(a) for a in ar_set]
        
        return {"nos": nos_final, "ar": ar_final}
    
    return payload_vault


def _frontmatter_date(path):
    """Extrai o campo 'date' do frontmatter YAML da nota."""
    try:
        txt = path.read_text(encoding='utf-8')
        m = DATE_RE.search(txt)
        if m:
            return m.group(1).strip().strip('"\'')
    except Exception:
        pass
    return None


def mapa_datas():
    """{slug da nota: timestamp (epoch)} do campo 'date' do frontmatter.
    Usa mtime como fallback se nao houver date."""
    m = {}
    for f in VAULT.rglob("*.md"):
        try:
            ds = _frontmatter_date(f)
            ts = None
            if ds:
                from datetime import datetime
                for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
                    try:
                        ts = datetime.strptime(ds[:19], fmt).timestamp()
                        break
                    except ValueError:
                        continue
            if ts is None:
                ts = f.stat().st_mtime
            m[f.stem] = ts
        except Exception:
            continue
    return m


def mapa_caminhos():
    """{slug da nota: caminho relativo ao ecossistema} do vault.
    Usado para abrir a nota no editor a partir de um clique no grafo."""
    m = {}
    for f in VAULT.rglob("*.md"):
        try:
            m[f.stem] = f.relative_to(BASE).as_posix()
        except Exception:
            continue
    return m


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
        # Nos sem nenhuma aresta (libs nao citadas) caem mais forte pro
        # centro: viram um cacho denso em vez de estilhaços soltos.
        grav = np.where(grau == 0, 0.09, 0.018)
        forca -= pos * grav[:, None]
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
    mtimes = mapa_datas()
    paths = mapa_caminhos()
    pos, herdados = layout_3d(nos_brutos, arestas, pos_antigas)
    nos = []
    for n in nos_brutos:
        nid = n["id"]
        nascido = mtimes.get(nid)
        no = {
            "id": nid,
            "l": n.get("label") or nid,
            "cl": n.get("cl", "geral"),
            "g": int(grau_por_id.get(nid, 0)),
            "a": round(float(n.get("atv", 0.5)), 2),
            "x": pos[nid][0],
            "y": pos[nid][1],
            "z": pos[nid][2],
        }
        if nascido:
            no["tm"] = round(float(nascido), 1)
        # Campos extras para o painel de detalhes do frontend
        if n.get("title"):
            no["_summary"] = str(n.get("title"))
        if n.get("tags"):
            tg = n.get("tags")
            no["_tags"] = tg if isinstance(tg, list) else [tg]
        no["_filePath"] = paths.get(nid, "")
        no["_kind"] = "nota"
        nos.append(no)
    global ULTIMA_POS
    ULTIMA_POS = pos
    return {"nos": nos, "ar": [[a, b] for a, b in arestas]}, herdados


def mapa_mtimes():
    """{slug da nota: mtime} de todo o vault. Fonte do diff de eventos."""
    return mapa_datas()


def assinatura_de_mapa(mapa):
    """Mesma assinatura de antes, derivada do mapa sem segundo scan."""
    if not mapa:
        return 0, 0.0
    return len(mapa), max(mapa.values())


MTIMES_ANTIGOS = None  # baseline persistida em cerebro_dados.json (_mtimes)


def instancia_unica():
    import psutil
    import time
    import platform

    me = str(os.getpid())
    print(f"[instancia_unica] Meu PID: {me}, PID_FILE existe: {PID_FILE.exists()}", flush=True)

    for attempt in range(3):
        if attempt > 0:
            time.sleep(0.5)

        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                if platform.system() != "Windows":
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
            print(f"[instancia_unica] PID file criado com sucesso", flush=True)
            return True
        except FileExistsError:
            print(f"[instancia_unica] PID_FILE ja existe (tentativa {attempt+1})", flush=True)
            dono_vivo = False
            try:
                dono = int(PID_FILE.read_text().strip())
                p = psutil.Process(dono)
                cmd = ' '.join(p.cmdline())
                print(f"[instancia_unica] Dono do PID file: PID={dono}, cmd: {cmd[:100]}", flush=True)
                if any(t.lower().endswith("widget_grafo.py") for t in p.cmdline()):
                    dono_vivo = True
            except Exception:
                pass
            if dono_vivo:
                print(f"[instancia_unica] Dono vivo com widget_grafo, retornando False", flush=True)
                return False
            try:
                PID_FILE.unlink()
                print(f"[instancia_unica] PID file removido (dono morto)", flush=True)
            except FileNotFoundError:
                pass
    print(f"[instancia_unica] Tentativas esgotadas, retornando False", flush=True)
    return False
class Api:
    def __init__(self):
        self.payload = None

    def fechar(self):
        import webview, threading
        # salva posicoes ANTES de destruir (o finally pode nao rodar)
        try:
            if ULTIMA_POS:
                salvo = {}
                if DADOS_FILE.exists():
                    salvo = json.loads(DADOS_FILE.read_text(encoding="utf-8"))
                salvo["_pos"] = ULTIMA_POS
                DADOS_FILE.write_text(json.dumps(salvo, ensure_ascii=False),
                                      encoding="utf-8")
        except Exception:
            pass
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except OSError:
            pass
        try:
            if webview.windows:
                webview.windows[0].destroy()
        except Exception:
            pass

        def _sair():
            print("encerrado (forcado)", flush=True)
            os._exit(0)
        # rede de seguranca: destroy() pode nao retornar o controle ao
        # webview.start(), deixando o processo orfao. Garante o fim.
        threading.Timer(2.0, _sair).start()
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
                    print(f"montando payload (assinatura {sig}, fonte={DATA_SOURCE})...", flush=True)
                    if DATA_SOURCE == "memories":
                        mem_nodes, mem_links = fetch_memories_api(limit=300)
                        payload = memories_to_widget(mem_nodes, mem_links, POS_ANTIGAS)
                    elif DATA_SOURCE == "combined":
                        payload = montar_payload_combined(GEN, POS_ANTIGAS)
                    else:
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
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Cerebro Vivo")
            if hwnd:
                u32 = ctypes.windll.user32
                u32.ShowWindow(hwnd, 9)          # SW_RESTORE: desfaz minimizada
                u32.SetForegroundWindow(hwnd)    # traz para frente
                print("janela existente trazida para frente.", flush=True)
        except Exception as e:
            print(f"foco: {type(e).__name__}: {e}", flush=True)
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

    jw = webview.create_window(
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

    def _janela_fechada():
        """Alt+F4 ou fechamento pelo sistema: garante saida do processo."""
        import threading as _t
        _t.Timer(2.0, lambda: os._exit(0)).start()
    jw.events.closed += _janela_fechada

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
