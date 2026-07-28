"""MCP server for knowledge search. Allows agents to query the knowledge base."""
import json, sys, os

BASE = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada'),
                    'Desktop', 'Codigos', 'EcoSystemUmGrau')
sys.path.insert(0, BASE)

def handle_request(req):
    req_id = req.get('id')
    method = req.get('method', '')
    params = req.get('params', {})

    if method == 'initialize':
        return {'jsonrpc': '2.0', 'id': req_id, 'result': {
            'protocolVersion': '2026-07-01',
            'capabilities': {'tools': {}}
        }}

    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': req_id, 'result': {'tools': [
            {
                'name': 'search-knowledge',
                'description': 'Search knowledge graph, memories, and notes. BM25 semantic search.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search term'}
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'get-memory-context',
                'description': 'Get relevant memory context from previous sessions.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'project': {'type': 'string', 'description': 'Project name (optional)'}
                    }
                }
            },
            {
                'name': 'add-memory',
                'description': 'Store a memory from the current session.',
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
                'description': 'Read the CONHECIMENTO.md base (full knowledge dump).',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            }
        ]}}

    if method == 'tools/call':
        tool = params.get('name', '')
        args = params.get('arguments', {})

        if tool == 'search-knowledge':
            q = args.get('query', '')
            import subprocess
            r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'search_knowledge.py'), q],
                             capture_output=True, text=True, cwd=BASE)
            return {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [
                {'type': 'text', 'text': r.stdout or r.stderr or 'No results'}
            ]}}

        if tool == 'get-memory-context':
            import subprocess
            proj = args.get('project', '')
            cmd = [sys.executable, os.path.join(BASE, 'scripts', 'memory_engine.py'), 'context']
            if proj: cmd.extend(['--project', proj])
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE)
            return {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [
                {'type': 'text', 'text': r.stdout or r.stderr or 'No context'}
            ]}}

        if tool == 'add-memory':
            import subprocess
            r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'memory_engine.py'),
                              'add', args.get('task', ''), args.get('summary', ''), args.get('kind', 'episodio')],
                             capture_output=True, text=True, cwd=BASE)
            return {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [
                {'type': 'text', 'text': r.stdout or r.stderr or 'OK'}
            ]}}

        if tool == 'read-conhecimento':
            path = os.path.join(BASE, 'ler-runtime', 'CONHECIMENTO.md')
            try:
                with open(path, encoding='utf-8') as f:
                    text = f.read()[:50000]
                return {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [
                    {'type': 'text', 'text': text}
                ]}}
            except Exception as e:
                return {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [
                    {'type': 'text', 'text': f'Error: {e}'}
                ]}}

        return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32601, 'message': f'Tool not found: {tool}'}}

    return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}

if __name__ == '__main__':
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            if req.get('id') is not None:
                print(json.dumps(resp), flush=True)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            if req.get('id') is not None:
                print(json.dumps({'jsonrpc': '2.0', 'id': req.get('id'), 'error': {'code': -32603, 'message': str(e)}}), flush=True)
