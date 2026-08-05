import urllib.request, base64, json
from pathlib import Path

p = Path('scripts/.env').read_text(encoding='utf-8')
pwd = None
for ln in p.splitlines():
    if ln.startswith('OPENCODE_SERVER_PASSWORD='):
        pwd = ln.split('=', 1)[1].strip()
        if pwd.startswith('"') and pwd.endswith('"'):
            pwd = pwd[1:-1]
        elif pwd.startswith("'") and pwd.endswith("'"):
            pwd = pwd[1:-1]
        break

print('senha:', repr(pwd)[:20], 'len=', len(pwd or ''))
cred = base64.b64encode(f'opencode:{pwd}'.encode()).decode()

# GET /session
req = urllib.request.Request('http://127.0.0.1:8767/session',
                            headers={'Authorization': f'Basic {cred}'}, method='GET')
try:
    r = urllib.request.urlopen(req, timeout=10)
    print('GET /session ->', r.status)
except urllib.error.HTTPError as e:
    print('GET /session -> HTTP', e.code)
except Exception as e:
    print('GET /session -> ERR', e)

# POST /session
req = urllib.request.Request('http://127.0.0.1:8767/session',
                            data=json.dumps({'title': 'Jarvis'}).encode(),
                            headers={'Authorization': f'Basic {cred}',
                                     'Content-Type': 'application/json'},
                            method='POST')
try:
    r = urllib.request.urlopen(req, timeout=10)
    print('POST /session ->', r.status, '->', r.read(200))
except urllib.error.HTTPError as e:
    print('POST /session -> HTTP', e.code, ':', e.read(200))
except Exception as e:
    print('POST /session -> ERR', e)
