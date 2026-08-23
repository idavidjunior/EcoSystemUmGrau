"""Runtime State: estado persistente do Ecossistema.

O Runtime mantém continuamente o estado operacional: projeto ativo, objetivo
atual, última tarefa, contexto, agentes ativos, memória carregada, pendências,
checkpoints e histórico resumido. Nenhuma conversa é sessão isolada: toda
sessão restaura este estado antes de processar.

Uso CLI:
  python scripts/runtime_state.py status                 # mostra estado
  python scripts/runtime_state.py set <key> <value>      # atualiza campo (projeto/objetivo/tarefa/contexto)
  python scripts/runtime_state.py add-agent <nome>       # registra agente ativo
  python scripts/runtime_state.py drop-agent <nome>      # remove agente ativo
  python scripts/runtime_state.py pending add <texto>    # adiciona pendência
  python scripts/runtime_state.py pending done <id>      # conclui pendência
  python scripts/runtime_state.py checkpoint [label]     # salva checkpoint
  python scripts/runtime_state.py restore [id]           # restaura checkpoint (padrão: último)
  python scripts/runtime_state.py note <texto>           # adiciona linha ao histórico resumido
  python scripts/runtime_state.py reset                  # zera estado (mantém checkpoints)
"""

import argparse
import json
import os
import sys
import shutil
from datetime import datetime

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME_DIR = os.path.join(BASE, 'runtime')
STATE_FILE = os.path.join(RUNTIME_DIR, 'state.json')
CHECKPOINTS_DIR = os.path.join(RUNTIME_DIR, 'checkpoints')
MAX_CHECKPOINTS = 30

DEFAULT_STATE = {
    'schema_version': 1,
    'updated_at': '',
    'active_project': '',
    'objective': '',
    'last_task': '',
    'operational_context': '',
    'active_agents': [],
    'loaded_memory': [],
    'pending': [],
    'history': [],
    'last_checkpoint': None,
    'session_greeted': False,
}


def _ensure_dirs():
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)


def _now():
    return datetime.now().isoformat(timespec='seconds')


def load_state():
    _ensure_dirs()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            data = json.load(f)
        for k, v in DEFAULT_STATE.items():
            data.setdefault(k, v)
        return data
    state = dict(DEFAULT_STATE)
    state['updated_at'] = _now()
    save_state(state)
    return state


def save_state(state):
    _ensure_dirs()
    state['updated_at'] = _now()
    tmp = STATE_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)


def set_field(key, value):
    state = load_state()
    if key in ('active_project', 'objective', 'last_task', 'operational_context'):
        state[key] = value
        save_state(state)
        return f'[OK] {key} = {value}'
    return f'[ERR] chave desconhecida: {key}'


def add_agent(name):
    state = load_state()
    if name not in state['active_agents']:
        state['active_agents'].append(name)
    save_state(state)
    return f'[OK] agente ativo: {name}'


def drop_agent(name):
    state = load_state()
    if name in state['active_agents']:
        state['active_agents'].remove(name)
    save_state(state)
    return f'[OK] agente removido: {name}'


def add_pending(text):
    state = load_state()
    pid = max([p.get('id', 0) for p in state['pending']], default=0) + 1
    state['pending'].append({'id': pid, 'text': text, 'done': False,
                             'created': _now()})
    save_state(state)
    return f'[OK] pendência #{pid}: {text}'


def done_pending(pid):
    state = load_state()
    for p in state['pending']:
        if p['id'] == pid:
            p['done'] = True
            save_state(state)
            return f'[OK] pendência #{pid} concluída'
    return f'[ERR] pendência #{pid} não encontrada'


def add_note(text):
    state = load_state()
    state['history'].append({'timestamp': _now(), 'text': text})
    state['history'] = state['history'][-30:]
    save_state(state)
    return f'[OK] histórico: {text}'


def save_checkpoint(label='auto'):
    state = load_state()
    cid = datetime.now().strftime('%Y%m%d_%H%M%S')
    cpath = os.path.join(CHECKPOINTS_DIR, f'{cid}_{label}.json')
    cp = {'id': cid, 'label': label, 'created': _now(), 'state': state}
    tmp = cpath + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)
    os.replace(tmp, cpath)
    state['last_checkpoint'] = cid
    save_state(state)
    _cleanup_old()
    return cid


def _checkpoint_path(cid=None):
    if cid:
        for f in os.listdir(CHECKPOINTS_DIR):
            if f.startswith(cid):
                return os.path.join(CHECKPOINTS_DIR, f)
        return None
    files = sorted(os.listdir(CHECKPOINTS_DIR), reverse=True)
    if not files:
        return None
    return os.path.join(CHECKPOINTS_DIR, files[0])


def load_checkpoint(cid=None):
    path = _checkpoint_path(cid)
    if not path:
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def restore(cid=None):
    cp = load_checkpoint(cid)
    if not cp:
        return '[ERR] checkpoint não encontrado'
    state = cp['state']
    state['last_checkpoint'] = cp['id']
    save_state(state)
    return f"[OK] restaurado checkpoint {cp['id']} ({cp.get('label')})"


def list_checkpoints():
    files = sorted(os.listdir(CHECKPOINTS_DIR), reverse=True)
    out = []
    for f in files:
        with open(os.path.join(CHECKPOINTS_DIR, f), encoding='utf-8') as fh:
            cp = json.load(fh)
        out.append(f"{cp['id']} | {cp.get('label')} | {cp.get('created')}")
    return out


def _cleanup_old():
    files = sorted(os.listdir(CHECKPOINTS_DIR))
    for f in files[:max(0, len(files) - MAX_CHECKPOINTS)]:
        os.remove(os.path.join(CHECKPOINTS_DIR, f))


def reset():
    state = dict(DEFAULT_STATE)
    state['updated_at'] = _now()
    save_state(state)
    return '[OK] estado zerado (checkpoints preservados)'


def render_status(state):
    pending_open = [p for p in state['pending'] if not p['done']]
    lines = [
        '=== RUNTIME STATE ===',
        f"Projeto ativo:  {state['active_project'] or '(nenhum)'}",
        f"Objetivo:       {state['objective'] or '(nenhum)'}",
        f"Última tarefa:  {state['last_task'] or '(nenhuma)'}",
        f"Agentes ativos: {', '.join(state['active_agents']) or '(nenhum)'}",
        f"Pendências:     {len(pending_open)} aberta(s)",
    ]
    if state['operational_context']:
        lines.append(f"Contexto:       {state['operational_context']}")
    if state['loaded_memory']:
        lines.append(f"Memória carregada: {', '.join(state['loaded_memory'])}")
    if pending_open:
        lines.append('')
        for p in pending_open:
            lines.append(f"  [#{p['id']}] {p['text']}")
    if state['history']:
        lines.append('')
        for h in state['history'][-5:]:
            lines.append(f"  · {h['timestamp'][:19]} {h['text']}")
    return '\n'.join(lines)


def _import_frases_manager():
    """Importa frases_manager dinamicamente."""
    import sys
    import os
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import frases_manager
    return frases_manager


def generate_spontaneous_greeting(state):
    """Gera saudação espontânea curta (3-4 linhas) estilo Jarvis — contextual, variada, anti-repetição."""
    if state.get('session_greeted', False):
        return None
    
    try:
        fm = _import_frases_manager()
        saudacao = fm.saudacao_dinamica()
        # Adicionar contexto leve do estado do EcoSystem
        projeto = state.get('active_project', 'EcoSystem')
        pendencias_list = [p for p in state.get('pending', []) if not p.get('done')]
        pendencias_count = len(pendencias_list)
        
        # Contexto extra: projeto + pendências
        contexto_extra = f" {projeto} ativo"
        if pendencias_count:
            contexto_extra += f" — {pendencias_count} pendências"
        
        # Se a saudação já tem ponto final, adicionar contexto depois
        if saudacao.endswith('.'):
            saudacao = saudacao[:-1] + contexto_extra + '.'
        else:
            saudacao = saudacao + contexto_extra + '.'
        
        return saudacao
    except Exception as e:
        # Fallback para templates simples se frases_manager falhar
        import random
        GREETING_TEMPLATES = [
            "EcoSystem no ar. {projeto} ativo — build OK no {device}. {pendencias} pendências técnicas carregadas.",
            "Sistema operante. {projeto} rodando — {contexto}. Gaps: {gaps}.",
            "Runtime restaurado. Memória: {mem_count} entradas, última tarefa: {last_task}. Pendências: {pendencias} abertas.",
            "EcoSystemUmGrau ativo. {projeto} v{versao} no {device}. Checkpoint: {checkpoint}. {pendencias} itens pendentes.",
        ]
        
        projeto = state.get('active_project', 'EcoSystem')
        dispositivo = 'MIUI'
        pendencias_list = [p for p in state.get('pending', []) if not p.get('done')]
        pendencias_count = len(pendencias_list)
        
        gaps = []
        for p in pendencias_list[:3]:
            texto = p.get('text', '')
            if 'SQLite' in texto:
                gaps.append('SQLite incremental')
            elif 'data' in texto.lower() or 'incremental' in texto.lower():
                gaps.append('scan por data')
            elif 'export' in texto.lower() or 'csv' in texto.lower() or 'json' in texto.lower():
                gaps.append('exportação')
            elif 'widget' in texto.lower():
                gaps.append('widget')
            elif 'shizuku' in texto.lower() or 'root' in texto.lower():
                gaps.append('Shizuku/root')
        gaps_str = ', '.join(gaps) if gaps else 'nenhum crítico'
        
        mem_count = len(state.get('loaded_memory', []))
        last_task = state.get('last_task', 'inicialização')[:50]
        checkpoint = state.get('last_checkpoint', 'recente')
        versao = '2.1'
        
        contexto = state.get('operational_context', '')
        if 'scan' in contexto.lower():
            scan_info = 'scan ativo'
        else:
            scan_info = 'pronto'
        
        template = random.choice(GREETING_TEMPLATES)
        return template.format(
            projeto=projeto,
            device=dispositivo,
            pendencias=pendencias_count,
            contexto=scan_info,
            gaps=gaps_str,
            mem_count=mem_count,
            last_task=last_task,
            checkpoint=checkpoint,
            versao=versao,
        )


def mark_session_greeted():
    """Marca a sessão como já saudada."""
    state = load_state()
    state['session_greeted'] = True
    save_state(state)
    return '[OK] sessão marcada como saudada'


def reset_session_greeting():
    """Reseta a saudação para nova sessão (útil para testes)."""
    state = load_state()
    state['session_greeted'] = False
    save_state(state)
    return '[OK] saudação de sessão resetada'


def main():
    parser = argparse.ArgumentParser(description='Runtime State — estado persistente do Ecossistema')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('status')
    sub.add_parser('reset')
    p_set = sub.add_parser('set')
    p_set.add_argument('key')
    p_set.add_argument('value')
    p_agent = sub.add_parser('add-agent')
    p_agent.add_argument('name')
    p_drop = sub.add_parser('drop-agent')
    p_drop.add_argument('name')
    p_pend = sub.add_parser('pending')
    p_pend.add_argument('action', choices=['add', 'done'])
    p_pend.add_argument('value', nargs='+')
    p_cp = sub.add_parser('checkpoint')
    p_cp.add_argument('label', nargs='?', default='auto')
    p_rest = sub.add_parser('restore')
    p_rest.add_argument('cid', nargs='?', default=None)
    p_list = sub.add_parser('list')
    p_note = sub.add_parser('note')
    p_note.add_argument('text', nargs='+')
    sub.add_parser('greeting')
    sub.add_parser('reset-greeting')

    args = parser.parse_args()
    cmd = args.cmd or 'status'

    if cmd == 'status':
        print(render_status(load_state()))
    elif cmd == 'set':
        print(set_field(args.key, args.value))
    elif cmd == 'add-agent':
        print(add_agent(args.name))
    elif cmd == 'drop-agent':
        print(drop_agent(args.name))
    elif cmd == 'pending':
        text = ' '.join(args.value)
        if args.action == 'add':
            print(add_pending(text))
        else:
            print(done_pending(int(text)))
    elif cmd == 'checkpoint':
        cid = save_checkpoint(args.label)
        print(f'[OK] checkpoint salvo: {cid}')
    elif cmd == 'restore':
        print(restore(args.cid))
    elif cmd == 'list':
        print('\n'.join(list_checkpoints()) or '(nenhum checkpoint)')
    elif cmd == 'note':
        print(add_note(' '.join(args.text)))
    elif cmd == 'greeting':
        state = load_state()
        greeting = generate_spontaneous_greeting(state)
        if greeting:
            print(greeting)
            mark_session_greeted()
        else:
            print('[INFO] sessão já saudada')
    elif cmd == 'reset-greeting':
        print(reset_session_greeting())
    elif cmd == 'reset':
        print(reset())
    return 0


if __name__ == '__main__':
    sys.exit(main())
