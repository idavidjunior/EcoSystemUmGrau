import http.client, json, time

def get_status():
    c = http.client.HTTPConnection('127.0.0.1', 8096, timeout=3)
    c.request('GET', '/api/debug/ratelimit-status')
    r = c.getresponse()
    d = json.loads(r.read())
    c.close()
    return d

def get_health():
    c = http.client.HTTPConnection('127.0.0.1', 8096, timeout=3)
    c.request('GET', '/api/health')
    r = c.getresponse()
    s = r.status
    r.read()
    c.close()
    return s

# Reset
c = http.client.HTTPConnection('127.0.0.1', 8096, timeout=3)
c.request('GET', '/api/debug/reset-ratelimit')
r = c.getresponse(); r.read(); c.close()

d = get_status()
print(f"RESET: ip={d['ip']} entry={d['entry']} all_ips={d['all_ips']}")

s = get_health()
print(f"REQ1: status={s}")
d = get_status()
print(f"  bucket: entry={d['entry']}")

s = get_health()
print(f"REQ2: status={s}")
d = get_status()
print(f"  bucket: entry={d['entry']}")

# 5 rapid requests
for i in range(5):
    s = get_health()
    print(f"REQ{i+3}: status={s}")
d = get_status()
print(f"  bucket after 7 total: entry={d['entry']}")

# Now send 250 and count
blocked = 0
ok = 0
t0 = time.time()
for i in range(250):
    s = get_health()
    if s == 429:
        blocked += 1
    elif s == 200:
        ok += 1
elapsed = time.time() - t0
d = get_status()
print(f"\n250 RAPID: ok={ok} blocked={blocked} elapsed={elapsed:.2f}s")
print(f"  final bucket: entry={d['entry']}")
