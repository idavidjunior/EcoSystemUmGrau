"""
EcoDashboard — janela nativa sem navegador.
Abre o dashboard como programa nativo via pywebview.
"""
import webview, sys, time, urllib.request, subprocess, os

DASHBOARD_URL = "http://localhost:8766/dashboard"
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

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
    if not verificar_servidor():
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        subprocess.Popen([pythonw, os.path.join(SCRIPTS_DIR, "dashboard_http.py")],
                         cwd=SCRIPTS_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(2)

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
