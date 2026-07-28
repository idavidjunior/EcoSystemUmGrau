"""Debug MCP test"""
import subprocess, json

proc = subprocess.Popen(
    ["python", "scripts/mcp-knowledge-server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, cwd=r"C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau")
init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
tools = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
stdout, stderr = proc.communicate(input=init + tools, timeout=5)
proc.kill()
print("=== STDOUT ===")
print(repr(stdout))
print("=== STDERR ===")
print(repr(stderr))
print("=== LINES ===")
lines = [l for l in stdout.strip().split("\n") if l.strip()]
print(len(lines))
for i, l in enumerate(lines):
    print(f"  [{i}] {l[:200]}")
    try:
        obj = json.loads(l)
        print(f"    result: {'result' in obj}")
        if 'result' in obj:
            print(f"    tools: {'tools' in obj['result']}")
    except Exception as e:
        print(f"    parse: {e}")
