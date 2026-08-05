import os, sys
sys.path.insert(0, 'scripts')

# Carrega bridge como modulo para ler SERVER_PASS real usado nele
import importlib.util as ilu
spec = ilu.spec_from_file_location("jb", "scripts/jarvis_bridge.py")
m = ilu.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    print("SERVER_USER:", m.SERVER_USER)
    print("SERVER_PASS len:", len(m.SERVER_PASS or ''))
    print("SERVER_PASS first chars:", (m.SERVER_PASS or '')[:16])
    print("SERVE_URL:", m.SERVE_URL)
except Exception as e:
    print("ERRO import:", e)
