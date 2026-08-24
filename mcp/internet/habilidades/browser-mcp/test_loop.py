import asyncio
import json
import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\mcp\internet\habilidades\browser-mcp")

async def _read_frame(stream):
    peek = stream.peek(1)
    if not peek:
        return None

    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        return None

    headers = {}
    if b":" in first:
        key, value = first.split(b":", 1)
        headers[key.strip().lower()] = value.strip()
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length <= 0:
        return None
    body = stream.read(length)
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

async def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()

async def main_loop():
    from server import handle
    while True:
        req = await _read_frame(sys.stdin.buffer)
        if req is None:
            break
        resp = await handle(req)
        if resp is not None:
            await _write_frame(sys.stdout.buffer, resp)

asyncio.run(main_loop())