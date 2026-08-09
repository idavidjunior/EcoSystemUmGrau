#!/usr/bin/env python3
"""Find Duplicates - Detecção de código duplicado multiplataforma."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import hashlib

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, '', str(e)

def find_duplicates_python(path: Path, min_lines: int, min_tokens: int, exclude: list) -> list:
    """Usa pylint para duplicação Python."""
    exclude_args = []
    for e in exclude:
        exclude_args.extend(['--ignore', e])
    
    cmd = ['pylint', '--disable=all', '--enable=duplicate-code', 
           f'--min-similarity-lines={min_lines}'] + exclude_args + [str(path)]
    code, out, err = run_cmd(cmd)
    
    duplicates = []
    current_block = None
    for line in out.split('\n'):
        if 'Similar lines in' in line:
            if current_block:
                duplicates.append(current_block)
            parts = line.split('Similar lines in ')[1].split(' (')
            files_part = parts[0]
            lines_part = parts[1].rstrip(')')
            current_block = {'files': files_part.split(', '), 'lines': lines_part, 'code': ''}
        elif current_block and line.strip().startswith('|'):
            current_block['code'] += line + '\n'
    if current_block:
        duplicates.append(current_block)
    return duplicates

def find_duplicates_jscpd(path: Path, min_lines: int, exclude: list) -> list:
    """Usa jscpd para duplicação JS/TS e outras linguagens."""
    exclude_pattern = ','.join([f'!**/{e}**' for e in exclude])
    cmd = ['npx', 'jscpd', str(path), '--min-lines', str(min_lines), 
           '--reporter', 'json', '--pattern', f'**/*{exclude_pattern}']
    code, out, err = run_cmd(cmd)
    
    try:
        data = json.loads(out) if out else {}
        clones = data.get('clones', [])
        return clones
    except:
        return []

def find_duplicates_generic(path: Path, min_lines: int, exclude: list) -> list:
    """Detecção genérica baseada em hash de linhas (fallback)."""
    extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h', '.cs', '.php', '.rb'}
    exclude_set = set(exclude)
    
    file_hashes = defaultdict(list)
    
    for file_path in path.rglob('*'):
        if not file_path.is_file():
            continue
        if file_path.suffix not in extensions:
            continue
        if any(e in str(file_path) for e in exclude_set):
            continue
        if file_path.stat().st_size > 500_000:
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for i in range(len(lines) - min_lines + 1):
                window = '\n'.join(lines[i:i+min_lines]).strip()
                if len(window) < 50:
                    continue
                h = hashlib.md5(window.encode()).hexdigest()[:16]
                file_hashes[h].append({
                    'file': str(file_path.relative_to(path)),
                    'start_line': i + 1,
                    'end_line': i + min_lines,
                    'preview': window[:200]
                })
        except:
            pass
    
    duplicates = []
    for h, occurrences in file_hashes.items():
        if len(occurrences) > 1:
            by_file = defaultdict(list)
            for occ in occurrences:
                by_file[occ['file']].append(occ)
            
            duplicates.append({
                'hash': h,
                'files': list(by_file.keys()),
                'occurrences': occurrences,
                'count': len(occurrences)
            })
    
    return duplicates

def main():
    parser = argparse.ArgumentParser(description='Detecta código duplicado')
    parser.add_argument('path', nargs='?', default='.', help='Diretório do projeto')
    parser.add_argument('--min-lines', type=int, default=6, help='Mínimo de linhas para considerar duplicação')
    parser.add_argument('--min-tokens', type=int, default=70, help='Mínimo de tokens (pylint)')
    parser.add_argument('--exclude', nargs='*', default=['test', 'tests', '__pycache__', 'node_modules', '.git', 'venv', 'env', 'dist', 'build'], help='Padrões para excluir')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--tool', choices=['auto', 'pylint', 'jscpd', 'generic'], default='auto')
    args = parser.parse_args()
    
    path = Path(args.path).resolve()
    
    all_duplicates = []
    
    py_files = list(path.rglob('*.py'))
    if py_files and args.tool in ('auto', 'pylint'):
        print('[pylint] Verificando duplicação Python...')
        dupes = find_duplicates_python(path, args.min_lines, args.min_tokens, args.exclude)
        all_duplicates.extend([{'tool': 'pylint', **d} for d in dupes])
    
    js_ts_files = list(path.rglob('*.js')) + list(path.rglob('*.ts')) + list(path.rglob('*.jsx')) + list(path.rglob('*.tsx'))
    if js_ts_files and args.tool in ('auto', 'jscpd'):
        print('[jscpd] Verificando duplicação JS/TS...')
        dupes = find_duplicates_jscpd(path, args.min_lines, args.exclude)
        all_duplicates.extend([{'tool': 'jscpd', **d} for d in dupes])
    
    if args.tool == 'generic' or (args.tool == 'auto' and not py_files and not js_ts_files):
        print('[generic] Verificando duplicação genérica...')
        dupes = find_duplicates_generic(path, args.min_lines, args.exclude)
        all_duplicates.extend([{'tool': 'generic', **d} for d in dupes])
    
    if args.format == 'json':
        print(json.dumps(all_duplicates, indent=2, ensure_ascii=False))
        return
    
    if not all_duplicates:
        print('Nenhuma duplicação encontrada.')
        return
    
    print(f'\n=== {len(all_duplicates)} BLOCOS DUPLICADOS ENCONTRADOS ===\n')
    
    for i, dup in enumerate(all_duplicates, 1):
        tool = dup.get('tool', 'unknown')
        print(f'--- Bloco #{i} ({tool}) ---')
        
        if tool == 'pylint':
            print(f'Arquivos: {", ".join(dup["files"])}')
            print(f'Linhas: {dup["lines"]}')
            print(f'Código:\n{dup["code"][:500]}')
        elif tool == 'jscpd':
            print(f'Arquivos: {len(dup.get("files", []))} arquivos')
            for f in dup.get('files', [])[:5]:
                print(f'  - {f}')
        else:
            print(f'Hash: {dup["hash"]}')
            print(f'Ocorrências: {dup["count"]}')
            print(f'Arquivos: {", ".join(dup["files"][:5])}')
            if dup['occurrences']:
                print(f'Preview: {dup["occurrences"][0]["preview"]}')
        print()

if __name__ == '__main__':
    main()