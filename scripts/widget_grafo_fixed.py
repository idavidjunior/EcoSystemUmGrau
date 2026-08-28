def instancia_unica():
    import psutil
    import time
    import platform

    me = str(os.getpid())
    print(f"[instancia_unica] Meu PID: {me}, PID_FILE existe: {PID_FILE.exists()}", flush=True)
    
    # Força refresh do cache do psutil
    try:
        psutil.Process().cpu_percent()
    except:
        pass
    
    for attempt in range(3):
        # Pequeno delay para evitar race conditions
        if attempt > 0:
            time.sleep(0.5)
        
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
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
                    pass
                os.write(fd, me.encode())
                os.close(fd)
                print(f"[instancia_unica] PID file criado com sucesso", flush=True)
                return True
            except FileExistsError:
                print(f"[instancia_unica] PID_FILE ja existe (tentativa {attempt+1})", flush=True)
                dono_vivo = False
                try:
                    dono = int(PID_FILE.read_text().strip())
                    p = psutil.Process(dono)
                    cmd = ' '.join(p.cmdline())
                    print(f"[instancia_unica] Dono do PID file: PID={dono}, cmd: {cmd[:100]}", flush=True)
                    if any(t.lower().endswith("widget_grafo.py") for t in p.cmdline()):
                        dono_vivo = True
                except Exception:
                    pass
                if dono_vivo:
                    print(f"[instancia_unica] Dono vivo com widget_grafo, retornando False", flush=True)
                    return False
                try:
                    PID_FILE.unlink()
                    print(f"[instancia_unica] PID file removido (dono morto)", flush=True)
                except FileNotFoundError:
                    pass
        print(f"[instancia_unica] Tentativas esgotadas, retornando False", flush=True)
        return False