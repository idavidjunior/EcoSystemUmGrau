"""Memory engine: cross-session memory with Ebbinghaus decay."""
import json, os, re, sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
MEM_DIR = os.path.join(BASE, 'conhecimento', 'memoria')
SESSIONS_DIR = os.path.join(MEM_DIR, 'sessions')
MEMORIES_FILE = os.path.join(MEM_DIR, 'memories.json')
INDEX_FILE = os.path.join(MEM_DIR, 'index.json')

sys.path.insert(0, os.path.join(BASE, 'scripts'))
try:
    from semantic_tags import extrair_tags
except ImportError:
    extrair_tags = None

HALF_LIFE = {
    'decisao': 30,     # decisions last 30 days
    'padrao': 60,      # patterns last 60 days
    'episodio': 7,     # episodes last 7 days
    'erro': 90,        # errors last 90 days
    'contexto': 14,    # context lasts 14 days
    'preferencia': 365 # preferences last 1 year
}

# Redação automática de dados sensíveis antes de persistir (padrão isair/jarvis).
# Emails, chaves de API, tokens, senhas em pares, JWT, cartões e CPF/CNPJ são
# substituídos por marcadores — reforça LGPD/GDPR (cláusula de deveres externos):
# a memória em disco nunca guarda segredo em claro.
REDACT_ENABLED = os.environ.get('MEMORY_REDACT', '1') == '1'
_REDACT_PATTERNS = [
    (re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'), '[email]'),
    (re.compile(r'\b(?:sk|pk|ghp|gho|ghu|ghs|xox[baprs]|AKIA|AIza|sk-ant|sk-[A-Za-z0-9])\S*\b', re.IGNORECASE), '[chave]'),
    (re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), '[jwt]'),
    (re.compile(r'(?i)\b(password|passwd|senha|secret|token|api[-_]?key)\b\s*[=:]\s*["\']?[^\s,;"\']+'), r'\1=[redigido]'),
    (re.compile(r'\b(?:\d[ -]*?){13,16}\b'), '[cartao]'),
    (re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'), '[cpf]'),
    (re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'), '[cnpj]'),
]


def redigir_sensivel(texto):
    """Substitui segredos/identificadores pessoais em `texto` por marcadores.

    Nunca lança: se algo falhar, devolve o texto original (seguro não perder
    a memória por causa do redator). Desativável via env MEMORY_REDACT=0.
    """
    if not texto or not REDACT_ENABLED:
        return texto
    try:
        for padrao, marcador in _REDACT_PATTERNS:
            texto = padrao.sub(marcador, texto)
        return texto
    except Exception:
        return texto

def _ensure_dirs():
    for d in [MEM_DIR, SESSIONS_DIR]:
        os.makedirs(d, exist_ok=True)

def _load_memories():
    _ensure_dirs()
    if os.path.exists(MEMORIES_FILE):
        with open(MEMORIES_FILE, encoding='utf-8') as f:
            return json.load(f)
    return []

def _save_memories(memories):
    _ensure_dirs()
    tmp = MEMORIES_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MEMORIES_FILE)
    # Build index
    index = {}
    for m in memories:
        for tag in m.get('tags', []):
            index.setdefault(tag, []).append(m['id'])
        proj = m.get('project', '')
        if proj:
            index.setdefault(f'proj:{proj}', []).append(m['id'])
    tmp_idx = INDEX_FILE + '.tmp'
    with open(tmp_idx, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    os.replace(tmp_idx, INDEX_FILE)

def _decay_score(memory, now=None):
    """Ebbinghaus decay: score = strength * (0.5 ^ (days / half_life))"""
    if now is None:
        now = datetime.now()
    kind = memory.get('kind', 'episodio')
    half_life = HALF_LIFE.get(kind, 14)
    # Tolerante a variações de chave em memórias antigas/sintéticas
    stamp = (memory.get('last_accessed')
             or memory.get('created_at')
             or memory.get('created')
             or now.isoformat())
    last_acc = datetime.fromisoformat(stamp)
    days = (now - last_acc).total_seconds() / 86400
    strength = memory.get('strength', 1.0)
    return strength * (0.5 ** (days / half_life))

def _next_id(memories):
    return max([m['id'] for m in memories], default=0) + 1

def log_session(session_id=None, task=None, project=None, outcome=None,
                files=None, tokens=None, duration=None, tags=None):
    """Log a raw session event to JSONL."""
    _ensure_dirs()
    if session_id is None:
        session_id = datetime.now().strftime('session-%Y%m%d-%H%M%S-%f')
    event = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'task': task or '',
        'project': project or '',
        'outcome': outcome or '',
        'files': files or [],
        'tokens': tokens or 0,
        'duration_s': duration or 0,
        'tags': tags or []
    }
    fname = f"{session_id.split('-')[1]}.jsonl"
    path = os.path.join(SESSIONS_DIR, fname)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return session_id

def add_memory(task, summary, kind='episodio', project='', tags=None,
               strength=1.0, metadata=None, reindex=True,
               confidence=1.0, source_type='experiencia',
               solucao_aplicada=None,
               source_anchors=None,
               validado=False):
    """Add a consolidated memory with decay + epistemic metadata.

    confidence: float 0-1 — confiança epistêmica (1.0 = fato, 0.3 = hipótese).
    source_type: enum — 'experiencia', 'inferido', 'api', 'humano', 'rag'.
    source_anchors: list[dict] — âncoras de source {filePath, lineStart, lineEnd, snippet}
        para evidence-grounding (rastreabilidade até código/fonte).
    solucao_aplicada: dict ou None — para memórias de tipo 'erro', armazena a
        solução aplicada: {desc, script, data, tags, validado}.

    validado: bool — PROTEÇÃO ANTI-LIXO. Se False, a memória entra como
        RASCUNHO (confidence=0.3, tag='rascunho', aparece no /listar com aviso).
        Só vai pra base de conhecimento como fato após o usuário validar via
        scripts/promover_aprendizado.py. Default False (regra de 2026-08-31:
        nada vira conhecimento sem prova).

    Dispara reindexação semântica automática (TF-IDF + denso) para que a nova
    memória fique imediatamente recuperável por significado. Nunca bloqueia o add
    em caso de falha (best-effort). Use reindex=False para adições em lote rápidas.
    """
    # Gate de validacao (regra 2026-08-31): memorias nao validadas tem
    # confidence baixa e tag 'rascunho' para nao poluir a base.
    if not validado:
        confidence = min(confidence, 0.3)
        tags = list(tags or [])
        if 'rascunho' not in tags:
            tags.append('rascunho')
        if source_type == 'experiencia':
            source_type = 'rascunho'
    memories = _load_memories()
    now = datetime.now()
    tags = tags or []
    # Redação de dados sensíveis antes de persistir (LGPD; nunca gravar segredo)
    task = redigir_sensivel(task)
    summary = redigir_sensivel(summary)
    # Tag automática de confiança
    if confidence < 0.7:
        tags.append('baixa-confianca')
    elif confidence >= 0.9:
        tags.append('alta-confianca')
    if extrair_tags:
        semanticas = extrair_tags(f'{task} {summary}', max_tags=6)
        for t in semanticas:
            if t and t not in tags:
                tags.append(t)
    memory = {
        'id': _next_id(memories),
        'kind': kind,
        'task': task,
        'summary': summary,
        'project': project,
        'tags': tags,
        'metadata': metadata or {},
        'strength': strength,
        'confidence': confidence,
        'source_type': source_type,
        'source_anchors': source_anchors or [],
        'access_count': 0,
        'created_at': now.isoformat(),
        'last_accessed': now.isoformat()
    }
    if solucao_aplicada and kind == 'erro':
        memory['solucao_aplicada'] = solucao_aplicada
    memories.append(memory)
    _save_memories(memories)
    if reindex:
        reindexar_semantico(best_effort=True)
    try:
        from atividade_emit import emitir
        emitir("memoria", 0.75)
    except Exception:
        pass
    return memory['id']


def reindexar_semantico(best_effort=True):
    """Reconstrói o índice semântico (TF-IDF + matriz densa) de forma automática.

    Chamado após cada add_memory para que a memória nova seja recuperável por
    significado imediatamente. Em best_effort, falhas são reportadas mas nunca
    quebram o fluxo do add.

    Otimização 2026-08-08 (fix: add travava baixando modelo do HuggingFace):
      - Se o índice TF-IDF já reflete o corpus (fingerprint igual), pula tudo.
      - TF-IDF é reconstruído quando desatualizado (rápido, ~1s).
      - Camada densa (MiniLM) NUNCA bloqueia o add: é reconstruída em um
        subprocesso destacado (background) quando a matriz está velha ou ausente.
      - O download do modelo nunca é forçado (local_files_only=True).
    """
    try:
        from memory_semantic import build_index, index_stale, _dense_recente, _dense_lock_held
        import subprocess
        if not index_stale():
            return
        r = build_index(verbose=False)
        if r.get('ok'):
            print(f'[REINDEX] índice semântico atualizado: {r["count"]} docs')
            if not _dense_recente() and not _dense_lock_held():
                # Rebuild denso em background: ~2min no CPU nao pode bloquear o add.
                script = os.path.join(BASE, 'scripts', 'memory_semantic.py')
                flags = getattr(subprocess, 'DETACHED_PROCESS', 0) if os.name == 'nt' else 0
                subprocess.Popen([sys.executable, script, 'build-dense'],
                                 creationflags=flags, close_fds=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print('[REINDEX] rebuild denso disparado em background')
        else:
            print(f'[REINDEX] aviso: {r.get("erro", "falha no build")}')
    except Exception as e:
        if best_effort:
            print(f'[REINDEX] aviso (best-effort): {e}')
        else:
            raise

def reinforce(memory_id, delta=0.15):
    """Reinforce a memory when reused."""
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id:
            m['strength'] = min(2.0, m.get('strength', 1.0) + delta)
            m['access_count'] = m.get('access_count', 0) + 1
            m['last_accessed'] = datetime.now().isoformat()
            # Confiança aumenta levemente com reforço (memória usada = mais confiável)
            m['confidence'] = min(1.0, m.get('confidence', 1.0) + 0.02)
            _save_memories(memories)
            return True
    return False


def penalizar(memory_id, delta=0.05):
    """Sinapses Vivas fase 1: memória servida mas inútil/enganosa perde força.
    Proteções: decisões consolidadas e confiança alta não descem de
    confidence; strength tem piso 0.1 (decay_pass arquiva abaixo disso)."""
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id:
            if m.get('kind') == 'decisao' and m.get('confidence', 1.0) >= 0.9:
                return False          # decisão consolidada é intocável aqui
            m['strength'] = max(0.1, m.get('strength', 1.0) - delta)
            m['last_accessed'] = datetime.now().isoformat()
            m['access_count'] = m.get('access_count', 0) + 1  # acesso conta mesmo negativo
            if m.get('confidence', 1.0) < 0.9:
                m['confidence'] = round(max(0.3, m['confidence'] - 0.01), 4)
            _save_memories(memories)
            return True
    return False


def buscar_por_id(memory_id):
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id:
            return m
    return None

def link_solution(memory_id, solucao_desc, script=None, validado=True, tags=None):
    """Vincula uma solução a uma memória de erro existente.

    memory_id: ID da memória de erro
    solucao_desc: descrição da solução aplicada
    script: script que implementa a solução (opcional)
    validado: se a solução foi validada (default True)
    tags: tags da solução (opcional)
    """
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id and m.get('kind') == 'erro':
            m['solucao_aplicada'] = {
                'desc': solucao_desc,
                'script': script,
                'data': datetime.now().isoformat(),
                'validado': validado,
                'tags': tags or []
            }
            _save_memories(memories)
            return True
    return False

def get_unsolved_errors():
    """Retorna memórias de erro sem solução vinculada."""
    memories = _load_memories()
    return [m for m in memories if m.get('kind') == 'erro' and not m.get('solucao_aplicada')]

def get_solved_errors():
    """Retorna memórias de erro com solução vinculada."""
    memories = _load_memories()
    return [m for m in memories if m.get('kind') == 'erro' and m.get('solucao_aplicada')]

def build_solution_index():
    """Constrói índice cruzado problema→solução a partir das memórias."""
    memories = _load_memories()
    index = {
        'problemas': [],
        'solucoes': [],
        'cruzamento': []
    }
    for m in memories:
        if m.get('kind') == 'erro':
            entry = {
                'id': m['id'],
                'task': m['task'],
                'summary': m['summary'][:200],
                'tags': m.get('tags', []),
                'tem_solucao': bool(m.get('solucao_aplicada'))
            }
            index['problemas'].append(entry)
            if m.get('solucao_aplicada'):
                sol = m['solucao_aplicada']
                index['solucoes'].append({
                    'erro_id': m['id'],
                    'desc': sol.get('desc', ''),
                    'script': sol.get('script'),
                    'validado': sol.get('validado', False),
                    'data': sol.get('data', '')
                })
                index['cruzamento'].append({
                    'erro_id': m['id'],
                    'erro_task': m['task'][:100],
                    'solucao_desc': sol.get('desc', '')[:200],
                    'tags': list(set(m.get('tags', []) + sol.get('tags', [])))
                })
    return index

def query(project=None, tags=None, kind=None, text=None, limit=10,
          min_score=0.05, min_confidence=0.0, source_type=None):
    """Search memories with decay scoring and filters.
    
    min_confidence: filtra memórias com confidence >= valor (0-1)
    source_type: filtra por tipo de fonte ('experiencia', 'inferido', 'api', 'humano', 'rag')
    """
    memories = _load_memories()
    now = datetime.now()
    scored = []

    for m in memories:
        score = _decay_score(m, now)
        if score < min_score: continue
        if project and m.get('project') != project: continue
        if kind and m.get('kind') != kind: continue
        if tags and not any(t in m.get('tags', []) for t in tags): continue
        if source_type and m.get('source_type') != source_type: continue
        if m.get('confidence', 1.0) < min_confidence: continue
        if text:
            text_lower = text.lower()
            task_match = text_lower in m.get('task', '').lower()
            summary_match = text_lower in m.get('summary', '').lower()
            if not (task_match or summary_match): continue
        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:limit]]

def get_context(project=None, tags=None, text=None, limit=8):
    """Get formatted context string for prompts."""
    memories = query(project=project, tags=tags, text=text, limit=limit)
    if not memories:
        return ''
    lines = ['## Memory Context (from previous sessions)']
    for m in memories:
        kind = m['kind']
        task = m['task'][:80]
        score = _decay_score(m)
        pct = f'{int(score*100)}%'
        lines.append(f'- [{kind}] {task} (relevance: {pct})')
        lines.append(f'  {m["summary"][:120]}')
    return '\n'.join(lines)

def stats():
    """Return memory statistics."""
    memories = _load_memories()
    now = datetime.now()
    total = len(memories)
    by_kind = {}
    by_confidence = {'alta': 0, 'media': 0, 'baixa': 0}
    by_source = {}
    active = 0
    for m in memories:
        k = m.get('kind', 'unknown')
        by_kind[k] = by_kind.get(k, 0) + 1
        conf = m.get('confidence', 1.0)
        if conf >= 0.9:
            by_confidence['alta'] += 1
        elif conf >= 0.7:
            by_confidence['media'] += 1
        else:
            by_confidence['baixa'] += 1
        src = m.get('source_type', 'desconhecido')
        by_source[src] = by_source.get(src, 0) + 1
        if _decay_score(m, now) > 0.1: active += 1
    return {'total': total, 'active': active, 'by_kind': by_kind,
            'by_confidence': by_confidence, 'by_source': by_source}

def decay_pass(dry_run=False):
    """Decay pass: archive memories below threshold.

    Memórias com baixa confiança (confidence < 0.3) têm meia-vida reduzida
    pela metade — desgastam mais rápido se são hipóteses frágeis.
    """
    memories = _load_memories()
    now = datetime.now()
    kept = []
    archived = 0
    for m in memories:
        # Sinapses Vivas: decisão consolidada nunca arquiva por idade sozinha
        if m.get('kind') == 'decisao' and m.get('confidence', 1.0) >= 0.9 \
                and not m.get('archived'):
            kept.append(m)
            continue
        score = _decay_score(m, now)
        # Ajusta meia-vida para baixa confiança
        if m.get('confidence', 1.0) < 0.3:
            score *= 0.7  # desgaste acelerado
        if score < 0.01:
            archived += 1
            if not dry_run:
                m['archived'] = True
                m['archived_at'] = now.isoformat()
        kept.append(m)
    if not dry_run:
        _save_memories(kept)
    return {'archived': archived, 'remaining': len(kept)}

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    if cmd == 'add':
        task = sys.argv[2] if len(sys.argv) > 2 else ''
        summary = sys.argv[3] if len(sys.argv) > 3 else ''
        kind = sys.argv[4] if len(sys.argv) > 4 else 'episodio'
        no_reindex = '--no-reindex' in sys.argv
        confidence = 1.0
        source_type = 'experiencia'
        source_anchors = None
        for arg in sys.argv:
            if arg.startswith('--confidence='):
                confidence = float(arg.split('=')[1])
            elif arg.startswith('--source='):
                source_type = arg.split('=')[1]
            elif arg.startswith('--anchors='):
                import json
                source_anchors = json.loads(arg.split('=', 1)[1])
        if no_reindex:
            _no_reindex_global = True
            mid = add_memory(task, summary, kind, reindex=False, confidence=confidence, source_type=source_type, source_anchors=source_anchors)
        else:
            mid = add_memory(task, summary, kind, confidence=confidence, source_type=source_type, source_anchors=source_anchors)
        print(f'[OK] Memory #{mid}: {task[:60]} (conf={confidence:.2f}, src={source_type})')
    elif cmd == 'query':
        text = sys.argv[2] if len(sys.argv) > 2 else None
        results = query(text=text)
        for m in results:
            conf = m.get('confidence', 1.0)
            src = m.get('source_type', '?')
            print(f'  [{m["id"]}] {m["kind"]}: {m["task"][:60]} (conf={conf:.2f}, src={src})')
    elif cmd == 'context':
        project = sys.argv[2] if len(sys.argv) > 2 else None
        print(get_context(project=project))
    elif cmd == 'reinforce':
        mid = int(sys.argv[2])
        if reinforce(mid):
            print(f'[OK] Memory #{mid} reinforced')
        else: print(f'[ERR] Memory #{mid} not found')
    elif cmd == 'log':
        task = sys.argv[2] if len(sys.argv) > 2 else ''
        sid = log_session(task=task)
        print(f'[OK] Session logged: {sid}')
    elif cmd == 'semantic':
        # Busca semantica (TF-IDF + cosine) via memory_semantic.search()
        try:
            from memory_semantic import search as sem_search
        except ImportError:
            print('[ERR] memory_semantic.py nao encontrado')
            sys.exit(1)
        if len(sys.argv) < 3:
            print('uso: memory_engine.py semantic <query>')
            sys.exit(1)
        query_text = ' '.join(sys.argv[2:])
        results = sem_search(query_text, k=5)
        if not results:
            print('sem resultados (indice vazio ou nao construido)')
            print('  rode: python scripts/memory_semantic.py build')
        else:
            print(f'Busca semantica: "{query_text}" -> {len(results)} resultados')
            for r in results:
                print(f'  [{r["score"]:.4f}] #{r["id"]} ({r["kind"]}) {r["title"][:90]}')
    elif cmd == 'decay':
        dry = '--dry-run' in sys.argv
        r = decay_pass(dry_run=dry)
        print(f'[OK] Decay pass: {r["archived"]} archived, {r["remaining"]} remaining')
    elif cmd == 'episodio':
        # Query específica: memórias com baixa confiança (hipóteses)
        conf_str = sys.argv[2] if len(sys.argv) > 2 else '0.5'
        try:
            min_conf = float(conf_str)
        except ValueError:
            min_conf = 0.5
        results = query(min_confidence=min_conf)
        print(f'Memorias com confidence < {min_conf}: {len(results)}')
        for m in results:
            conf = m.get('confidence', 1.0)
            src = m.get('source_type', '?')
            print(f'  [{m["id"]}] {m["kind"]}: {m["task"][:60]} (conf={conf:.2f}, src={src})')
    else:  # stats
        s = stats()
        print(f'Memories: {s["total"]} total, {s["active"]} active')
        for k, v in s['by_kind'].items(): print(f'  {k}: {v}')
        print('  by_confidence:')
        for k, v in s.get('by_confidence', {}).items(): print(f'    {k}: {v}')
        print('  by_source:')
        for k, v in s.get('by_source', {}).items(): print(f'    {k}: {v}')
