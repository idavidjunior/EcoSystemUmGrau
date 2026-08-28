#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script creates the fixed widget_grafo.py by applying precise edits to the backup

with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add 'import platform' after 'import time' in the function
content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

# The old block to replace (from the backup)
old_block = '''            try:
                # Use psutil.pids() for fresh PID list, then check each individually
                pids = psutil.pids()
                for pid in pids:
                    if pid == os.getpid():
                        continue
                    try:
                        p = psutil.Process(pid)
                        # Quick check: is process actually running?
                        running = p.is_running()
                        print(f"[instancia_unica] PID {pid}: is_running()={running}", flush=True)
                        if not running:
                            continue
                        cmdline = p.cmdline()
                        if not cmdline:
                            continue
                        if any(t.lower().strip('"').endswith("widget_grafo.py")
                               for t in cmdline):
                            print(f"[instancia_unica] Outro widget_grafo encontrado: PID={pid}", flush=True)
                            os.close(fd)
                            PID_FILE.unlink()
                            return False
                    except psutil.NoSuchProcess:
                        continue
                    except psutil.AccessDenied:
                        continue
                    except Exception as e:
                        print(f"[instancia_unica] Unexpected exception for PID {pid}: {type(e).__name__}: {e}", flush=True)
                        continue
                except Exception as e:
                    print(f"[instancia_unica] Exception in pids loop: {type(e).__name__}: {e}", flush=True)
                    pass'''

new_block = '''            try:
                # On Windows, psutil.pids() can return stale PIDs.
                # Skip process scanning on Windows to avoid false positives.
                # The PID file itself is the authoritative lock.
                if platform.system() != "Windows":
                    pids = psutil.pids()
                    for pid in pids:
                        if pid == os.getpid():
                            continue
                        try:
                            p = psutil.Process(pid)
                            running = p.is_running()
                            print(f"[instancia_unica] PID {pid}: is_running()={running}", flush=True)
                            if not running:
                                continue
                            try:
                                cmdline = p.cmdline()
                            except psutil.NoSuchProcess:
                                continue
                            if not cmdline:
                                continue
                            if any(t.lower().strip('"').endswith("widget_grafo.py")
                                   for t in cmdline):
                                print(f"[instancia_unica] Outro widget_grafo encontrado: PID={pid}", flush=True)
                                os.close(fd)
                                PID_FILE.unlink()
                                return False
                        except psutil.NoSuchProcess:
                            continue
                        except psutil.AccessDenied:
                            continue
                        except Exception as e:
                            print(f"[instancia_unica] Unexpected exception for PID {pid}: {type(e).__name__}: {e}", flush=True)
                            continue
                except Exception as e:
                    print(f"[instancia_unica] Exception in pids loop: {type(e).__name__}: {e}", flush=True)
                    pass'''

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make replacements
content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

# Find the exact block to replace by locating unique markers
start_marker = '# Use psutil.pids() for fresh PID list, then check each individually'
end_marker = '            except FileExistsError:'

# Find the start and end positions
start_pos = content.find(start_marker)
if start_pos == -1:
    print("ERROR: start marker not found")
    exit(1)

# Find the end of the block - look for 'except FileExistsError:' after the block
# The block ends with 'pass' followed by blank line then 'os.write(fd, me.encode())'
# Actually, let's be more precise - find the exact block

# Let's find the block by looking for the unique structure
import re

# Pattern to match the old block
pattern = r'(\s+try:\s*\n\s+# Use psutil\.pids\(\) for fresh PID list, then check each individually\n\s+pids = psutil\.pids\(\).+?pass\s+\n\s+os\.write\(fd, me\.encode\(\)\))'

# Actually, let's do a more robust replacement by finding the function and doing precise edits

print("Reading file...")
with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function boundaries
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'def instancia_unica():' in line:
        start_idx = i
    if start_idx is not None and 'class Api:' in line:
        end_idx = i
        break

print(f"Function spans lines {start_idx} to {end_idx}")

# Now let's make the edits line by line
new_lines = []
in_function = False
added_platform_import = False
in_pids_loop = False
platform_check_added = False

for i, line in enumerate(lines):
    # Add import platform after import time
    if 'import time' in line and not added_platform_import and 'def instancia_unica' in ''.join(lines[max(0,i-3):i]):
        new_lines.append(line)
        new_lines.append('    import platform\n')
        added_platform_import = True
        continue
    
    # Detect the start of the pids loop block
    if 'pids = psutil.pids()' in line and 'for pid in pids:' in ''.join(lines[i:i+3]):
        indent = len(line) - len(line.lstrip())
        # Add platform check before the loop
        new_lines.append(' ' * len(line) - len(line.lstrip()) + 'if platform.system() != "Windows":\n')
        # The next line is 'for pid in pids:' - indent it by 4 more spaces
        # We need to indent the entire loop body by 4 more spaces
        # This is tricky - let's just add the platform check and continue normally
        new_lines.append(' ' * indent + 'if platform.system() != "Windows":\n')
        new_lines.append(line)  # pids = psutil.pids()
        in_pids_loop = True
        platform_check_added = True
        continue
    
    if in_pids_loop and 'for pid in pids:' in line:
        # Indent this line by 4 more spaces
        new_lines.append('    ' + line)
        continue
    
    # This is getting too complex. Let's write the whole file.
    new_lines.append(line)

print("Writing line-by-line approach is too complex. Writing complete fixed file...")