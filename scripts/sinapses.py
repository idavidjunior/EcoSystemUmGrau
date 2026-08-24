"""Sinapses Vivas — ciclo de vida da memória do ecossistema.

Fases:
  0. Telemetria (runtime_context grava o que serve) -> runtime/sinapses/telemetria.jsonl
  1. Laço pós-tarefa: este módulo fecha a tarefa reforçando ou penalizando
     as memórias servidas, usando memory_engine.reinforce/penalizar.
  2. Arestas emergentes entre memórias co-usadas (runtime/sinapses/arestas.json).
  3. Ciclo de vida periódico: decay + reindexação + relatório de saúde.
  5. Autonomia: detectar lacuna de conhecimento e destilar sozinho
     (Wikipédia PT via API oficial) criando memórias 'inferidas' que só
     sobem para 'confirmadas' se servirem tarefas boas de verdade.

Uso:
  python scripts/sinapses.py fechar boa|ruim|neutra ["assunto opcional"]
  python scripts/sinapses.py lacuna
  python scripts/sinapses.py destilar
  python scripts/sinapses.py ciclo [--dry]
  python scripts/sinapses.py relatorio
"""
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / 'runtime' / 'sinapses'
TELEMETRIA = DIR / 'telemetria.jsonl'
ARESTAS = DIR / 'arestas.json'
LACUNAS = DIR / 'lacunas.jsonl'

PONTUACAO_MINIMA = 1.5   # abaixo disso a memória nem era relevante na tarefa


def _ultima_tarefa():
    if not TELEMETRIA.exists():
        return None
    linhas = [l for l in TELEMETRIA.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not linhas:
        return None
    try:
        return json.loads(linhas[-1])
    except json.JSONDecodeError:
        # linha corrompida: tenta a penúltima
        for l in reversed(linhas[:-1]):
            try:
                return json.loads(l)
            except json.JSONDecodeError:
                continue
    return None


def _carregar_arestas():
    try:
        return json.loads(ARESTAS.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _gravar_arestas(arestas):
    ARESTAS.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARESTAS.with_suffix('.tmp')
    tmp.write_text(json.dumps(arestas, ensure_ascii=False, indent=0), encoding='utf-8')
    tmp.replace(ARESTAS)


def _registrar_arestas(ids_servidos):
    """Co-uso na mesma tarefa cria/reforça aresta simétrica."""
    ids = sorted({i['id'] for i in ids_servidos
                  if isinstance(i.get('id'), int)})
    if len(ids) < 2:
        return 0
    arestas = _carregar_arestas()
    criadas = 0
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            chave = f"{ids[a]}-{ids[b]}"
            arestas[chave] = arestas.get(chave, 0) + 1
            criadas += 1
    _gravar_arestas(arestas)
    return criadas


PONTUACAO_LACUNA = 3.0   # abaixo disso, o contexto estava raso


def detectar_lacuna():
    """Fase 5a: o contexto mede a propria ignorancia.
    Retorna 0 e grava lacuna.jsonl quando a ultima tarefa saiu rasa."""
    t = _ultima_tarefa()
    if not t:
        print("[INFO] sem telemetria ainda")
        return 1
    servidas = [m for m in t.get('memorias_servidas', [])]
    maximo = max((m.get('score', 0) for m in servidas), default=0)
    if servidas and maximo >= PONTUACAO_LACUNA:
        print(f"[OK] contexto denso (score max {maximo}) — sem lacuna")
        return 0
    registro = {
        'ts': t.get('ts'),
        'assunto': t.get('assunto', '')[:120],
        'score_maximo': maximo,
        'memorias_servidas': len(servidas),
    }
    DIR.mkdir(parents=True, exist_ok=True)
    with open(LACUNAS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + '\n')
    print(f"[LACUNA_DETECADA] score_max={maximo} "
          f"memorias={len(servidas)} assunto={registro['assunto']}")
    print("     -> agente deve coletar (busca-web / scrape-md) e destilar")
    return 0


def _promover_inferidas(ids_reforzadas):
    """Fase 5c: memória 'inferido' usada com sucesso vira 'confirmado'."""
    import memory_engine as me
    promovidas = []
    for mid in ids_reforzadas:
        m = me.buscar_por_id(mid)
        if not m:
            continue
        meta = m.get('metadata') or {}
        if meta.get('epistemic_status') == 'inferido':
            meta['epistemic_status'] = 'confirmado'
            meta['confirmado_por'] = 'tarefa_boa_sinapses'
            m['metadata'] = meta
            memories = me._load_memories()
            for x in memories:
                if x['id'] == mid:
                    x['metadata'] = meta
                    break
            me._save_memories(memories)
            promovidas.append(mid)
    return promovidas


def fechar(outcome, assunto=''):
    """Fecha a última tarefa servida pela telemetria."""
    import memory_engine as me

    if outcome not in ('boa', 'ruim', 'neutra'):
        print(f"[ERRO] outcome invalido: {outcome!r} (use boa|ruim|neutra)")
        return 2
    t = _ultima_tarefa()
    if not t:
        print("[INFO] nenhuma tarefa na telemetria para fechar")
        return 1

    servidas = [m for m in t.get('memorias_servidas', [])
                if m.get('score', 0) >= PONTUACAO_MINIMA]
    reforzadas, penalizadas = [], []
    for m in servidas:
        mid = m['id']
        if outcome == 'boa':
            if me.reinforce(mid):
                reforzadas.append(mid)
        elif outcome == 'ruim':
            if me.penalizar(mid):
                penalizadas.append(mid)
        # neutra: sem mutação, evita reforçar ruído

    n_arestas = _registrar_arestas(t.get('memorias_servidas', []))

    promovidas = _promover_inferidas(reforzadas) if outcome == 'boa' else []

    print(f"[OK] tarefa fechada ({outcome}): {t.get('assunto', '')[:60]}")
    if reforzadas:
        print(f"     reforçadas: {reforzadas}")
    if penalizadas:
        print(f"     penalizadas: {penalizadas}")
    if promovidas:
        print(f"     inferidas promovidas a confirmado: {promovidas}")
    if not servidas:
        print("     nenhuma memória acima do ponto de corte")
    print(f"     arestas co-uso processadas: {n_arestas}")
    return 0


def relatorio():
    import memory_engine as me
    st = me.stats()
    n_aretas = len(_carregar_arestas())
    total_usos = sum(_carregar_arestas().values()) if n_aretas else 0
    n_tele = 0
    if TELEMETRIA.exists():
        n_tele = sum(1 for l in
                     TELEMETRIA.read_text(encoding='utf-8').splitlines()
                     if l.strip())
    print(f"memórias ativas : {st['active']}/{st['total']}")
    print(f"tarefas servidas: {n_tele}")
    print(f"arestas co-uso  : {n_aretas} (peso acumulado {total_usos})")
    return 0


WIKI_API = 'https://pt.wikipedia.org/w/api.php'
UA = {'User-Agent': 'EcoSystemUmGrau-destilador/1.0 (ecossistema local; contato: usuario)'}
DESTILAR_POR_RODADA = 3
RELEVANCIA_MINIMA = 0.12


def _wiki_get(params):
    url = WIKI_API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode('utf-8'))


def _wiki_buscar(consulta, limite=3):
    """Retorna títulos candidatos (API oficial opensearch).
    Opensearch é estrito: consulta longa volta vazia, então tentamos
    primeiro os termos-chave completos e depois só os dois primeiros."""
    termos = [w for w in consulta.lower().split()
              if len(w) > 2 and w not in _STOP]
    for candidata in (' '.join(termos[:5]), ' '.join(termos[:2])):
        if not candidata.strip():
            continue
        dados = _wiki_get({'action': 'opensearch', 'search': candidata,
                           'limit': limite, 'format': 'json',
                           'redirects': 'resolve'})
        if len(dados) > 1 and dados[1]:
            return dados[1]
    return []


def _wiki_resumo(titulo, frases=8):
    dados = _wiki_get({'action': 'query', 'prop': 'extracts',
                       'explaintext': True, 'exsentences': frases,
                       'titles': titulo, 'format': 'json'})
    paginas = (dados.get('query') or {}).get('pages') or {}
    for p in paginas.values():
        texto = (p.get('extract') or '').strip()
        if texto:
            return titulo, texto
    return None, None


_STOP = {'de', 'da', 'do', 'das', 'dos', 'para', 'com', 'uma', 'que', 'por',
         'em', 'no', 'na', 'os', 'as', 'ao', 'aos', 'e', 'o', 'a', 'como'}


def _relevancia(texto, consulta):
    t = {w for w in consulta.lower().split() if len(w) > 2 and w not in _STOP}
    if not t:
        return 0.0
    c = {w.strip('.,;:()') for w in texto.lower().split()}
    return len(t & c) / len(t)


def destilar():
    """Fase 5b: consome lacunas.jsonl, busca na Wikipédia PT e destila
    memórias 'inferidas'. A validação real fica por conta do laço:
    só vira 'confirmado' se servir uma tarefa boa."""
    import memory_engine as me

    if not LACUNAS.exists():
        print("[INFO] sem lacunas registradas")
        return 0
    linhas = [l for l in LACUNAS.read_text(encoding='utf-8-sig').splitlines()
              if l.strip()]
    registros = []
    for l in linhas:
        try:
            registros.append(json.loads(l))
        except json.JSONDecodeError:
            continue  # linha corrompida é descartada no regravar

    pendentes = [r for r in registros
                 if not r.get('processado')
                 and r.get('tentativas', 0) < 2]
    if not pendentes:
        print("[OK] nenhuma lacuna pendente")
        return 0

    criadas, esgotadas = [], 0
    for lac in pendentes[:DESTILAR_POR_RODADA]:
        assunto = lac.get('assunto', '')
        melhor_txt, melhor_rel, melhor_url = '', 0.0, ''
        try:
            for titulo in _wiki_buscar(assunto):
                tit, resumo = _wiki_resumo(titulo)
                if not resumo:
                    continue
                rel = _relevancia(resumo, assunto)
                if rel > melhor_rel:
                    melhor_txt, melhor_rel = resumo, rel
                    melhor_url = ('https://pt.wikipedia.org/wiki/'
                                  + urllib.parse.quote(tit.replace(' ', '_')))
        except Exception as e:
            print(f"[WARN] busca falhou para '{assunto[:50]}': {e}")

        lac['tentativas'] = lac.get('tentativas', 0) + 1
        if melhor_rel >= RELEVANCIA_MINIMA and melhor_txt:
            try:
                mid = me.add_memory(
                    task=f"destilacao: {assunto[:80]}",
                    summary=melhor_txt[:600],
                    kind='padrao', project='',
                    tags=['destilacao-auto'],
                    confidence=0.5, source_type='inferido',
                    metadata={'epistemic_status': 'inferido',
                              'origem': 'destilador_sinapses',
                              'fonte_url': melhor_url},
                    reindex=False)
                lac['processado'] = True
                lac['memory_id'] = mid
                lac['fonte_url'] = melhor_url
                criadas.append(mid)
            except Exception as e:
                print(f"[ERRO] add_memory falhou: {e}")
        elif lac['tentativas'] >= 2:
            esgotadas += 1

    # regrava atomicamente com os estados atualizados
    tmp = LACUNAS.with_suffix('.tmp')
    tmp.write_text('\n'.join(json.dumps(r, ensure_ascii=False)
                             for r in registros) + '\n', encoding='utf-8')
    tmp.replace(LACUNAS)

    if criadas:
        me.reindexar_semantico(best_effort=True)

    print(f"[OK] destilação: {len(criadas)} memória(s) inferida(s) "
          f"{criadas}, {esgotadas} lacuna(s) esgotada(s)")
    for r in registros:
        if r.get('memory_id'):
            print(f"     lacuna '{r['assunto'][:50]}' -> memória #{r['memory_id']} "
                  f"({r.get('fonte_url', '')})")
    return 0


def ciclo(dry_run=False):
    """Fase 3: rotina periódica de vida — decay, reindexação e relatório."""
    import memory_engine as me
    from datetime import datetime

    r_decay = me.decay_pass(dry_run=dry_run)
    try:
        me.reindexar_semantico(best_effort=True)
        idx = "ok"
    except Exception as e:
        idx = f"falhou: {e}"

    st = me.stats()
    arestas = _carregar_arestas()
    top = sorted(arestas.items(), key=lambda kv: -kv[1])[:8]
    linhas = [
        f"=== SAÚDE DO CÉREBRO VIVO — {datetime.now().isoformat(timespec='seconds')} ===",
        f"memórias ativas : {st['active']}/{st['total']}",
        f"arquivadas agora: {r_decay.get('archived', 0)} "
        f"(restam {r_decay.get('remaining', '?')})",
        f"reindexação     : {idx}",
        f"arestas co-uso  : {len(arestas)}",
    ]
    if top:
        linhas.append("sinapses mais fortes:")
        for chave, peso in top:
            linhas.append(f"  {chave} (peso {peso})")
    texto = "\n".join(linhas) + "\n"
    DIR.mkdir(parents=True, exist_ok=True)
    destino = DIR / 'relatorio_saude.txt'
    tmp = destino.with_suffix('.tmp')
    tmp.write_text(texto, encoding='utf-8')
    tmp.replace(destino)
    print(texto)
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'fechar' and len(sys.argv) >= 3:
        sys.exit(fechar(sys.argv[2].lower(),
                        ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ''))
    elif cmd == 'lacuna':
        sys.exit(detectar_lacuna())
    elif cmd == 'destilar':
        sys.exit(destilar())
    elif cmd == 'ciclo':
        sys.exit(ciclo('--dry' in sys.argv))
    elif cmd == 'relatorio':
        sys.exit(relatorio())
    else:
        print(__doc__)
        sys.exit(1)
