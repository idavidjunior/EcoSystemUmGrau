import psutil, time
for i in range(5):
    print(f'--- Iteration {i+1} ---')
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = ' '.join(p.info['cmdline'] or [])
            if 'widget_grafo' in cmd.lower():
                print(f'  PID={p.info["pid"]}, running={p.is_running()}, cmd={cmd[:100]}')
        except:
            pass
    time.sleep(1)