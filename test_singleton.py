import os, psutil
PID_FILE = 'runtime/widget_grafo.pid'
os.makedirs('runtime', exist_ok=True)
try:
    fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    print('created')
    for p in psutil.process_iter(['pid', 'cmdline']):
        if p.info['pid'] == os.getpid():
            continue
        if any(t.lower().strip('"').endswith('widget_grafo.py') for t in (p.info['cmdline'] or [])):
            print('found other:', p.info['pid'], p.info['cmdline'])
            os.close(fd)
            from pathlib import Path
            Path(PID_FILE).unlink()
            exit(1)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    print('success')
except Exception as e:
    print('error:', e)