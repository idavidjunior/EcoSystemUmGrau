"""Parallel task dispatcher with file conflict detection and worker pool."""
import json, os, sys, subprocess, threading, time, copy
from datetime import datetime
from collections import defaultdict

BASE = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada'),
                    'Desktop', 'Codigos', 'EcoSystemUmGrau')
LOCKS_DIR = os.path.join(BASE, 'conhecimento', 'locks')
MAX_WORKERS = 4

def _ensure_locks_dir():
    os.makedirs(LOCKS_DIR, exist_ok=True)

def acquire_lock(file_path, worker_id, timeout=30):
    """Acquire a file lock. Returns True if acquired, False if timeout."""
    _ensure_locks_dir()
    lock_name = file_path.replace(':', '_').replace('\\', '_').replace('/', '_') + '.lock'
    lock_path = os.path.join(LOCKS_DIR, lock_name)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(worker_id)
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False

def release_lock(file_path):
    lock_name = file_path.replace(':', '_').replace('\\', '_').replace('/', '_') + '.lock'
    lock_path = os.path.join(LOCKS_DIR, lock_name)
    try: os.remove(lock_path)
    except FileNotFoundError: pass

def release_all_locks(worker_id):
    _ensure_locks_dir()
    for f in os.listdir(LOCKS_DIR):
        path = os.path.join(LOCKS_DIR, f)
        try:
            with open(path) as fh:
                if fh.read().strip() == worker_id:
                    os.remove(path)
        except: pass

class Task:
    def __init__(self, name, command, cwd=None, read_files=None, write_files=None, depends_on=None):
        self.name = name
        self.command = command  # shell command string
        self.cwd = cwd or BASE
        self.read_files = set(read_files or [])
        self.write_files = set(write_files or [])
        self.depends_on = set(depends_on or [])
        self.result = None
        self.error = None
        self.duration = 0

def conflicts(a, b):
    """Two tasks conflict if they write to the same file, or one reads what the other writes."""
    return bool(a.write_files & b.write_files) or bool(a.write_files & b.read_files) or bool(b.write_files & a.read_files)

def build_levels(tasks):
    """Build execution levels from task DAG. tasks = {name: Task}"""
    task_map = {t.name: t for t in tasks}
    by_name = {t.name: t for t in tasks}
    levels = []
    remaining = set(by_name.keys())

    while remaining:
        # Find tasks whose dependencies are all done
        ready = {n for n in remaining if not (by_name[n].depends_on & remaining)}
        if not ready:
            raise ValueError(f"Circular dependency or missing deps among: {remaining}")

        # Within ready tasks, group by file conflicts for parallel execution
        level_groups = []
        ready_list = list(ready)
        assigned = set()
        for t in ready_list:
            if t in assigned: continue
            group = [t]
            assigned.add(t)
            for t2 in ready_list:
                if t2 in assigned: continue
                if not any(conflicts(by_name[t], by_name[t2]) for t in group):
                    group.append(t2)
                    assigned.add(t2)
            level_groups.append(group)

        for group in level_groups:
            levels.append(group)
        remaining -= ready

    return levels

def run_worker(task, worker_id):
    """Execute a task in a subprocess with file locks."""
    # Acquire write locks
    for f in task.write_files:
        if not acquire_lock(f, worker_id):
            task.error = f"Timeout acquiring lock for {f}"
            release_all_locks(worker_id)
            return False

    start = time.time()
    try:
        result = subprocess.run(
            task.command if isinstance(task.command, list) else task.command,
            shell=isinstance(task.command, str),
            capture_output=True, text=True, timeout=300,
            cwd=task.cwd
        )
        task.duration = time.time() - start
        if result.returncode == 0:
            task.result = result.stdout
            return True
        else:
            task.error = result.stderr or result.stdout
            return False
    except subprocess.TimeoutExpired:
        task.error = "Timeout (300s)"
        return False
    except Exception as e:
        task.error = str(e)
        return False
    finally:
        release_all_locks(worker_id)

def dispatch(tasks, max_workers=MAX_WORKERS):
    """Execute tasks in parallel respecting dependencies and file conflicts."""
    total = len(tasks)
    completed = []
    failed = []

    try:
        levels = build_levels(tasks)
    except ValueError as e:
        print(f'[DISPATCH] ERROR: {e}')
        return completed, failed

    print(f'[DISPATCH] {total} tasks, {len(levels)} execution levels')
    for i, level in enumerate(levels):
        group_names = [t.name for t in level]
        print(f'[DISPATCH] Level {i+1}: {", ".join(group_names)} ({"parallel" if len(level) > 1 else "serial"})')

        results = [None] * len(level)
        threads = []

        def worker_wrapper(idx, task):
            wid = f'worker-{idx}-{os.getpid()}'
            ok = run_worker(task, wid)
            results[idx] = (ok, task)

        for idx, task in enumerate(level):
            t = threading.Thread(target=worker_wrapper, args=(idx, task))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for ok, task in results:
            if ok:
                print(f'  [OK] {task.name} ({task.duration:.1f}s)')
                completed.append(task)
            else:
                print(f'  [FAIL] {task.name}: {task.error}')
                failed.append(task)

    return completed, failed

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Uso: python scripts/parallel_dispatcher.py <tasks.json>')
        print('tasks.json: [{"name":"...", "command":"...", "write_files":["..."], "depends_on":["..."]}]')
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        data = json.load(f)

    tasks = []
    for item in data:
        tasks.append(Task(
            name=item['name'],
            command=item['command'],
            cwd=item.get('cwd', BASE),
            read_files=item.get('read_files', []),
            write_files=item.get('write_files', []),
            depends_on=item.get('depends_on', [])
        ))

    completed, failed = dispatch(tasks)
    result = {'completed': len(completed), 'failed': len(failed), 'duration': sum(t.duration for t in completed)}
    print(json.dumps(result))
