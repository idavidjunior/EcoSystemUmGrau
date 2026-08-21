#!/usr/bin/env python3
import sys, os, psutil

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

# Check PID files
print("=== PID FILES ===")
for f in ['narrador.pid', 'tts_service.pid', 'widget.pid']:
    path = 'runtime/' + f
    if os.path.exists(path):
        pid = int(open(path).read().strip())
        exists = psutil.pid_exists(pid)
        running = psutil.Process(pid).is_running() if exists else 'N/A'
        print(f'{f}: {pid} - exists={exists} - running={running}')
    else:
        print(f'{f}: NOT FOUND')

# Check actual processes
print("\n=== PROCESSES ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or []).lower()
        if 'narrador_desktop' in cmd:
            print(f'Narrador process: PID {p.pid}, cmdline: {str(p.info["cmdline"])[:80]}')
        if 'tts_service' in cmd:
            print(f'TTS process: PID {p.pid}, cmdline: {str(p.info["cmdline"])[:80]}')
        if 'widget_controle' in cmd:
            print(f'Widget process: PID {p.pid}, cmdline: {str(p.info["cmdline"])[:80]}')
    except:
        pass

# Check guardian status
print("\n=== GUARDIAN STATUS ===")
from system_guardian import is_narrador_up, is_tts_service_up, is_widget_up, update_protected_eco_pids
update_protected_eco_pids()
print(f'PROTECTED_ECO_PIDS: {PROTECTED_ECO_PIDS}')
print(f'is_narrador_up: {is_narrador_up()}')
print(f'is_tts_service_up: {is_tts_service_up()}')
print(f'is_widget_up: {is_widget_up()}')