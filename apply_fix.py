#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The changes needed:
# 1. Add 'import platform' at the top of instancia_unica function
# 2. Wrap the process scanning loop in a platform check

# Find the function
start = content.find('def instancia_unica():')
func_end = content.find('\nclass Api:')

# Extract the function
func_content = content[start:end]

# Make the changes
# 1. Add import platform after import time
func_content = func_content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

# 2. Wrap the pids loop in platform check
old_loop = '''            try:
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

new_loop = '''            try:
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

# Make the replacements
content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

content = content.replace(
    '''            try:
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
                    pass''',
    '''            try:
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
                    pass''')

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

content = content.replace(
    '''            try:
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
                    pass''',
    '''            try:
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
                    pass''')

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

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

content = content.replace(
    '    import psutil\n    import time\n',
    '    import psutil\n    import time\n    import platform\n'
)

content = content.replace(old_block, new_block)

with open('scripts/widget_grafo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')