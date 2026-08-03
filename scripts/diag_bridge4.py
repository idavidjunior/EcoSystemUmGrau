import webview, sys, os

sys.stdout.reconfigure(line_buffering=True)
print("[diag] iniciando (storage_path dedicado)", flush=True)

class Api:
    def versao(self):
        print("[diag] versao() chamado", flush=True)
        return "TESTE"

api = Api()
win = webview.create_window("Diag Bridge Test", html="""<html><body>
<script>
function t(){
  try { window.pywebview.api.versao().then(function(v){ document.title='OK:'+v; }); }
  catch(e){ document.title='ERR'; }
}
window.addEventListener('pywebviewready', t);
setTimeout(t, 3000);
</script>
</body></html>""", js_api=api, width=300, height=200)
print("[diag] janela criada", flush=True)

def fechar():
    print("[diag] auto-fechando apos 8s", flush=True)
    for w in webview.windows:
        w.destroy()

sp = os.path.join(os.environ["LOCALAPPDATA"], "pywebview-cerebro-vivo", "udf")
os.makedirs(sp, exist_ok=True)
webview.start(fechar, storage_path=sp, private_mode=False)
print("[diag] finalizou", flush=True)
