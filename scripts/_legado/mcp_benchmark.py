#!/usr/bin/env python3
"""MCP Server Boot Latency Benchmark.
Measures time to spawn + initialize + tools/list for each of the 13 MCP servers.
"""
import json, os, sys, subprocess, time, statistics
from pathlib import Path

USERPROFILE = str(Path.home())
BASE = str(Path(__file__).resolve().parent.parent)
DEPLOYED = os.path.join(USERPROFILE, '.config', 'opencode', 'opencode.jsonc')

def expand_path(path_str):
    """Expand {env:USERPROFILE} and {{USERPROFILE}} template vars."""
    result = path_str.replace('{env:USERPROFILE}', USERPROFILE.replace('\\', '/'))
    result = result.replace('{{USERPROFILE}}', USERPROFILE.replace('\\', '/'))
    return result

def test_mcp_server(server_name, command, args, runs=3):
    """Test an MCP server multiple times and return timing stats."""
    print(f'\n{"="*60}')
    print(f'  Benchmarking: {server_name}')
    print(f'  Command: {command} {" ".join(args)}')
    print(f'  Runs: {runs}')
    print(f'{"="*60}')
    
    cmd_expanded = expand_path(command)
    args_expanded = [expand_path(a) for a in args]
    full_cmd = [cmd_expanded] + args_expanded
    
    init_msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
    tools_msg = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
    
    spawn_times = []
    init_times = []
    tools_times = []
    total_times = []
    tool_counts = []
    errors = []
    
    for run in range(runs):
        print(f'  Run {run+1}/{runs}...', end=' ', flush=True)
        
        try:
            # Measure spawn time
            spawn_start = time.perf_counter()
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=BASE
            )
            spawn_end = time.perf_counter()
            spawn_time = (spawn_end - spawn_start) * 1000  # ms
            
            # Send initialize + tools/list
            communicate_start = time.perf_counter()
            stdout, stderr = proc.communicate(input=init_msg + tools_msg, timeout=30)
            communicate_end = time.perf_counter()
            total_time = (communicate_end - communicate_start) * 1000
            
            # Parse responses
            init_found = False
            tools_found = False
            tools_count = 0
            
            for line in stdout.split('\n'):
                line = line.strip()
                if not line or not line.startswith('{'):
                    continue
                try:
                    obj = json.loads(line)
                    result = obj.get('result') or {}
                    if isinstance(result, dict):
                        if 'protocolVersion' in result:
                            init_found = True
                        if 'tools' in result:
                            tools_found = True
                            tools_count = len(result['tools'])
                except json.JSONDecodeError:
                    continue
            
            if init_found and tools_found:
                print(f'OK ({spawn_time:.1f}ms spawn, {total_time:.1f}ms total, {tools_count} tools)')
                spawn_times.append(spawn_time)
                total_times.append(total_time)
                tool_counts.append(tools_count)
                # Approximate init+tools time (total - spawn overhead)
                init_times.append(total_time)
            else:
                err = stderr[:200] if stderr else 'No valid response'
                print(f'FAIL - {err}')
                errors.append(err)
                
        except subprocess.TimeoutExpired:
            proc.kill()
            print('TIMEOUT (30s)')
            errors.append('Timeout')
        except Exception as e:
            print(f'ERROR - {str(e)[:100]}')
            errors.append(str(e)[:100])
    
    return {
        'server': server_name,
        'command': full_cmd,
        'runs': runs,
        'successful_runs': len(spawn_times),
        'spawn_ms': {
            'mean': statistics.mean(spawn_times) if spawn_times else None,
            'stdev': statistics.stdev(spawn_times) if len(spawn_times) > 1 else 0,
            'min': min(spawn_times) if spawn_times else None,
            'max': max(spawn_times) if spawn_times else None,
        },
        'total_ms': {
            'mean': statistics.mean(total_times) if total_times else None,
            'stdev': statistics.stdev(total_times) if len(total_times) > 1 else 0,
            'min': min(total_times) if total_times else None,
            'max': max(total_times) if total_times else None,
        },
        'tools_count': tool_counts[0] if tool_counts else 0,
        'errors': errors,
    }

def main():
    print('========================================')
    print('  MCP SERVER BOOT LATENCY BENCHMARK')
    print('========================================')
    
    with open(DEPLOYED, encoding='utf-8-sig') as f:
        cfg = json.load(f)
    
    servers = cfg.get('mcp', {})
    results = []
    
    # Test servers in order from config
    for name, config in servers.items():
        if not isinstance(config, dict):
            continue
        cmd = config.get('command', '')
        args = config.get('args', [])
        if isinstance(cmd, list):
            args = cmd[1:] + (list(args) if isinstance(args, list) else [])
            cmd = cmd[0] if cmd else ''
        if not cmd or 'npx' in str(cmd).lower():
            print(f'\nSkipping {name}: npx or no command')
            continue
        
        result = test_mcp_server(name, cmd, args, runs=3)
        results.append(result)
    
    # Summary table
    print('\n\n========================================')
    print('  BENCHMARK SUMMARY (mean of 3 runs)')
    print('========================================')
    print(f'{"Server":<30} {"Spawn(ms)":<12} {"Total(ms)":<12} {"Tools":<6} {"Status"}')
    print('-' * 80)
    
    for r in results:
        spawn = r['spawn_ms']['mean'] or 0
        total = r['total_ms']['mean'] or 0
        tools = r['tools_count']
        status = 'OK' if r['successful_runs'] == r['runs'] else f'{r["successful_runs"]}/{r["runs"]} FAIL'
        print(f'{r["server"]:<30} {spawn:<12.1f} {total:<12.1f} {tools:<6} {status}')
    
    # Sort by total time descending (slowest first)
    results_sorted = sorted([r for r in results if r['total_ms']['mean']], 
                           key=lambda x: x['total_ms']['mean'], reverse=True)
    
    print('\n\n========================================')
    print('  BOTTLENECK ANALYSIS (slowest first)')
    print('========================================')
    for i, r in enumerate(results_sorted, 1):
        total = r['total_ms']['mean']
        spawn = r['spawn_ms']['mean']
        print(f'  {i}. {r["server"]:<30} Total: {total:.1f}ms  Spawn: {spawn:.1f}ms  Tools: {r["tools_count"]}')
    
    # Detailed findings
    print('\n\n========================================')
    print('  DETAILED FINDINGS')
    print('========================================')
    
    if results_sorted:
        slowest = results_sorted[0]
        fastest = results_sorted[-1]
        print(f'\n  SLOWEST: {slowest["server"]} ({slowest["total_ms"]["mean"]:.1f}ms)')
        print(f'    - Spawn overhead: {slowest["spawn_ms"]["mean"]:.1f}ms')
        print(f'    - Tools: {slowest["tools_count"]}')
        print(f'    - Command: {" ".join(slowest["command"])}')
        
        print(f'\n  FASTEST: {fastest["server"]} ({fastest["total_ms"]["mean"]:.1f}ms)')
        print(f'    - Spawn overhead: {fastest["spawn_ms"]["mean"]:.1f}ms')
        print(f'    - Tools: {fastest["tools_count"]}')
        
        # Check for Python vs Node.js pattern
        python_servers = [r for r in results if r['command'][0].endswith('python.exe') or 'python' in r['command'][0]]
        node_servers = [r for r in results if r['command'][0].endswith('node.exe') or 'node' in r['command'][0]]
        
        if python_servers and node_servers:
            py_avg = statistics.mean([r['total_ms']['mean'] for r in python_servers if r['total_ms']['mean']])
            node_avg = statistics.mean([r['total_ms']['mean'] for r in node_servers if r['total_ms']['mean']])
            print(f'\n  PYTHON SERVERS avg: {py_avg:.1f}ms ({len(python_servers)} servers)')
            print(f'  NODE.JS SERVERS avg: {node_avg:.1f}ms ({len(node_servers)} servers)')
            print(f'  Ratio (Python/Node): {py_avg/node_avg:.2f}x')
    
    # Save results
    output_path = os.path.join(BASE, 'mcp_benchmark_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f'\n  Results saved to: {output_path}')
    
    return results

if __name__ == '__main__':
    main()