"""Memory engine: cross-session memory with Ebbinghaus decay."""
import json, os, re, sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
MEM_DIR = os.path.join(BASE, 'conhecimento', 'memoria')
SESSIONS_DIR = os.path.join(MEM_DIR, 'sessions')
MEMORIES_FILE = os.path.join(MEM_DIR, 'memories.json')
INDEX_FILE = os.path.join(MEM_DIR, 'index.json')

HALF_LIFE = {
    'decisao': 30,     # decisions last 30 days
    'padrao': 60,      # patterns last 60 days
    'episodio': 7,     # episodes last 7 days
    'erro': 90,        # errors last 90 days
    'contexto': 14,    # context lasts 14 days
    'preferencia': 365 # preferences last 1 year
}

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
    last_acc = datetime.fromisoformat(memory.get('last_accessed', memory['created_at']))
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
               strength=1.0, metadata=None):
    """Add a consolidated memory with decay metadata."""
    memories = _load_memories()
    now = datetime.now()
    memory = {
        'id': _next_id(memories),
        'kind': kind,
        'task': task,
        'summary': summary,
        'project': project,
        'tags': tags or [],
        'metadata': metadata or {},
        'strength': strength,
        'access_count': 0,
        'created_at': now.isoformat(),
        'last_accessed': now.isoformat()
    }
    memories.append(memory)
    _save_memories(memories)
    return memory['id']

def reinforce(memory_id, delta=0.15):
    """Reinforce a memory when reused."""
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id:
            m['strength'] = min(2.0, m['strength'] + delta)
            m['access_count'] += 1
            m['last_accessed'] = datetime.now().isoformat()
            _save_memories(memories)
            return True
    return False

def query(project=None, tags=None, kind=None, text=None, limit=10,
          min_score=0.05):
    """Search memories with decay scoring and filters."""
    memories = _load_memories()
    now = datetime.now()
    scored = []

    for m in memories:
        score = _decay_score(m, now)
        if score < min_score: continue
        if project and m.get('project') != project: continue
        if kind and m.get('kind') != kind: continue
        if tags and not any(t in m.get('tags', []) for t in tags): continue
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
    active = 0
    for m in memories:
        k = m.get('kind', 'unknown')
        by_kind[k] = by_kind.get(k, 0) + 1
        if _decay_score(m, now) > 0.1: active += 1
    return {'total': total, 'active': active, 'by_kind': by_kind}

def decay_pass(dry_run=False):
    """Decay pass: archive memories below threshold."""
    memories = _load_memories()
    now = datetime.now()
    kept = []
    archived = 0
    for m in memories:
        score = _decay_score(m, now)
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
        mid = add_memory(task, summary, kind)
        print(f'[OK] Memory #{mid}: {task[:60]}')
    elif cmd == 'query':
        text = sys.argv[2] if len(sys.argv) > 2 else None
        results = query(text=text)
        for m in results:
            print(f'  [{m["id"]}] {m["kind"]}: {m["task"][:70]}')
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
    elif cmd == 'decay':
        dry = '--dry-run' in sys.argv
        r = decay_pass(dry_run=dry)
        print(f'[OK] Decay pass: {r["archived"]} archived, {r["remaining"]} remaining')
    else:  # stats
        s = stats()
        print(f'Memories: {s["total"]} total, {s["active"]} active')
        for k, v in s['by_kind'].items(): print(f'  {k}: {v}')
