#!/usr/bin/env python3
"""Analyze widget_grafo.py for issues."""
import re

with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

issues = []

# 1. Bare except
for i, line in enumerate(content.split('\n'), 1):
    if 'except:' in line and not line.strip().startswith('#'):
        issues.append(f'Line {i}: Bare except: {line.strip()}')

# 2. TODO/FIXME
for i, line in enumerate(content.split('\n'), 1):
    if any(kw in line.upper() for kw in ['TODO', 'FIXME', 'HACK', 'XXX']):
        issues.append(f'Line {i}: {line.strip()}')

# 3. print statements
print_lines = [(i+1, line.strip()) for i, line in enumerate(content.split('\n')) if 'print(' in line and not line.strip().startswith('#')]
issues.extend([f'Line {i}: Print statement: {line}' for i, line in print_lines[:15]])

# 4. Long functions
lines = content.split('\n')
func_start = None
func_name = None
for i, line in enumerate(lines):
    if line.strip().startswith('def ') or line.strip().startswith('async def '):
        if func_start:
            func_len = i - func_start
            if func_len > 50:
                issues.append(f'Line {func_start+1}: Function {func_name} >50 lines ({func_len})')
        func_start = i
        func_name = line.strip().split('def ')[1].split('(')[0]
if func_start:
    func_len = len(lines) - func_start
    if func_len > 50:
        issues.append(f'Line {func_start+1}: Function {func_name} >50 lines ({func_len})')

# 5. Hardcoded paths
for i, line in enumerate(content.split('\n'), 1):
    if 'C:\\\\' in line or '/home/' in line or '/Users/' in line:
        issues.append(f'Line {i}: Hardcoded path: {line.strip()}')

# 6. Global mutable state
for i, line in enumerate(content.split('\n'), 1):
    if line.strip().startswith('global '):
        issues.append(f'Line {i}: Global statement: {line.strip()}')

# 7. eval/exec usage
for i, line in enumerate(content.split('\n'), 1):
    if 'eval(' in line or 'exec(' in line:
        issues.append(f'Line {i}: eval/exec usage: {line.strip()}')

# 8. Large functions/classes
for i, line in enumerate(content.split('\n'), 1):
    if 'class ' in line and ':' in line:
        class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0]
        issues.append(f'Line {i}: Class: {class_name}')

# 9. String concatenation in loops (potential performance)
for i, line in enumerate(content.split('\n'), 1):
    if '+=' in line and ('str' in line.lower() or 'string' in line.lower() or 'parts' in line.lower()):
        issues.append(f'Line {i}: Possible string concat in loop: {line.strip()}')

# 10. Mutable default arguments
for i, line in enumerate(content.split('\n'), 1):
    if 'def ' in line and '[]' in line or '{}' in line:
        issues.append(f'Line {i}: Possible mutable default arg: {line.strip()}')

# 11. Missing error handling in subprocess
for i, line in enumerate(content.split('\n'), 1):
    if 'subprocess.run' in line and 'timeout' not in content[max(0,content.index(line)):content.index(line)+200]:
        issues.append(f'Line {i}: subprocess.run without timeout check nearby')

for issue in issues:
    print(issue)

print(f'\nTotal issues: {len(issues)}')