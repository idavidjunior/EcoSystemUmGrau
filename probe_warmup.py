import urllib.request, base64, json, time
from pathlib import Path

pwd = None
for ln in Path('scripts/.env').read_text(encoding='utf-8').splitlines():
    if ln.startswith('OPENCODE_SERVER_PASSWORD='):
        pwd = ln.split('=', 1)[1].strip()
        if pwd.startswith('"') and pwd.endswith('"'):
            pwd = pwd[1:-1]
        break
cred = base64.b64encode(f'opencode:{pwd}'.encode()).decode()

# cria sessao warmup
r = urllib.request.urlopen(urllib.request.Request(
    'http://127.0.0.1:8767/session',
    data=json.dumps({'title': 'warmup'}).encode(),
    headers={'Authorization': f'Basic {cred}', 'Content-Type': 'application/json'},
    method='POST'), timeout=30)
sid = json.loads(r.read())['id']
print('sessao:', sid)

body = json.dumps({'parts': [{'type': 'text', 'text': 'oi'}]}).encode()
req = urllib.request.Request(f'http://127.0.0.1:8767/session/{sid}/message', data=body,
                            headers={'Authorization': f'Basic {cred}',
                                     'Content-Type': 'application/json'},
                            method='POST')
print('aquecendo (180s)...')
t0 = time.time()
try:
    r = urllib.request.urlopen(req, timeout=180)
    dt = time.time() - t0
    data = json.loads(r.read())
    parts = data.get('parts', [])
    text = next((p.get('text', '') for p in parts if p.get('text', '')), '')
    print(f'OK em {dt:.1f}s: {text[:200]}')
except Exception as e:
    print(f'FALHA em {time.time()-t0:.1f}s: {e}')
