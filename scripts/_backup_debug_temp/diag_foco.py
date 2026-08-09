"""Teste definitivo: physics desativada + focus, para ver se canvas aparece
no pywebview. Isola se o problema e o throttling do rAF sem foco."""
html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>t2</title>
<style>body{margin:0;background:#111}#net{width:100vw;height:100vh}</style>
<script src="vendor/vis-network.min.js"></script>
</head>
<body>
<div id="net"></div>
<script>
  window.__t0__=Date.now();
  window.addEventListener('error', function(e){ window.__jsErr__=(window.__jsErr__||[]).concat(String(e.message||e)); });
  setTimeout(function(){
    var c=[{id:1,label:'A'},{id:2,label:'B'},{id:3,label:'C'}];
    var ed=[{from:1,to:2},{from:2,to:3}];
    var n=new vis.DataSet(c); var e=new vis.DataSet(ed);
    var container=document.getElementById('net');
    try{
      var net=new vis.Network(container,{nodes:n,edges:e},{physics:{enabled:false,stabilization:false},layout:{improvedLayout:false}});
      window.__ok__=true;
    }catch(err){window.__ok__=String(err&&err.message||err);}
    window.__t1__=Date.now();
  },0);
</script>
</body>
</html>
"""
import io
io.open('docs/teste_foco.html', 'w', encoding='utf-8').write(html)
print('OK')

import subprocess, sys, os, time, threading
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
env = dict(os.environ); env["PYWEBVIEW_LOG"] = "DEBUG"
code = r'''
import sys, os, time, threading
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
win = webview.create_window("TF", url="http://127.0.0.1:8094/teste_foco.html", width=700, height=500, resizable=True)
def M(tag):
    try:
        r = win.evaluate_js("JSON.stringify({ok:typeof window.__ok__, jsErr:window.__jsErr__, ms:window.__t1__?window.__t1__-window.__t0__:0, canvas:document.querySelectorAll('#net canvas').length})")
        print("[debug]" + tag + ": " + r, flush=True)
    except Exception as e:
        print("[debug]" + tag + " E: " + repr(e), flush=True)
def onload():
    threading.Timer(3.0, lambda: M("+3s")).start()
    threading.Timer(8.0, lambda: M("+8s")).start()
win.events.loaded += onload
webview.start()
'''
tmp = os.path.join(ROOT, "scripts", "dbg_foco.py")
open(tmp, "w", encoding="utf-8").write(code)
serv = subprocess.Popen([sys.executable, "-m", "http.server", "8094", "--directory", os.path.join(ROOT, "docs")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
print("PID", p.pid, flush=True)
time.sleep(15)
p.terminate()
out, err = p.communicate(timeout=10)
print(out.decode("utf-8", errors="ignore") if out else "(out vazio)")
print("ERR:", err.decode("utf-8", errors="ignore")[-600:] if err else "(vazio)")
serv.terminate()