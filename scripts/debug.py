#!/usr/bin/env python3
"""Debug Unificado - Comando principal de debug do ecossistema."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / 'scripts'

def run_script(script_name, args):
    """Executa script de debug."""
    cmd = [sys.executable, str(SCRIPTS / script_name)] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=BASE)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f'TIMEOUT ({script_name})'
    except Exception as e:
        return -1, '', str(e)

def main():
    parser = argparse.ArgumentParser(description='Debug Unificado - EcoSystemUmGrau')
    parser.add_argument('target', nargs='?', default='.', help='Arquivo/diretório alvo')
    parser.add_argument('--categoria', choices=[
        'crash', 'logic', 'perf', 'ui', 'config', 'dup', 'smell', 'link', 'race', 'memory', 'health', 'all'
    ], default='health', help='Categoria de debug')
    parser.add_argument('--min-lines', type=int, default=6, help='Mínimo linhas para duplicação')
    parser.add_argument('--threshold', choices=['low', 'medium', 'high'], default='medium', help='Threshold para smells')
    parser.add_argument('--base-url', help='Base URL para verificação de links')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--fix', action='store_true', help='Tentar correção automática (quando possível)')
    parser.add_argument('--verbose', '-v', action='store_true')
    
    args = parser.parse_args()
    
    target_path = Path(args.target).resolve()
    
    print(f'=== DEBUG UNIFICADO: {target_path} ===')
    print(f'Categoria: {args.categoria}\n')
    
    results = {}
    
    # Health check (sempre roda)
    if args.categoria in ('health', 'all'):
        print('[1/10] Health Check...')
        code, out, err = run_script('debug_health_check.py', [str(target_path), '--json'] if args.format == 'json' else [str(target_path)])
        results['health'] = {'code': code, 'output': out, 'error': err}
        if not args.format == 'json':
            print(out[:2000])
    
    # Duplicação
    if args.categoria in ('dup', 'all'):
        print('\n[2/10] Detecção de Duplicação...')
        code, out, err = run_script('find_duplicates.py', 
            [str(target_path), '--min-lines', str(args.min_lines), '--format', args.format])
        results['duplicates'] = {'code': code, 'output': out, 'error': err}
        if not args.format == 'json':
            print(out[:2000])
    
    # Code smells
    if args.categoria in ('smell', 'all'):
        print('\n[3/10] Code Smells...')
        code, out, err = run_script('detect_smells.py', 
            [str(target_path), '--threshold', args.threshold, '--format', args.format])
        results['smells'] = {'code': code, 'output': out, 'error': err}
        if not args.format == 'json':
            print(out[:2000])
    
    # Links quebrados
    if args.categoria in ('link', 'all'):
        print('\n[4/10] Links Quebrados...')
        link_args = [str(target_path), '--format', args.format]
        if args.base_url:
            link_args.extend(['--base-url', args.base_url])
        code, out, err = run_script('check_links.py', link_args)
        results['links'] = {'code': code, 'output': out, 'error': err}
        if not args.format == 'json':
            print(out[:2000])
    
    # Race conditions
    if args.categoria in ('race', 'all'):
        print('\n[5/10] Race Conditions...')
        print('  (Requer --target-module e --target-func para testar)')
        results['race'] = {'skipped': 'Needs target module/function'}
    
    # Memory leaks
    if args.categoria in ('memory', 'all'):
        print('\n[6/10] Memory Leaks...')
        print('  (Requer --module para monitorar)')
        results['memory'] = {'skipped': 'Needs module to monitor'}
    
    # Crash/Logic - would need specific target
    if args.categoria in ('crash', 'logic', 'all'):
        print('\n[7/10] Crash/Logic Analysis...')
        print('  (Requer stack trace ou caso de reprodução)')
        results['crash_logic'] = {'skipped': 'Needs reproduction case'}
    
    # Performance
    if args.categoria in ('perf', 'all'):
        print('\n[8/10] Performance...')
        print('  (Requer benchmark ou profiler)')
        results['perf'] = {'skipped': 'Needs benchmark target'}
    
    # UI
    if args.categoria in ('ui', 'all'):
        print('\n[9/10] UI/Dysfunctional...')
        print('  (Requer frontend project)')
        results['ui'] = {'skipped': 'Needs frontend project'}
    
    # Config
    if args.categoria in ('config', 'all'):
        print('\n[10/10] Config/Environment...')
        code, out, err = run_script('preflight_check.py', [])
        results['config'] = {'code': code, 'output': out, 'error': err}
        if not args.format == 'json':
            print(out[:2000])
    
    # Summary
    if args.format == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print('\n=== RESUMO ===')
        for cat, res in results.items():
            if 'skipped' in res:
                print(f'  {cat}: SKIPPED - {res["skipped"]}')
            elif 'code' in res:
                status = 'OK' if res['code'] == 0 else 'FAIL'
                print(f'  {cat}: {status} (exit={res["code"]})')
    
    # Overall exit code
    failed = any(r.get('code', 0) != 0 for r in results.values() if 'code' in r)
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()