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

# HTTP API para memorias reais (jarvis_bridge.py:8766)
MEMORIES_API = "http://localhost:8766"

if getattr(sys, 'frozen', False):
    exe_dir = Path(sys.executable).resolve().parent
    # Se o exe esta em dist/, a raiz e o pai
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


# HTTP API para memorias reais (jarvis_bridge.py:8766)
MEMORIES_API = "http://localhost:8766"

# Fonte de dados: "vault" (notas), "memories" (memorias reais), "combined"
DATA_SOURCE = os.environ.get("CEREBRO_DATA_SOURCE", "combined")


def fetch_memories_api(limit=300, kind=None, max_days=None):
    """Busca memorias reais do jarvis_bridge.py /api/memories."""
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
    
    # Filtra nos validos
    valid_nodes = [n for n in nodes if n.get("id") is not None]
    id_to_idx = {n["id"]: i for i, n in enumerate(valid_nodes)}
    
    # Converte arestas (links usam indices no array original)
    widget_links = []
    for link in links:
        src = link.get("source")
        tgt = link.get("target")
        if src in id_to_idx and tgt in id_to_idx:
            widget_links.append([valid_nodes[id_to_idx[src]]["id"],
                                 valid_nodes[id_to_idx[tgt]]["id"]])
    
    # Layout 3D reusa posicoes antigas
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
        # tm = timestamp de criacao (para sinapses novas)
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
            "g": 1,  # grau sera recalculado
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
    """Combina vault + memorias reais."""
    # 1. Payload do vault (existente)
    payload_vault, _ = montar_payload(mod, pos_antigas)
    
    # 2. Payload das memorias reais
    mem_nodes, mem_links = fetch_memories_api(limit=200)
    if mem_nodes:
        payload_mem = memories_to_widget(mem_nodes, mem_links, pos_antigas)
        
        # Merge: evita duplicatas por ID
        nos_map = {n["id"]: n for n in payload_vault["nos"]}
        for n in payload_mem["nos"]:
            # Prefere memoria real se ja existe (dados mais ricos)
            if n["id"] in nos_map:
                # Mescla: mantem posicao do vault, adiciona campos da memoria
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
    
    # Força refresh do cache do psutil
    try:
        psutil.Process().cpu_percent()
    except:
        pass
    
    for attempt in range(3):
        # Pequeno delay para evitar race conditions
        if attempt > 0:
            time.sleep(0.5)
        
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                # On Windows, psutil.pids() can return stale PIDs.
                # Skip process scanning on Windows to avoid false positives.
                # The PID file itself is the authoritative lock.
                if platform.system() != "Windows":
                    pids = psutil.pids()
                    try:
                        for pid in pids:
                            if pid == os.getpid():
                                continue
                            try:
                                p = psutil.Process(pid)
                                running = p.is_running()
                                print(f"[instancia_unica] PID {pid}: is_running()={running}", flush=True)
                                if not running:
                                    continue
                                try:
                                    cmdline = p.cmdline()
                                except psutil.NoSuchProcess:
                                    continue
                                if not cmdline:
                                    continue
                                if any(t.lower().strip('"').endswith("widget_grafo.py")
                                       for t in cmdline):
                                    print(f"[instancia_unica] Outro widget_grafo encontrado: PID={pid}", flush=True)
                                    os.close(fd)
                                    PID_FILE.unlink()
                                    return False
                            except psutil.NoSuchProcess:
                                continue
                            except psutil.AccessDenied:
                                continue
                            except Exception as e:
                                print(f"[instancia_unica] Unexpected exception for PID {pid}: {type(e).__name__}: {e}", flush=True)
                                continue
                    except Exception as e:
                        print(f"[instancia_unica] Exception in pids loop: {type(e).__name__}: {e}", flush=True)
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