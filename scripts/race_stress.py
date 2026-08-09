#!/usr/bin/env python3
"""Race Stress Test - Detecção de race conditions via stress testing."""
import argparse
import sys
import threading
import time
import random
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List

@dataclass
class StressResult:
    iterations: int = 0
    errors: List[Dict] = field(default_factory=list)
    race_detected: bool = False
    durations: List[float] = field(default_factory=list)
    lock_contention: int = 0

def run_stress(target: Callable, args_list: List[tuple], kwargs_list: List[dict], 
               num_threads: int, iterations: int, shared_state: Dict = None) -> StressResult:
    """Executa stress test com múltiplas threads."""
    result = StressResult()
    errors_lock = threading.Lock()
    state_lock = threading.Lock() if shared_state else None
    
    def worker(worker_id: int):
        local_iterations = 0
        local_errors = []
        
        for i in range(iterations):
            start = time.perf_counter()
            try:
                # Pick random args/kwargs
                args = random.choice(args_list) if args_list else ()
                kwargs = random.choice(kwargs_list) if kwargs_list else {}
                
                if shared_state and state_lock:
                    with state_lock:
                        target(*args, **kwargs, _shared_state=shared_state)
                else:
                    target(*args, **kwargs)
                
                local_iterations += 1
            except Exception as e:
                with errors_lock:
                    local_errors.append({
                        'worker': worker_id,
                        'iteration': i,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'args': args if 'args' in locals() else (),
                        'kwargs': kwargs if 'kwargs' in locals() else {}
                    })
            finally:
                dur = time.perf_counter() - start
                result.durations.append(dur)
        
        with errors_lock:
            result.iterations += local_iterations
            result.errors.extend(local_errors)
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Analyze errors for race conditions
    error_signatures = defaultdict(int)
    for err in result.errors:
        # Simplify error to signature
        sig = f"{type(err['error']).__name__}: {str(err['error'])[:100]}"
        error_signatures[sig] += 1
    
    # Race condition indicators:
    # - Same error from multiple threads at similar times
    # - Inconsistent state errors
    # - AssertionErrors in concurrent context
    race_indicators = [
        'RaceCondition', 'ConcurrentModification', 'InconsistentState',
        'AssertionError', 'KeyError', 'IndexError', 'ValueError'
    ]
    
    for sig, count in error_signatures.items():
        if count > 1 and any(ind in sig for ind in race_indicators):
            result.race_detected = True
            break
    
    # Check for non-deterministic behavior (same input, different output)
    # This would require target to be pure - skip for now
    
    return result

def test_data_race(target_module: str, target_func: str, shared_var_name: str,
                   num_threads: int = 10, iterations: int = 1000) -> StressResult:
    """Testa especificamente data race em variável compartilhada."""
    import importlib
    mod = importlib.import_module(target_module)
    target = getattr(mod, target_func)
    shared_var = getattr(mod, shared_var_name)
    
    print(f'[DATA RACE TEST] {target_module}.{target_func} -> {shared_var_name}')
    print(f'  Threads: {num_threads}, Iterações/thread: {iterations}')
    
    # Reset shared state
    if isinstance(shared_var, dict):
        shared_var.clear()
    elif isinstance(shared_var, list):
        shared_var.clear()
    elif hasattr(shared_var, 'value'):
        shared_var.value = 0
    
    errors = []
    errors_lock = threading.Lock()
    results = []
    
    def worker(wid):
        for i in range(iterations):
            try:
                target()
                # Verify consistency
                if isinstance(shared_var, dict):
                    assert len(shared_var) == wid * (i+1)  # Example check
            except Exception as e:
                with errors_lock:
                    errors.append((wid, i, e))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    return StressResult(
        iterations=num_threads * iterations,
        errors=[{'worker': w, 'iteration': i, 'error': str(e)} for w, i, e in errors],
        race_detected=len(errors) > 0
    )

def main():
    parser = argparse.ArgumentParser(description='Race Condition Stress Tester')
    parser.add_argument('--target-module', required=True, help='Módulo alvo (ex: my_module)')
    parser.add_argument('--target-func', required=True, help='Função alvo')
    parser.add_argument('--shared-var', help='Variável compartilhada para testar data race')
    parser.add_argument('--threads', type=int, default=10, help='Número de threads')
    parser.add_argument('--iterations', type=int, default=1000, help='Iterações por thread')
    parser.add_argument('--args', nargs='*', default=[], help='Args posicionais (JSON)')
    parser.add_argument('--kwargs', nargs='*', default=[], help='Kwargs (JSON)')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout total (segundos)')
    args = parser.parse_args()
    
    import importlib
    import json
    
    mod = importlib.import_module(args.target_module)
    target = getattr(mod, args.target_func)
    
    # Parse args/kwargs
    args_list = []
    for a in args.args:
        try:
            args_list.append(tuple(json.loads(a)))
        except:
            args_list.append((a,))
    if not args_list:
        args_list = [()]
    
    kwargs_list = []
    for k in args.kwargs:
        try:
            kwargs_list.append(json.loads(k))
        except:
            kwargs_list.append({})
    if not kwargs_list:
        kwargs_list = [{}]
    
    print(f'=== RACE STRESS TEST ===')
    print(f'Target: {args.target_module}.{args.target_func}')
    print(f'Threads: {args.threads}, Iterações: {args.iterations}')
    print(f'Args variations: {len(args_list)}, Kwargs variations: {len(kwargs_list)}')
    print()
    
    if args.shared_var:
        result = test_data_race(args.target_module, args.target_func, args.shared_var,
                                args.threads, args.iterations)
    else:
        result = run_stress(target, args_list, kwargs_list, args.threads, args.iterations)
    
    print(f'\n=== RESULTADOS ===')
    print(f'Iterações totais: {result.iterations}')
    print(f'Erros: {len(result.errors)}')
    print(f'Race condition detectada: {"SIM" if result.race_detected else "NÃO"}')
    
    if result.durations:
        avg_dur = sum(result.durations) / len(result.durations)
        max_dur = max(result.durations)
        print(f'Duração média: {avg_dur*1000:.2f}ms, Máx: {max_dur*1000:.2f}ms')
    
    if result.errors:
        print('\n--- ERROS ---')
        by_type = defaultdict(int)
        for err in result.errors[:20]:
            etype = type(err['error']).__name__ if isinstance(err['error'], BaseException) else 'Error'
            by_type[etype] += 1
            print(f"  Worker {err['worker']}, Iter {err['iteration']}: {err['error'][:150]}")
        print(f'\nResumo por tipo: {dict(by_type)}')
    
    # Exit code: 1 if race detected, 0 otherwise
    sys.exit(1 if result.race_detected else 0)

if __name__ == '__main__':
    main()