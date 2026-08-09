#!/usr/bin/env python3
"""Debug Health Check - Análise completa de saúde do projeto."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

BASE = Path(__file__).resolve().parent.parent

def run_cmd(cmd: List[str], cwd: Path = BASE) -> Tuple[int, str, str]:
    """Executa comando e retorna (code, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except Exception as e:
        return -1, '', str(e)

def check_python_project(project_path: Path) -> Dict:
    """Verifica projeto Python."""
    results = {
        'type': 'python',
        'lint': {'status': 'skipped', 'details': ''},
        'typecheck': {'status': 'skipped', 'details': ''},
        'tests': {'status': 'skipped', 'details': ''},
        'security': {'status': 'skipped', 'details': ''},
        'duplicates': {'status': 'skipped', 'details': ''},
        'dead_code': {'status': 'skipped', 'details': ''},
        'imports': {'status': 'skipped', 'details': ''},
    }
    
    # Ruff lint
    code, out, err = run_cmd(['ruff', 'check', str(project_path)])
    results['lint'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
    
    # MyPy typecheck
    code, out, err = run_cmd(['mypy', str(project_path), '--ignore-missing-imports'])
    results['typecheck'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
    
    # Pytest (se existir)
    if (project_path / 'pytest.ini').exists() or (project_path / 'pyproject.toml').exists():
        code, out, err = run_cmd(['pytest', str(project_path), '-x', '-q', '--tb=short'])
        results['tests'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
    
    # Bandit security
    code, out, err = run_cmd(['bandit', '-r', str(project_path), '-f', 'json'])
    try:
        bandit_data = json.loads(out) if out else {'results': []}
        high_sev = [r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'HIGH']
        results['security'] = {'status': 'fail' if high_sev else 'pass', 'details': f'{len(high_sev)} HIGH'}
    except:
        results['security'] = {'status': 'error', 'details': 'bandit parse failed'}
    
    # Duplicates (pylint)
    code, out, err = run_cmd(['pylint', '--disable=all', '--enable=duplicate-code', str(project_path)])
    results['duplicates'] = {'status': 'pass' if code == 0 else 'warn', 'details': out[:500]}
    
    # Dead code (vulture)
    code, out, err = run_cmd(['vulture', str(project_path), '--min-confidence', '80'])
    results['dead_code'] = {'status': 'pass' if code == 0 else 'warn', 'details': out[:500]}
    
    # Unused imports (pyflakes)
    code, out, err = run_cmd(['pyflakes', str(project_path)])
    results['imports'] = {'status': 'pass' if code == 0 else 'warn', 'details': out[:500]}
    
    return results

def check_js_ts_project(project_path: Path) -> Dict:
    """Verifica projeto JavaScript/TypeScript."""
    results = {
        'type': 'javascript/typescript',
        'lint': {'status': 'skipped', 'details': ''},
        'typecheck': {'status': 'skipped', 'details': ''},
        'tests': {'status': 'skipped', 'details': ''},
        'security': {'status': 'skipped', 'details': ''},
        'duplicates': {'status': 'skipped', 'details': ''},
        'circular_deps': {'status': 'skipped', 'details': ''},
    }
    
    # ESLint
    code, out, err = run_cmd(['npx', 'eslint', str(project_path), '--ext', '.js,.ts,.tsx,.jsx'])
    results['lint'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
    
    # TypeScript check
    tsconfig = project_path / 'tsconfig.json'
    if tsconfig.exists():
        code, out, err = run_cmd(['npx', 'tsc', '--noEmit', '-p', str(tsconfig)])
        results['typecheck'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
    
    # Tests (jest/vitest)
    pkg_json = project_path / 'package.json'
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            scripts = pkg.get('scripts', {})
            if 'test' in scripts:
                code, out, err = run_cmd(['npm', 'test', '--', '--watchAll=false'], cwd=project_path)
                results['tests'] = {'status': 'pass' if code == 0 else 'fail', 'details': out or err}
        except:
            pass
    
    # npm audit
    code, out, err = run_cmd(['npm', 'audit', '--json'], cwd=project_path)
    try:
        audit = json.loads(out) if out else {}
        high = audit.get('metadata', {}).get('vulnerabilities', {}).get('high', 0)
        critical = audit.get('metadata', {}).get('vulnerabilities', {}).get('critical', 0)
        results['security'] = {'status': 'fail' if (high + critical) > 0 else 'pass', 
                               'details': f'{high} HIGH, {critical} CRITICAL'}
    except:
        results['security'] = {'status': 'error', 'details': 'audit parse failed'}
    
    # Duplicates (jscpd)
    code, out, err = run_cmd(['npx', 'jscpd', str(project_path), '--min-lines', '6', '--reporter', 'json'])
    try:
        jscpd = json.loads(out) if out else {}
        dupes = jscpd.get('statistics', {}).get('total', 0)
        results['duplicates'] = {'status': 'warn' if dupes > 0 else 'pass', 'details': f'{dupes} clones'}
    except:
        results['duplicates'] = {'status': 'skipped', 'details': 'jscpd not available'}
    
    # Circular deps (madge)
    code, out, err = run_cmd(['npx', 'madge', '--circular', '--extensions', 'js,ts', str(project_path)])
    has_circular = 'circular' in (out + err).lower()
    results['circular_deps'] = {'status': 'fail' if has_circular else 'pass', 'details': out[:500]}
    
    return results

def check_generic(project_path: Path) -> Dict:
    """Verificações genéricas (qualquer projeto)."""
    results = {
        'git_status': {'status': 'skipped', 'details': ''},
        'secrets': {'status': 'skipped', 'details': ''},
        'large_files': {'status': 'skipped', 'details': ''},
        'todo_fixme': {'status': 'skipped', 'details': ''},
    }
    
    # Git status
    code, out, err = run_cmd(['git', 'status', '--porcelain'])
    modified = len(out.strip().split('\n')) if out.strip() else 0
    results['git_status'] = {'status': 'warn' if modified > 0 else 'pass', 
                             'details': f'{modified} arquivos modificados'}
    
    # Secrets (gitleaks)
    code, out, err = run_cmd(['gitleaks', 'detect', '--source', str(project_path), '--no-banner', '--report-format', 'json'])
    try:
        leaks = json.loads(out) if out else []
        results['secrets'] = {'status': 'fail' if leaks else 'pass', 
                              'details': f'{len(leaks)} segredos detectados'}
    except:
        results['secrets'] = {'status': 'skipped', 'details': 'gitleaks not available'}
    
    # Large files (> 1MB)
    large = []
    for f in project_path.rglob('*'):
        if f.is_file() and f.stat().st_size > 1_000_000:
            large.append(f'{f.relative_to(project_path)} ({f.stat().st_size/1024/1024:.1f}MB)')
    results['large_files'] = {'status': 'warn' if large else 'pass', 
                              'details': '; '.join(large[:5])}
    
    # TODO/FIXME count
    code, out, err = run_cmd(['grep', '-r', '-i', '-E', 'TODO|FIXME|HACK|XXX', str(project_path), '--include=*.py', '--include=*.js', '--include=*.ts', '--include=*.md'])
    count = len(out.strip().split('\n')) if out.strip() else 0
    results['todo_fixme'] = {'status': 'info', 'details': f'{count} marcadores'}
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Debug Health Check completo')
    parser.add_argument('--project', default='.', help='Caminho do projeto')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    args = parser.parse_args()
    
    project_path = Path(args.project).resolve()
    
    print(f'=== DEBUG HEALTH CHECK: {project_path} ===\n')
    
    all_results = {}
    
    # Detectar tipo de projeto
    if (project_path / 'pyproject.toml').exists() or (project_path / 'requirements.txt').exists() or list(project_path.rglob('*.py')):
        print('[Python] Executando verificações...')
        all_results['python'] = check_python_project(project_path)
    
    if (project_path / 'package.json').exists() or list(project_path.rglob('*.js')) or list(project_path.rglob('*.ts')):
        print('[JS/TS] Executando verificações...')
        all_results['javascript'] = check_js_ts_project(project_path)
    
    print('[Generic] Executando verificações genéricas...')
    all_results['generic'] = check_generic(project_path)
    
    # Resumo
    print('\n=== RESUMO ===')
    total_checks = 0
    failed = 0
    warnings = 0
    
    for category, checks in all_results.items():
        print(f'\n--- {category.upper()} ---')
        for check_name, result in checks.items():
            if isinstance(result, dict) and 'status' in result:
                total_checks += 1
                status = result['status']
                details = result.get('details', '')
                icon = {'pass': '[OK]', 'fail': '[FAIL]', 'warn': '[WARN]', 'error': '[ERR]', 'skipped': '[SKIP]', 'info': '[INFO]'}.get(status, '[?]')
                print(f'  {icon} {check_name}: {status} {details}')
                if status == 'fail':
                    failed += 1
                elif status in ('warn', 'error'):
                    warnings += 1
    
    print(f'\n=== TOTAL: {total_checks} checks, {failed} falhas, {warnings} avisos ===')
    
    if args.json:
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
    
    sys.exit(1 if failed > 0 else 0)

if __name__ == '__main__':
    main()