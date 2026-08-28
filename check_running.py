import psutil
for p in psutil.process_iter(['pid', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'widget_grafo' in cmd.lower():
            print(f'PID={p.info["pid"]}, running={p.is_running()}, cmd={cmd[:100]}')
    except:
        pass