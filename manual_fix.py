import re

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the lines we need to modify
# We need to:
# 1. Add 'import platform' at the top of the function
# 2. Wrap the pids loop in a platform check
# 2. Add exception handling for cmdline() call

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Add 'import platform' after 'import time'
    if 'import time' in line and 'import platform' not in line and i > 0 and 'def instancia_unica' in lines[i-1]:
        new_lines.append(line)
        new_lines.append('    import platform\n')
        i += 1
        continue
    
    # Find the pids loop and wrap it in platform check
    if 'pids = psutil.pids()' in line:
        # Add platform check before the loop
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + 'if platform.system() != "Windows":\n')
        new_lines.append(' ' * (indent + 4) + lines[i+1].lstrip())  # for pid in pids:
        # We need to indent the entire loop body
        # This is complex - let's do a different approach
        pass
    
    new_lines.append(line)
    i += 1

# This approach is too complex. Let me just write the whole file.

with open('scripts/widget_grafo.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)