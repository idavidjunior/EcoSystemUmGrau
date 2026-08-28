# This script applies the precise fix to widget_grafo.py
# It reads the file line by line and makes targeted changes

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 1. Add 'import platform' after 'import time' in instancia_unica
    if 'import time' in line and i > 0 and 'def instancia_unica' in ''.join(lines[max(0,i-5):i]):
        new_lines.append(line)
        if 'import platform' not in lines[i+1]:
            new_lines.append('    import platform\n')
        i += 1
        continue
    
    # Find the pids loop and wrap it in platform check
    if 'pids = psutil.pids()' in line and i > 0 and 'for pid in pids:' in lines[i+1]:
        # Get indentation
        indent = len(line) - len(line.lstrip())
        # Replace the line and add platform check
        new_lines.append(' ' * indent + 'if platform.system() != "Windows":\n')
        new_lines.append(' ' * (indent + 4) + lines[i+1])  # for pid in pids:
        # We need to indent the entire loop body by 4 more spaces
        # This is complex - let's just mark that we need to indent the next block
        i += 1
        continue
    
    # If we're inside the pids loop, indent everything by 4 more spaces until we hit the matching dedent
    # This is too complex for line-by-line. Let's use a different approach.
    
    new_lines.append(line)
    i += 1

# This approach is too fragile. Let's just write the whole fixed file.

print("Need to write complete fixed file instead")