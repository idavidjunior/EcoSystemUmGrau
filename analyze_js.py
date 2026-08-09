#!/usr/bin/env python3
"""Analyze JS code in widget_grafo.py."""
with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

js_sections = [
    ('WIDGET_CSS', 'WIDGET_CSS'),
    ('API_INJECT', 'API_INJECT'),
    ('RESIZE_JS', 'RESIZE_JS'),
    ('WIDGET_JS', 'WIDGET_JS'),
    ('WIDGET_JS_EXTRA', 'WIDGET_JS_EXTRA'),
]

for name, var in js_sections:
    start = content.find(var + ' = """')
    if start != -1:
        start = content.find('"""', start) + 3
        end = content.find('"""', start)
        js = content[start:end]
        print(f'\n=== {name} ({len(js)} chars) ===')
        lines = js.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if 'console.log' in stripped:
                print(f'  JS Line {i}: console.log: {stripped[:80]}')
            if 'catch (e) {}' in stripped or 'catch(e){}' in stripped:
                print(f'  JS Line {i}: Empty catch: {stripped[:80]}')
            if 'eval(' in stripped or 'Function(' in stripped:
                print(f'  JS Line {i}: eval/Function: {stripped[:80]}')
            if 'innerHTML' in stripped and '=' in stripped:
                print(f'  JS Line {i}: innerHTML assignment: {stripped[:80]}')
            if 'setTimeout' in stripped or 'setInterval' in stripped:
                print(f'  JS Line {i}: Timer: {stripped[:80]}')
            if 'document.write' in stripped:
                print(f'  JS Line {i}: document.write: {stripped[:80]}')
            if 'localStorage.setItem' in stripped or 'localStorage.getItem' in stripped:
                print(f'  JS Line {i}: localStorage: {stripped[:80]}')
            if 'var ' in stripped and '=' in stripped:
                pass  # OK
            if '===' in stripped or '!==' in stripped:
                pass  # Good, strict equality
            if '==' in stripped and '===' not in stripped and '!=' not in stripped:
                print(f'  JS Line {i}: Loose equality: {stripped[:80]}')