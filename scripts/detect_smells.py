#!/usr/bin/env python3
"""Detect Smells - Detecção de code smells."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, '', str(e)

def check_python_smells(path: Path, threshold: str) -> dict:
    """Verifica code smells em Python via ruff + pylint + radon."""
    results = {}
    
    # Ruff - todas as regras
    code, out, err = run_cmd(['ruff', 'check', str(path), '--output-format=json'])
    try:
        ruff_issues = json.loads(out) if out else []
        by_code = {}
        for issue in ruff_issues:
            code = issue.get('code', 'UNKNOWN')
            by_code[code] = by_code.get(code, 0) + 1
        results['ruff'] = {'total': len(ruff_issues), 'by_code': by_code}
    except:
        results['ruff'] = {'error': 'parse failed'}
    
    # Pylint - métricas de complexidade
    code, out, err = run_cmd(['pylint', str(path), '--output-format=json', 
                              '--disable=all', '--enable=R,C,W'])
    try:
        pylint_issues = json.loads(out) if out else []
        by_type = {}
        for issue in pylint_issues:
            t = issue.get('type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
        results['pylint'] = {'total': len(pylint_issues), 'by_type': by_type}
    except:
        results['pylint'] = {'error': 'parse failed'}
    
    # Radon - complexidade ciclomática
    code, out, err = run_cmd(['radon', 'cc', str(path), '-j'])
    try:
        radon_data = json.loads(out) if out else {}
        high_cc = []
        for file, funcs in radon_data.items():
            for f in funcs:
                if f.get('complexity', 0) > 10:
                    high_cc.append(f'{file}:{f["name"]} (CC={f["complexity"]})')
        results['cyclomatic_complexity'] = {'high_count': len(high_cc), 'functions': high_cc[:20]}
    except:
        results['cyclomatic_complexity'] = {'error': 'radon not available or parse failed'}
    
    # Radon - métricas de manutenibilidade
    code, out, err = run_cmd(['radon', 'mi', str(path), '-j'])
    try:
        mi_data = json.loads(out) if out else {}
        low_mi = []
        for file, metrics in mi_data.items():
            mi = metrics.get('mi', 100)
            if mi < 50:
                low_mi.append(f'{file} (MI={mi:.1f})')
        results['maintainability_index'] = {'low_count': len(low_mi), 'files': low_mi[:20]}
    except:
        results['maintainability_index'] = {'error': 'radon mi not available'}
    
    # Vulture - código morto
    code, out, err = run_cmd(['vulture', str(path), '--min-confidence', '80'])
    dead_code = [l for l in out.split('\n') if l.strip() and not l.startswith(' ')]
    results['dead_code'] = {'count': len(dead_code), 'items': dead_code[:20]}
    
    return results

def check_js_ts_smells(path: Path, threshold: str) -> dict:
    """Verifica code smells em JS/TS via ESLint + sonarjs."""
    results = {}
    
    # ESLint com todas as regras
    code, out, err = run_cmd(['npx', 'eslint', str(path), '--ext', '.js,.ts,.tsx,.jsx', '-f', 'json'])
    try:
        eslint_data = json.loads(out) if out else []
        total_issues = sum(len(f.get('messages', [])) for f in eslint_data)
        by_rule = {}
        for f in eslint_data:
            for msg in f.get('messages', []):
                rule = msg.get('ruleId', 'unknown')
                by_rule[rule] = by_rule.get(rule, 0) + 1
        results['eslint'] = {'total': total_issues, 'by_rule': dict(sorted(by_rule.items(), key=lambda x: -x[1])[:30])}
    except:
        results['eslint'] = {'error': 'parse failed'}
    
    # Complexidade (eslint-plugin-complexity ou manual)
    # Usar jscpd para duplicação já feito no find_duplicates
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Detecta code smells')
    parser.add_argument('path', nargs='?', default='.', help='Diretório do projeto')
    parser.add_argument('--threshold', choices=['low', 'medium', 'high'], default='medium', help='Nível de alerta')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    args = parser.parse_args()
    
    path = Path(args.path).resolve()
    
    all_results = {}
    
    py_files = list(path.rglob('*.py'))
    if py_files:
        print('[Python] Verificando code smells...')
        all_results['python'] = check_python_smells(path, args.threshold)
    
    js_ts_files = list(path.rglob('*.js')) + list(path.rglob('*.ts')) + list(path.rglob('*.jsx')) + list(path.rglob('*.tsx'))
    if js_ts_files:
        print('[JS/TS] Verificando code smells...')
        all_results['javascript'] = check_js_ts_smells(path, args.threshold)
    
    if args.format == 'json':
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
        return
    
    print('\n=== CODE SMELLS REPORT ===\n')
    
    for lang, results in all_results.items():
        print(f'--- {lang.upper()} ---')
        for tool, data in results.items():
            if 'error' in data:
                print(f'  {tool}: ERRO - {data["error"]}')
                continue
            if 'total' in data:
                print(f'  {tool}: {data["total"]} issues')
                if 'by_code' in data:
                    for code, count in sorted(data['by_code'].items(), key=lambda x: -x[1])[:10]:
                        print(f'    {code}: {count}')
                if 'by_type' in data:
                    for t, count in data['by_type'].items():
                        print(f'    {t}: {count}')
                if 'by_rule' in data:
                    for rule, count in list(data['by_rule'].items())[:10]:
                        print(f'    {rule}: {count}')
            if 'high_count' in data:
                print(f'  {tool}: {data["high_count"]} itens problemáticos')
                for item in data.get('functions', data.get('files', []))[:10]:
                    print(f'    - {item}')
            if 'count' in data and 'items' in data:
                print(f'  {tool}: {data["count"]} itens')
                for item in data['items'][:10]:
                    print(f'    - {item}')
        print()

if __name__ == '__main__':
    main()