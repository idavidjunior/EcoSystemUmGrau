"""
EcoDashboard — janela nativa sem navegador.
Abre o dashboard como programa nativo via pywebview.
"""
import webview, sys, time, urllib.request

DASHBOARD_URL = "http://localhost:8766/dashboard"

def verificar_servidor():
    for _ in range(5):
        try:
            r = urllib.request.urlopen(DASHBOARD_URL, timeout=2)
            if r.status == 200:
                return True
        except:
            time.sleep(1)
    return False

def main():
    print("Verificando servidor...")
    if not verificar_servidor():
        print("Servidor HTTP offline. Iniciando...")
        import subprocess, os
        script = os.path.join(os.path.dirname(__file__), "dashboard_http.py")
        subprocess.Popen([sys.executable, script], cwd=os.path.dirname(__file__))
        time.sleep(2)

    print("Abrindo EcoDashboard...")
    window = webview.create_window(
        "EcoSystemUmGrau",
        DASHBOARD_URL,
        width=1400,
        height=900,
        min_size=(900, 600),
        background_color="#0a0e1a",
        text_select=True,
    )
    webview.start(debug=False)

if __name__ == "__main__":
    main()
