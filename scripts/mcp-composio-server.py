"""MCP server local - proxy do Composio (streamable HTTP).

Recebe JSON-RPC pelo stdin (padrao stdio do OpenCode), encaminha como POST
para o endpoint gerenciado https://connect.composio.dev/mcp autenticado com
x-consumer-api-key (COMPOSIO_API_KEY) e normaliza a resposta (SSE ou JSON puro)
de volta para JSON-RPC no stdout.

100% stdlib. Chave carregada de env ou scripts/.env (fonte de secrets do ecossistema).
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = str(Path(__file__).resolve().parent.parent)
ENDPOINT = 'https://connect.composio.dev/mcp'
TIMEOUT = 90


def _load_dotenv():
    """Carrega scripts/.env apenas para variaveis ainda nao definidas."""
    try:
        env_file = os.path.join(BASE, 'scripts', '.env')
        if os.path.isfile(env_file):
            with open(env_file, encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, _, v = line.partition('=')
                    k = k.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v.strip()
    except Exception:
        pass


def _remote_post(req):
    key = os.environ.get('COMPOSIO_API_KEY', '').strip()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'x-consumer-api-key': key,
    }
    body = json.dumps(req, ensure_ascii=False).encode('utf-8')
    rq = urllib.request.Request(ENDPOINT, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(rq, timeout=TIMEOUT) as resp:
        return resp.read().decode('utf-8', errors='replace')


def _sse_blocks(raw):
    """Separa eventos SSE (blocos de linhas data: separados por linha em branco)."""
    blocks = []
    curr = []
    for line in raw.splitlines():
        if not line.strip():
            if curr:
                blocks.append(''.join(curr))
                curr = []
            continue
        if line.startswith('data:'):
            curr.append(line[len('data:'):].strip() + '\n')
    if curr:
        blocks.append(''.join(curr))
    return blocks


def _remote_req(req):
    """Encaminha ao remoto e devolve a resposta JSON-RPC correspondente."""
    raw = _remote_post(req)
    rid = req.get('id')
    blocks = _sse_blocks(raw)
    if blocks:
        for b in blocks:
            try:
                obj = json.loads(b)
            except Exception:
                continue
            if obj.get('id') == rid or (rid is None and 'id' not in obj):
                return obj
        try:
            return json.loads(blocks[0])
        except Exception:
            return {'jsonrpc': '2.0', 'id': rid,
                    'error': {'code': -32700, 'message': 'resposta remota invalida'}}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return {'jsonrpc': '2.0', 'id': rid,
                'error': {'code': -32603, 'message': 'resposta remota nao-JSON' + (': ' + raw[:200] if raw else '')}}


def handle(req):
    rid = req.get('id')
    method = req.get('method', '')
    params = req.get('params', {})

    if not os.environ.get('COMPOSIO_API_KEY', '').strip():
        return {'jsonrpc': '2.0', 'id': rid,
                'error': {'code': -32002, 'message': 'COMPOSIO_API_KEY nao definida (scripts/.env ou env)'}}

    # Clientes minimalistas (ex.: preflight, servers legados) enviam initialize
    # com params vazio. O protocolo 2025-03-26 exige protocolVersion/clientInfo.
    if method == 'initialize':
        params = dict(params or {})
        params.setdefault('protocolVersion', '2025-03-26')
        params.setdefault('capabilities', {})
        params.setdefault('clientInfo',
                          {'name': 'eco-composio-wrapper', 'version': '1.0'})
        req = dict(req)
        req['params'] = params

    try:
        return _remote_req(req)
    except Exception as e:
        return {'jsonrpc': '2.0', 'id': rid,
                'error': {'code': -32603, 'message': f'Composio remoto: {str(e)[:200]}'}}


def _self_test():
    """Initialize + tools/list com o remoto, sem depender de stdin."""
    init = handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                   'params': {'protocolVersion': '2025-03-26',
                              'capabilities': {},
                              'clientInfo': {'name': 'eco-composio', 'version': '1.0'}}})
    if init.get('error'):
        print(f'[FAIL] initialize: {init["error"].get("message")}', file=sys.stderr)
        return 1
    tools = handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    if tools.get('error'):
        print(f'[FAIL] tools/list: {tools["error"].get("message")}', file=sys.stderr)
        return 1
    n = len((tools.get('result') or {}).get('tools', []))
    print(f'[OK] initialize + tools/list ({n} ferramentas do Composio)', file=sys.stderr)
    return 0


if __name__ == '__main__':
    _load_dotenv()
    if '--self-test' in sys.argv:
        sys.exit(_self_test())
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        if req.get('method') == 'notifications/initialized' and req.get('id') is None:
            continue
        resp = handle(req)
        if resp and req.get('id') is not None:
            line_out = json.dumps(resp, ensure_ascii=False)
            sys.stdout.write(line_out + '\n')
            sys.stdout.flush()