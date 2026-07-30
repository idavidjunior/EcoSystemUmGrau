"""MCP server for knowledge search. Robust, self-contained, no external deps."""
import json, sys, os, subprocess

BASE = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada'),
                    'Desktop', 'Codigos', 'EcoSystemUmGrau')

TOOLS = [
    {
        'name': 'search-knowledge',
        'description': 'Search knowledge graph, memories, and notes via BM25 semantic search.',
        'inputSchema': {
            'type': 'object',
            'properties': {'query': {'type': 'string', 'description': 'Search term'}},
            'required': ['query']
        }
    },
    {
        'name': 'get-memory-context',
        'description': 'Get relevant memory context from previous sessions (Ebbinghaus decay).',
        'inputSchema': {
            'type': 'object',
            'properties': {'project': {'type': 'string', 'description': 'Optional project filter'}}
        }
    },
    {
        'name': 'add-memory',
        'description': 'Store a memory from the current session (cross-session persistence).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'task': {'type': 'string', 'description': 'Task description'},
                'summary': {'type': 'string', 'description': 'What was learned'},
                'kind': {'type': 'string', 'description': 'decisao|padrao|episodio|erro'}
            },
            'required': ['task', 'summary']
        }
    },
    {
        'name': 'read-conhecimento',
        'description': 'Read the CONHECIMENTO.md base (full knowledge dump, ~46KB).',
        'inputSchema': {'type': 'object', 'properties': {}}
    }
]

def handle(req):
    rid = req.get('id')
    method = req.get('method', '')
    params = req.get('params', {})

    if method == 'initialize':
        return {'jsonrpc': '2.0', 'id': rid, 'result': {
            'protocolVersion': '2024-11-05',
            'serverInfo': {'name': 'eco-knowledge', 'version': '1.0.0'},
            'capabilities': {'tools': {}}}}

    if method in ('notifications/initialized',):
        return {'jsonrpc': '2.0', 'id': rid, 'result': {}} if rid else None

    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': rid, 'result': {'tools': TOOLS}}

    if method == 'tools/call':
        tool = params.get('name', '')
        args = params.get('arguments', {})
        try:
            return handle_tool(tool, args, rid)
        except Exception as e:
            return {'jsonrpc': '2.0', 'id': rid, 'error': {'code': -32603, 'message': str(e)}}

    # Unknown method
    return {'jsonrpc': '2.0', 'id': rid, 'result': {}} if rid else None

def handle_tool(tool, args, rid):
    if tool == 'search-knowledge':
        q = args.get('query', '')
        if not q:
            return {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': 'No query'}]}}
        r = subprocess.run(
            [sys.executable, os.path.join(BASE, 'scripts', 'search_knowledge.py'), q],
            capture_output=True, text=True, cwd=BASE, timeout=30)
        text = (r.stdout or r.stderr or f'No results for: {q}')[:10000]
        return {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': text}]}}

    if tool == 'get-memory-context':
        proj = args.get('project', '')
        cmd = [sys.executable, os.path.join(BASE, 'scripts', 'memory_engine.py'), 'context']
        if proj: cmd.extend(['--project', proj])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE, timeout=15)
        text = (r.stdout or 'No context available')[:10000]
        return {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': text}]}}

    if tool == 'add-memory':
        task = args.get('task', '')
        summary = args.get('summary', '')
        kind = args.get('kind', 'episodio')
        r = subprocess.run(
            [sys.executable, os.path.join(BASE, 'scripts', 'memory_engine.py'),
             'add', task, summary, kind],
            capture_output=True, text=True, cwd=BASE, timeout=15)
        text = (r.stdout or r.stderr or 'OK')[:500]
        return {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': text}]}}

    if tool == 'read-conhecimento':
        path = os.path.join(BASE, 'ler-runtime', 'CONHECIMENTO.md')
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()[:30000]
        except FileNotFoundError:
            text = 'CONHECIMENTO.md not found. Run ecosystem sync first.'
        return {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': text}]}}

    return {'jsonrpc': '2.0', 'id': rid, 'error': {'code': -32601, 'message': f'Tool not found: {tool}'}}

if __name__ == '__main__':
    # Self-test on startup
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle(req)
            if resp is not None:
                print(json.dumps(resp), flush=True)
        except json.JSONDecodeError:
            pass
