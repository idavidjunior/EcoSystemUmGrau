import subprocess, sys, time, os
base = r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau"
out = r"C:\Users\DAVIDJ~1\AppData\Local\Temp\opencode\w_out.txt"
err = r"C:\Users\DAVIDJ~1\AppData\Local\Temp\opencode\w_err.txt"
for f in (out, err):
    if os.path.exists(f):
        os.remove(f)
with open(out, 'w') as fo, open(err, 'w') as fe:
    p = subprocess.Popen([sys.executable, 'scripts/widget_grafo.py'],
                         cwd=base, stdout=fo, stderr=fe)
    print('PID:', p.pid)
    time.sleep(15)
    print('poll:', p.poll())
    print('--- STDOUT ---')
    print(open(out, encoding='utf-8', errors='replace').read())
    print('--- STDERR ---')
    print(open(err, encoding='utf-8', errors='replace').read())
