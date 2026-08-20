#!/usr/bin/env python3
import subprocess
import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

# Test bridge detection
said = subprocess.run(
    ['tasklist', '/FI', 'PID eq ', '/NH'],
    capture_output=True, text=True, timeout=10
).stdout
print('tasklist output:')
print(said)
for linha in said.splitlines():
    if 'unified_bridge' in linha.lower():
        print('Found bridge in line:', linha[:60])
    else:
        print('Not found in line:', linha[:60].strip()[:30])