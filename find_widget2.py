import psutil, os
me = str(os.getpid())
print(f'Meu PID: {me}')
for p in psutil.process_iter(['pid', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'widget_grafo' in cmd.lower():
            print(f'Encontrado: PID={p.info["pid"]}, CMD={cmd[:100]}')
    except:
        pass