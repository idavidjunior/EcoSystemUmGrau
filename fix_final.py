#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Read the backup file
with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line numbers for key locations
# We need to:
# 1. Add 'import platform' after 'import time' in instancia_unica
# 2. Wrap the pids loop in a platform check

# Find line numbers
import_time_line = None
pids_line = None
for i, line in enumerate(lines):
    if 'def instancia_unica():' in line:
        func_start = i
    if 'import time' in line and i > 0 and 'def instancia_unica' in ''.join(lines[max(0,i-5):i]):
        import_time_line = i
    if 'pids = psutil.pids()' in line:
        pids_line = i
    if 'def instancia_unica():' in line and i > 0:
        func_start = i
    if 'class Api:' in line:
        class_api_line = i

print(f"import_time_line: {import_time_line}")
print(f"pids_line: {pids_line}")

# Read the whole file as string for easier manipulation
with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import platform
content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

# The exact old block from the backup
old = '''            try:
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

# New block with platform check
new = '''            try:
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

with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

old = '''            try:
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

new = '''            try:
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

with open('scripts/widget_grafo.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

content = content.replace(old_block, new_block)

with open('scripts/widget_grafo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')