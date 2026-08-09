#!/usr/bin/env python3
import re

with open('docs/test_grafo.html', 'r', encoding='utf-8') as f:
    content = f.read()

print('HTML size:', len(content))
print('Has groups config:', 'groups:' in content)
print('Has options config:', 'const options' in content)
print('Has physics config:', 'physics:' in content)
print('Has interaction config:', 'interaction:' in content)
print('Has groups object:', 'padroes:' in content and 'color:' in content)
print('References local vendor:', 'vendor/vis-network.min.js' in content)

# Check script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print('Script tags:', len(scripts))
for i, s in enumerate(scripts):
    if len(s) > 1000:
        print('  Large script #{}: {} chars'.format(i, len(s)))

# Check for group property in nodes
if '"group"' in content:
    idx = content.index('"group"')
    print('First group property:', content[idx:idx+50])

# Check vendor inlining
if '<script>' in content[:5000] and 'vis-network' in content[:5000]:
    print('WARNING: Vendor JS appears inlined in head')
else:
    print('OK: Vendor JS not inlined in head')