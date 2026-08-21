#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

import psutil
from widget_controle_jarvis import _ler_recent_errors

print('=== Current errors ===')
result = _ler_recent_errors()
for err in result:
    print('  ', err)

print()
print('=== Relevant processes ===')
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or []).lower()
        if any(x in cmd for x in ['narrador', 'widget', 'tts_service', 'audit', 'guardian']):
            print(f"  PID {p.pid}: {p.info['name']} - {cmd[:80]}")
    except:
        pass

print()
print('=== PID files ===')
import os
for f in ['narrador.pid', 'tts_service.pid', 'widget.pid']:
    path = 'runtime/' + f
    if os.path.exists(path):
        pid = int(open(path).read().strip())
        exists = psutil.pid_exists(pid)
        print(f'  {f}: {pid} - exists={exists}')
    else:
        print(f'  {f}: NOT FOUND')