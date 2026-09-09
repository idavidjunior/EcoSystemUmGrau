import urllib.request, json, time, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8096
BASE = f"http://127.0.0.1:{PORT}"

def req(path):
    try:
        r = urllib.request.urlopen(BASE + path, timeout=5)
        return r.getcode(), json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}

# Reset
req("/api/debug/reset-ratelimit")
# Faz 1 request normal para registrar o IP no bucket
urllib.request.urlopen(BASE + "/api/health", timeout=5)
print("Bucket resetado e IP registrado")

# Estado inicial
code, data = req("/api/debug/ratelimit-status")
entry = data.get("entry")
if entry:
    print(f"Inicial: tokens={entry[0]:.2f}")
else:
    print("Inicial: bucket vazio (IP ainda nao registrado)")

# Envia 250 requests e conta
blocked = 0
ok = 0
t0 = time.time()
for i in range(250):
    try:
        r = urllib.request.urlopen(BASE + "/api/health", timeout=5)
        ok += 1
    except urllib.error.HTTPError as e:
        if e.code == 429:
            blocked += 1
        else:
            print(f"Request {i}: unexpected status {e.code}")
            ok += 1
    except Exception as e:
        print(f"Request {i}: error {e}")
        break
elapsed = time.time() - t0

print(f"Resultado: ok={ok} blocked={blocked} elapsed={elapsed:.2f}s")

# Estado final
code, data = req("/api/debug/ratelimit-status")
entry = data.get("entry")
if entry:
    print(f"Final: tokens={entry[0]:.2f}")
else:
    print("Final: entry=None (IP nao encontrado)")
