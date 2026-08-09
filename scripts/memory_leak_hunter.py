#!/usr/bin/env python3
"""Memory Leak Hunter - Detecção de memory leaks em Python."""
import argparse
import gc
import sys
import time
import tracemalloc
import psutil
import os
from collections import defaultdict

def get_memory_mb():
    """Retorna memória atual do processo em MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def snapshot_diff(snap1, snap2, top_n=20):
    """Compara dois snapshots do tracemalloc."""
    stats = snap2.compare_to(snap1, 'lineno')
    return stats[:top_n]

def format_stats(stats):
    """Formata estatísticas de memória."""
    lines = []
    for stat in stats:
        lines.append(f"  {stat.size_diff/1024:+.1f} KB  {stat.count_diff:+d}  {stat}")
    return '\n'.join(lines)

def track_allocations(target_func, duration=60, interval=5):
    """Rastreia alocações durante execução de uma função."""
    tracemalloc.start(25)  # 25 frames
    
    snapshot_before = tracemalloc.take_snapshot()
    mem_before = get_memory_mb()
    
    print(f'[INIT] Memória inicial: {mem_before:.1f} MB')
    print(f'[INIT] Rastreando por {duration}s (intervalo {interval}s)...\n')
    
    start_time = time.time()
    last_snapshot = snapshot_before
    last_mem = mem_before
    
    # Run target in background thread
    import threading
    result = {'done': False, 'error': None, 'return_value': None}
    
    def runner():
        try:
            result['return_value'] = target_func()
        except Exception as e:
            result['error'] = e
        finally:
            result['done'] = True
    
    thread = threading.Thread(target=runner)
    thread.start()
    
    while not result['done'] and (time.time() - start_time) < duration:
        time.sleep(interval)
        current_mem = get_memory_mb()
        current_snapshot = tracemalloc.take_snapshot()
        
        mem_diff = current_mem - last_mem
        print(f'[{time.time()-start_time:.0f}s] Mem: {current_mem:.1f} MB ({mem_diff:+.1f} MB)')
        
        if mem_diff > 5:  # Crescimento > 5MB
            stats = snapshot_diff(last_snapshot, current_snapshot, top_n=10)
            print(f'  [ALERT] Crescimento detectado! Top alocações:')
            print(format_stats(stats))
        
        last_snapshot = current_snapshot
        last_mem = current_mem
    
    thread.join(timeout=5)
    
    # Final snapshot
    final_snapshot = tracemalloc.take_snapshot()
    final_mem = get_memory_mb()
    
    print(f'\n[FINAL] Memória final: {final_mem:.1f} MB (delta: {final_mem - mem_before:+.1f} MB)')
    
    # Top allocations overall
    stats = snapshot_diff(snapshot_before, final_snapshot, top_n=30)
    print('\n[TOP ALLOCAÇÕES GERAL]')
    print(format_stats(stats))
    
    # Group by file
    by_file = defaultdict(lambda: {'size': 0, 'count': 0})
    for stat in final_snapshot.statistics('filename'):
        by_file[stat.traceback._frames[0].filename if stat.traceback._frames else 'unknown'] = {
            'size': stat.size,
            'count': stat.count
        }
    
    print('\n[POR ARQUIVO]')
    for file, data in sorted(by_file.items(), key=lambda x: -x[1]['size'])[:15]:
        print(f"  {data['size']/1024/1024:.2f} MB  {data['count']} blocks  {file}")
    
    tracemalloc.stop()
    
    if result['error']:
        raise result['error']
    return result['return_value']

def analyze_object_growth(target_func, duration=60, interval=5):
    """Analisa crescimento de objetos via gc.get_objects()."""
    import threading
    
    print('[OBJETOS] Iniciando análise de objetos...')
    
    baseline = defaultdict(int)
    for obj in gc.get_objects():
        baseline[type(obj).__name__] += 1
    
    result = {'done': False}
    def runner():
        try:
            target_func()
        finally:
            result['done'] = True
    
    thread = threading.Thread(target=runner)
    thread.start()
    
    start = time.time()
    while not result['done'] and (time.time() - start) < duration:
        time.sleep(interval)
        current = defaultdict(int)
        for obj in gc.get_objects():
            current[type(obj).__name__] += 1
        
        growing = []
        for typ, count in current.items():
            diff = count - baseline.get(typ, 0)
            if diff > 100:  # Mais de 100 objetos novos
                growing.append((typ, count, diff))
        
        if growing:
            print(f'  [{time.time()-start:.0f}s] Objetos crescendo:')
            for typ, count, diff in sorted(growing, key=lambda x: -x[2])[:10]:
                print(f'    {typ}: {count} (+{diff})')
    
    thread.join(timeout=5)

def main():
    parser = argparse.ArgumentParser(description='Memory Leak Hunter para Python')
    parser.add_argument('--attach-pid', type=int, help='Anexar a processo existente (PID)')
    parser.add_argument('--duration', type=int, default=60, help='Duração do monitoramento (segundos)')
    parser.add_argument('--interval', type=int, default=5, help='Intervalo de verificação (segundos)')
    parser.add_argument('--module', help='Módulo para executar e monitorar (ex: my_module.main)')
    parser.add_argument('--function', help='Função para chamar (usar com --module)')
    parser.add_argument('--analyze-objects', action='store_true', help='Analisar crescimento de objetos (gc)')
    args = parser.parse_args()
    
    if args.attach_pid:
        print(f'[ATTACH] Monitorando PID {args.attach_pid}...')
        # Would need to use ptrace or similar - complex
        print('Attach a PID não implementado ainda. Use --module.')
        return
    
    if args.module:
        # Import and run module
        import importlib
        mod = importlib.import_module(args.module)
        if args.function:
            target = getattr(mod, args.function)
        else:
            target = getattr(mod, 'main', None)
            if not target:
                print('Erro: módulo não tem função "main" nem --function especificado')
                return
        
        print(f'[TARGET] {args.module}.{target.__name__}')
        
        if args.analyze_objects:
            analyze_object_growth(target, args.duration, args.interval)
        else:
            track_allocations(target, args.duration, args.interval)
    else:
        print('Erro: especifique --module ou --attach-pid')
        parser.print_help()

if __name__ == '__main__':
    main()