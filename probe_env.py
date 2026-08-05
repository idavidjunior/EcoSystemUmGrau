import os
from pathlib import Path

env = Path('scripts/.env').read_text(encoding='utf-8')
v_env = None
for ln in env.splitlines():
    if ln.startswith('OPENCODE_SERVER_PASSWORD='):
        v_env = ln.split('=', 1)[1]
        break

v_os = os.environ.get('OPENCODE_SERVER_PASSWORD', '')
print('len .env raw:', len(v_env) if v_env else 0)
print('len os.environ:', len(v_os))
print('repr .env:', repr(v_env)[:60] if v_env else 'None')
print('repr os:', repr(v_os)[:60])
print('match:', v_env == v_os)
