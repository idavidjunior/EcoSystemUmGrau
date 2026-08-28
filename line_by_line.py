# Read the backup and create the fixed version
with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the lines we need to modify
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Add import platform after import time in instancia_unica
    if 'import time' in line and i > 0 and 'def instancia_unica' in ''.join(lines[max(0,i-5):i]):
        new_lines.append(line)
        new_lines.append('    import platform\n')
        i += 1
        continue
    
    # Find the pids loop and wrap it in platform check
    if 'pids = psutil.pids()' in line:
        # Check if next line is 'for pid in pids:'
        if i + 1 < len(lines) and 'for pid in pids:' in lines[i+1]:
            indent = len(line) - len(line.lstrip())
            # Add platform check before the loop
            new_lines.append(' ' * indent + 'if platform.system() != "Windows":\n')
            # The pids line needs 4 more spaces
            new_lines.append(' ' * (indent + 4) + line.lstrip())
            # The next line (for pid in pids:) also needs 4 more spaces
            new_lines.append(' ' * (indent + 4) + lines[i+1].lstrip())
            i += 2
            # Now we need to indent the entire loop body by 4 more spaces
            # until we reach the matching 'except Exception as e:' at the same level
            # This is complex - let's use a different approach
            pass
    else:
        new_lines.append(line)
    i += 1

print("This approach is too complex for line-by-line")