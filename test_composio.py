import subprocess, json

proc = subprocess.Popen(
    ['python', 'scripts/mcp-composio-server.py'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, cwd='C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau', encoding='utf-8', errors='replace')
init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
tools = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
stdout, stderr = proc.communicate(input=init + tools, timeout=20)
print('STDOUT:')
print(stdout)
print('STDERR:')
print(stderr)