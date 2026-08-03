import webview, sys, os, time

sys.stdout.reconfigure(line_buffering=True)
print("[diag] iniciando", flush=True)

class Api:
    def versao(self):
        print("[diag] versao() chamado", flush=True)
        return "TESTE"
    def guardar_geo(self, x, y, w, h):
        print(f"[diag] guardar_geo({x},{y},{w},{h})", flush=True)

api = Api()
win = webview.create_window("Diag Bridge Test", html="<h1>ok</h1>", js_api=api, width=300, height=200)
print("[diag] janela criada", flush=True)

def rodar():
    print("[diag] pywebview.start rodando", flush=True)

webview.start(rodar)
print("[diag] finalizou", flush=True)
