
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
win = webview.create_window("Probe", url="http://127.0.0.1:8096/teste_title.html",
    width=900, height=600, resizable=True)
webview.start()
