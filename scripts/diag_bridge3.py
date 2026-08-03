import webview, sys

sys.stdout.reconfigure(line_buffering=True)
print("[diag] iniciando", flush=True)

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
    webview.local_app.stop()

webview.start(fechar)
print("[diag] finalizou", flush=True)
